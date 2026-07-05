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


async def test_get_and_list(client, auth_headers, seed_emission_factors, monkeypatch):
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
