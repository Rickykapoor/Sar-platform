import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_full_structuring_pipeline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. POST /submit-transaction with structuring scenario
        resp1 = await client.post("/submit-transaction", json={
            "amount_usd": 9800.0,
            "transaction_type": "wire",
            "geography": "us",
            "account_id": "ACC123"
        })
        # 2. Assert response status 200, case_id present
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert "case_id" in data1
        case_id = data1["case_id"]

        # 3. GET /case/{id} — assert risk_tier == "RED"
        resp2 = await client.get(f"/case/{case_id}")
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2.get("risk_assessment", {}).get("risk_tier") == "RED"

        # 4. POST /case/{id}/run-pipeline
        resp3 = await client.post(f"/case/{case_id}/run-pipeline")
        assert resp3.status_code == 200

        # 5. GET /case/{id} — assert all 5 agent outputs non-None
        resp4 = await client.get(f"/case/{case_id}")
        assert resp4.status_code == 200
        data4 = resp4.json()
        for key in ["normalized", "risk_assessment", "narrative", "compliance", "audit"]:
            assert data4.get(key) is not None

        # 6. Assert len(audit_trail) >= 5
        assert len(data4.get("audit_trail", [])) >= 5

        # 7. Assert len(audit.immutable_hash) == 64
        assert len(data4.get("audit", {}).get("immutable_hash", "")) == 64

        # 8. Assert risk_score >= 0.85
        assert data4.get("risk_assessment", {}).get("risk_score", 0) >= 0.85

        # 9. POST /case/{id}/approve with analyst_name="TestAnalyst"
        resp5 = await client.post(f"/case/{case_id}/approve", json={"analyst_name": "TestAnalyst"})
        assert resp5.status_code == 200

        # 10. GET /case/{id} — assert status == "FILED"
        resp6 = await client.get(f"/case/{case_id}")
        assert resp6.status_code == 200
        assert resp6.json().get("status") == "FILED"
