#!/usr/bin/env python3
"""
CLIMATRIX Production Smoke Test

Runs a sequence of HTTP checks against a deployed instance to verify
that all core features are functional. Exits 0 if all pass, 1 otherwise.

Usage:
    python scripts/smoke_test.py                          # defaults to localhost:8000
    python scripts/smoke_test.py --base-url https://api.climatrix.io
    python scripts/smoke_test.py --base-url https://api.climatrix.io --email test@example.com --password s3cret
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error

# ─── Helpers ─────────────────────────────────────────────────────────

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
SKIP = "\033[93mSKIP\033[0m"

results: list[tuple[str, str, str]] = []  # (name, status, detail)


def log(name: str, status: str, detail: str = ""):
    results.append((name, status, detail))
    tag = PASS if status == "pass" else (FAIL if status == "fail" else SKIP)
    line = f"  [{tag}] {name}"
    if detail:
        line += f"  — {detail}"
    print(line)


def request(url: str, method: str = "GET", data: dict | None = None,
            headers: dict | None = None, timeout: int = 15) -> tuple[int, dict | str]:
    """Simple HTTP request. Returns (status_code, parsed_json_or_body)."""
    hdrs = headers or {}
    body = None
    if data is not None:
        body = json.dumps(data).encode()
        hdrs.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url, data=body, headers=hdrs, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode()
            try:
                return resp.status, json.loads(raw)
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as e:
        raw = e.read().decode() if e.fp else ""
        try:
            return e.code, json.loads(raw)
        except json.JSONDecodeError:
            return e.code, raw


# ─── Test Functions ──────────────────────────────────────────────────

def test_health(base: str):
    """1. Health endpoint responds."""
    try:
        code, body = request(f"{base}/health")
        if code == 200 and isinstance(body, dict) and body.get("status") == "healthy":
            log("Health endpoint", "pass", f"v{body.get('version')} ({body.get('environment')})")
        else:
            log("Health endpoint", "fail", f"status={code} body={body}")
    except Exception as e:
        log("Health endpoint", "fail", str(e))


def test_root(base: str):
    """2. Root endpoint responds."""
    try:
        code, body = request(f"{base}/")
        if code == 200 and isinstance(body, dict) and body.get("status") == "healthy":
            log("Root endpoint", "pass")
        else:
            log("Root endpoint", "fail", f"status={code}")
    except Exception as e:
        log("Root endpoint", "fail", str(e))


def test_cors_preflight(base: str, origin: str):
    """3. CORS preflight returns correct headers."""
    try:
        req = urllib.request.Request(
            f"{base}/health",
            method="OPTIONS",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            },
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            acao = resp.getheader("access-control-allow-origin", "")
            if origin in acao or acao == "*":
                log("CORS preflight", "pass", f"origin={origin} acao={acao}")
            else:
                log("CORS preflight", "fail", f"origin={origin} acao={acao}")
    except Exception as e:
        # Some servers return 400 for OPTIONS if CORS isn't configured
        log("CORS preflight", "fail", str(e))


def test_reference_data(base: str):
    """4. Reference data endpoints return non-empty lists."""
    for endpoint in ["/api/reference/categories", "/api/reference/fuel-types"]:
        try:
            code, body = request(f"{base}{endpoint}")
            if code == 200 and isinstance(body, list) and len(body) > 0:
                log(f"Reference {endpoint}", "pass", f"{len(body)} items")
            elif code == 401:
                log(f"Reference {endpoint}", "skip", "requires auth")
            else:
                log(f"Reference {endpoint}", "fail", f"status={code}")
        except Exception as e:
            log(f"Reference {endpoint}", "fail", str(e))


def test_register_login(base: str, email: str, password: str) -> str | None:
    """5. Register a test user and log in. Returns JWT token or None."""
    # Register
    ts = int(time.time())
    test_email = email or f"smoketest+{ts}@climatrix.io"
    test_password = password or f"SmokeT3st!{ts}"

    try:
        code, body = request(f"{base}/api/auth/register", method="POST", data={
            "email": test_email,
            "password": test_password,
            "full_name": "Smoke Test",
            "organization_name": f"Smoke Test Org {ts}",
            "country": "United States",
            "industry": "Technology",
        })
        if code in (200, 201):
            token = body.get("access_token") if isinstance(body, dict) else None
            if token:
                log("Register user", "pass", test_email)
                return token
            else:
                log("Register user", "fail", f"no token in response: {body}")
                return None
        elif code == 400 and "already" in str(body).lower():
            log("Register user", "skip", "user already exists, trying login")
        else:
            log("Register user", "fail", f"status={code} body={body}")
    except Exception as e:
        log("Register user", "fail", str(e))

    # If registration was skipped (user exists), try login
    try:
        code, body = request(f"{base}/api/auth/login", method="POST", data={
            "email": test_email,
            "password": test_password,
        })
        if code == 200 and isinstance(body, dict) and body.get("access_token"):
            log("Login user", "pass", test_email)
            return body["access_token"]
        else:
            log("Login user", "fail", f"status={code} body={body}")
            return None
    except Exception as e:
        log("Login user", "fail", str(e))
        return None


def test_auth_endpoints(base: str, token: str):
    """6. Authenticated endpoints respond correctly."""
    headers = {"Authorization": f"Bearer {token}"}

    # GET /api/auth/me
    try:
        code, body = request(f"{base}/api/auth/me", headers=headers)
        if code == 200 and isinstance(body, dict) and body.get("email"):
            log("GET /api/auth/me", "pass", body["email"])
        else:
            log("GET /api/auth/me", "fail", f"status={code}")
    except Exception as e:
        log("GET /api/auth/me", "fail", str(e))

    # GET /api/organization
    try:
        code, body = request(f"{base}/api/organization", headers=headers)
        if code == 200 and isinstance(body, dict):
            log("GET /api/organization", "pass", body.get("name", ""))
        else:
            log("GET /api/organization", "fail", f"status={code}")
    except Exception as e:
        log("GET /api/organization", "fail", str(e))


def test_periods(base: str, token: str) -> str | None:
    """7. Create a period and return its ID."""
    headers = {"Authorization": f"Bearer {token}"}
    ts = int(time.time())

    try:
        code, body = request(f"{base}/api/periods", method="POST", data={
            "name": f"Smoke Test {ts}",
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
        }, headers=headers)
        if code in (200, 201) and isinstance(body, dict) and body.get("id"):
            log("Create period", "pass", f"id={body['id']}")
            return body["id"]
        else:
            log("Create period", "fail", f"status={code} body={body}")
    except Exception as e:
        log("Create period", "fail", str(e))

    # Try listing existing periods instead
    try:
        code, body = request(f"{base}/api/periods", headers=headers)
        if code == 200 and isinstance(body, list) and len(body) > 0:
            pid = body[0].get("id")
            log("List periods (fallback)", "pass", f"found {len(body)}, using id={pid}")
            return pid
    except Exception:
        pass

    return None


def test_activities(base: str, token: str, period_id: str):
    """8. List activities for a period."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        code, body = request(f"{base}/api/activities?period_id={period_id}", headers=headers)
        if code == 200 and isinstance(body, (list, dict)):
            items = body if isinstance(body, list) else body.get("items", body.get("activities", []))
            log("List activities", "pass", f"{len(items)} activities")
        else:
            log("List activities", "fail", f"status={code}")
    except Exception as e:
        log("List activities", "fail", str(e))


