"""API-level test for the ingestion funnel (upload → answers → commit over HTTP).

The single LLM mapping call is monkeypatched so the endpoints are exercised
without an API key.
"""

from app.services.ingestion import orchestrator
from app.services.ingestion.mapper import MappedRow

_CSV = b"Activity,Quantity,Unit\nOffice electricity,45600,kWh\nMystery line,5,widgets\n"


def _fake_map_table(table, catalog, max_rows=None, client=None):
    return [
        MappedRow(
            0,
            "electricity_kwh",
            2,
            "2",
            45600,
            "kWh",
            "Office electricity",
            0.95,
            None,
            {},
        ),
        MappedRow(
            1,
            None,
            None,
            None,
            5,
            "widgets",
            "Mystery line",
            0.3,
            "We couldn't match this — which activity is it?",
            {},
        ),
    ]


async def test_upload_rejects_executable(client, auth_headers, seed_emission_factors):
    macho = b"\xcf\xfa\xed\xfe" + b"\x00" * 64
    resp = await client.post(
        "/api/ingest",
        headers=auth_headers,
        files={"file": ("evil.xlsx", macho, "application/octet-stream")},
    )
    assert resp.status_code == 400
    assert "program" in resp.json()["detail"].lower()


async def test_full_funnel_over_http(
    client, auth_headers, test_period, seed_emission_factors, monkeypatch
):
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_map_table)
    monkeypatch.setattr(orchestrator, "map_table", _fake_map_table)

    # 1) upload
    resp = await client.post(
        "/api/ingest",
        headers=auth_headers,
        files={"file": ("footprint.csv", _CSV, "text/csv")},
        data={"reporting_period_id": str(test_period.id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    sid = body["id"]
    assert body["total_rows"] == 2
    assert body["status"] == "needs_answers"
    assert len(body["questions"]) == 1
    elec = [r for r in body["rows"] if r["activity_key"] == "electricity_kwh"]
    assert elec and elec[0]["scope"] == 2  # scope taken from the catalog, not the LLM

    # 2) answer the open question -> classify the mystery row
    qid = body["questions"][0]["id"]
    resp = await client.post(
        f"/api/ingest/{sid}/answers",
        headers=auth_headers,
        json={"answers": [{"question_id": qid, "answer": "petrol_liters"}]},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["open_question_count"] == 0
    assert resp.json()["status"] == "ready_for_review"

    # 3) approve both rows from the review grid
    for r in resp.json()["rows"]:
        pr = await client.patch(
            f"/api/ingest/{sid}/rows/{r['id']}",
            headers=auth_headers,
            json={"status": "approved"},
        )
        assert pr.status_code == 200, pr.text

    # 4) commit -> electricity commits; petrol (unit 'widgets') is rejected by the pipeline
    resp = await client.post(f"/api/ingest/{sid}/commit", headers=auth_headers, json={})
    assert resp.status_code == 200, resp.text
    final = resp.json()
    assert final["status"] == "committed"
    assert final["committed_count"] == 1
    assert final["import_batch_id"] is not None
    committed = [r for r in final["rows"] if r["status"] == "committed"]
    assert len(committed) == 1
    assert committed[0]["committed_activity_id"] is not None


async def test_upload_enqueues_worker_when_enabled(
    client, auth_headers, test_period, seed_emission_factors, monkeypatch
):
    """When ingest_use_worker is on, the parse is dispatched to the worker: upload
    returns instantly with status 'analyzing' and no rows; the client polls the
    result. (Off by default — the parser is fast, so we normally parse inline.)"""
    from app.api import ingest as ingest_module

    enqueued = {}

    class _FakeRedis:
        async def enqueue_job(self, name, *args):
            enqueued["name"] = name
            enqueued["args"] = args

    async def _fake_create_pool(*a, **k):
        return _FakeRedis()

    monkeypatch.setattr(ingest_module.settings, "ingest_use_worker", True)
    monkeypatch.setattr(ingest_module, "create_pool", _fake_create_pool)

    resp = await client.post(
        "/api/ingest",
        headers=auth_headers,
        files={"file": ("footprint.csv", _CSV, "text/csv")},
        data={"reporting_period_id": str(test_period.id)},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "analyzing"
    assert body["rows"] == []
    assert enqueued["name"] == "analyze_ingestion_session"
    assert enqueued["args"][0] == body["id"]  # session id passed to the job


async def test_duplicate_commit_warns(
    client, auth_headers, test_period, seed_emission_factors, monkeypatch
):
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_map_table)
    monkeypatch.setattr(orchestrator, "map_table", _fake_map_table)

    async def upload():
        return await client.post(
            "/api/ingest",
            headers=auth_headers,
            files={"file": ("footprint.csv", _CSV, "text/csv")},
            data={"reporting_period_id": str(test_period.id)},
        )

    # First upload + commit (approve the mapped row, then commit).
    first = (await upload()).json()
    for r in first["rows"]:
        await client.patch(
            f"/api/ingest/{first['id']}/rows/{r['id']}",
            headers=auth_headers,
            json={"status": "approved"},
        )
    await client.post(
        f"/api/ingest/{first['id']}/commit", headers=auth_headers, json={}
    )

    # Re-uploading the exact same bytes must warn about double-counting.
    second = (await upload()).json()
    assert second["summary"].get("duplicate_warning")
    assert second["summary"].get("duplicate_of") == first["id"]


async def test_patch_edit_regrounds_row(
    client, auth_headers, test_period, seed_emission_factors, monkeypatch
):
    """Editing a row's activity/unit must re-ground it — not keep a stale band."""
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_map_table)
    monkeypatch.setattr(orchestrator, "map_table", _fake_map_table)
    up = await client.post(
        "/api/ingest",
        headers=auth_headers,
        files={"file": ("footprint.csv", _CSV, "text/csv")},
        data={"reporting_period_id": str(test_period.id)},
    )
    sid = up.json()["id"]
    # The 'Mystery line' row came back unmapped (red, 0%). Hand-map it to a real key.
    mystery = [r for r in up.json()["rows"] if r["activity_key"] is None][0]
    assert mystery["band"] == "red"
    patched = await client.patch(
        f"/api/ingest/{sid}/rows/{mystery['id']}",
        headers=auth_headers,
        json={"activity_key": "electricity_kwh", "unit": "kWh", "quantity": 100},
    )
    assert patched.status_code == 200, patched.text
    body = patched.json()
    # Re-grounded: it now carries the catalog's scope and a real confidence, not 0/red.
    assert body["scope"] == 2
    assert body["confidence"] > 0
    assert body["activity_key"] == "electricity_kwh"


async def test_get_and_list(client, auth_headers, seed_emission_factors, monkeypatch):
    monkeypatch.setattr(orchestrator, "map_table_fast", _fake_map_table)
    monkeypatch.setattr(orchestrator, "map_table", _fake_map_table)
    up = await client.post(
        "/api/ingest",
        headers=auth_headers,
        files={"file": ("f.csv", _CSV, "text/csv")},
    )
    sid = up.json()["id"]

    got = await client.get(f"/api/ingest/{sid}", headers=auth_headers)
    assert got.status_code == 200
    assert got.json()["id"] == sid

    lst = await client.get("/api/ingest", headers=auth_headers)
    assert lst.status_code == 200
    assert any(s["id"] == sid for s in lst.json())
