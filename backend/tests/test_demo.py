"""Public demo endpoint tests.

The parse path itself needs the Anthropic API key (the fast mapper calls the LLM),
so here we cover the deterministic, no-key branches:

  * the router is registered and public (no auth required)
  * the security guard rejects unsafe/oversized/unsupported uploads
  * an empty-but-valid file returns a clean, explained "nothing to analyze" result

The full parse is exercised by the ingestion tests, which share the exact same
loader / mapper / grounding / calculation services this endpoint reuses.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_demo_route_is_public_and_registered():
    """POST /api/demo/analyze exists and needs no auth (a missing file -> 422, not 401)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/demo/analyze")
    # 422 = FastAPI validation (no file); crucially NOT 401/403 (would mean auth-gated).
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_demo_rejects_unsupported_file_type():
    """An unsupported extension is rejected by the security guard with a 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/demo/analyze",
            files={
                "file": ("payload.exe", b"MZ\x90\x00binary", "application/octet-stream")
            },
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_demo_empty_valid_file_returns_clean_notice():
    """A CSV with only a header (no data rows) yields a clean, explained result."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/demo/analyze",
            files={"file": ("empty.csv", b"activity,quantity,unit\n", "text/csv")},
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["rows_calculated"] == 0
    assert body["total_tco2e"] == 0.0
    assert body["by_scope"] == []
    assert body["notice"]