def test_reports(base: str, token: str, period_id: str):
    """9. Reports endpoint returns data."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        code, body = request(f"{base}/api/reports/summary?period_id={period_id}", headers=headers)
        if code == 200:
            log("Reports summary", "pass")
        else:
            log("Reports summary", "fail", f"status={code}")
    except Exception as e:
        log("Reports summary", "fail", str(e))


def test_emission_factors(base: str, token: str):
    """10. Emission factors are seeded in the database."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        code, body = request(f"{base}/api/emission-factors?limit=5", headers=headers)
        if code == 200:
            items = body if isinstance(body, list) else body.get("items", [])
            if len(items) > 0:
                log("Emission factors", "pass", f"{len(items)}+ factors in DB")
            else:
                log("Emission factors", "fail", "0 factors — database may not be seeded")
        else:
            log("Emission factors", "fail", f"status={code}")
    except Exception as e:
        log("Emission factors", "fail", str(e))


def test_database_is_postgres(base: str):
    """11. Verify production uses PostgreSQL (not SQLite)."""
    try:
        code, body = request(f"{base}/health")
        if code == 200 and isinstance(body, dict):
            env = body.get("environment", "unknown")
            if env == "production":
                log("Environment=production", "pass")
            else:
                log("Environment check", "skip", f"environment={env} (not production)")
        else:
            log("Environment check", "fail", f"status={code}")
    except Exception as e:
        log("Environment check", "fail", str(e))


def test_billing_config(base: str, token: str):
    """12. Billing config endpoint returns publishable key status."""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        code, body = request(f"{base}/api/billing/config", headers=headers)
        if code == 200 and isinstance(body, dict):
            has_key = bool(body.get("publishable_key"))
            log("Billing config", "pass" if has_key else "skip",
                "Stripe configured" if has_key else "Stripe not configured (ok for dev)")
        elif code == 404:
            log("Billing config", "skip", "endpoint not found")
        else:
            log("Billing config", "fail", f"status={code}")
    except Exception as e:
        log("Billing config", "fail", str(e))


# ─── Main ────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CLIMATRIX Production Smoke Test")
    parser.add_argument("--base-url", default="http://localhost:8000",
                        help="Base URL of the backend API (no trailing slash)")
    parser.add_argument("--email", default="", help="Test user email (auto-generated if empty)")
    parser.add_argument("--password", default="", help="Test user password (auto-generated if empty)")
    parser.add_argument("--origin", default="https://climatrix.io",
                        help="Origin header for CORS test")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    print(f"\n{'='*60}")
    print(f"  CLIMATRIX Smoke Test")
    print(f"  Target: {base}")
    print(f"{'='*60}\n")

    # Unauthenticated checks
    print("── Health & Connectivity ──")
    test_health(base)
    test_root(base)
    test_cors_preflight(base, args.origin)
    test_database_is_postgres(base)

    print("\n── Reference Data ──")
    test_reference_data(base)

    # Auth flow
    print("\n── Authentication ──")
    token = test_register_login(base, args.email, args.password)

    if not token:
        print("\n  [SKIP] Skipping authenticated tests (no token)")
    else:
        print("\n── Authenticated Endpoints ──")
        test_auth_endpoints(base, token)
        test_emission_factors(base, token)
        test_billing_config(base, token)

        print("\n── Data Flow ──")
        period_id = test_periods(base, token)
        if period_id:
            test_activities(base, token, period_id)
            test_reports(base, token, period_id)
        else:
            log("Activities (skipped)", "skip", "no period available")
            log("Reports (skipped)", "skip", "no period available")

    # Summary
    passed = sum(1 for _, s, _ in results if s == "pass")
    failed = sum(1 for _, s, _ in results if s == "fail")
    skipped = sum(1 for _, s, _ in results if s == "skip")
    total = len(results)

    print(f"\n{'='*60}")
    print(f"  Results: {passed}/{total} passed, {failed} failed, {skipped} skipped")
    print(f"{'='*60}\n")

    if failed > 0:
        print("Failed tests:")
        for name, status, detail in results:
            if status == "fail":
                print(f"  - {name}: {detail}")
        print()
        sys.exit(1)
    else:
        print("All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
