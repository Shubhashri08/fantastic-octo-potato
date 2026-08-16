import pytest
from datetime import datetime
from httpx import AsyncClient

# Test payloads helper
def get_sample_ingest_payload(
    event_id="EVT_999", 
    correlation_id="CORR_111", 
    lat=19.123, 
    lon=72.456, 
    confidence=0.95, 
    severity="HIGH"
):
    return {
        "event": {
            "event_id": event_id,
            "event_type": "accident",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "location": {"latitude": lat, "longitude": lon},
            "confidence": confidence,
            "severity": severity,
            "entities": ["vehicle_V17"],
            "cameras": ["CAM_03"],
            "correlation_id": correlation_id
        },
        "context": {
            "location": {"latitude": lat, "longitude": lon},
            "risk_score": 0.8,
            "hotspot": True,
            "historical_incident_count": 5,
            "dominant_incident_type": "accident",
            "peak_time": "18:00-22:00",
            "correlation_id": correlation_id
        }
    }

@pytest.mark.asyncio
async def test_alert_consistency_validation_correlation_mismatch(client: AsyncClient):
    payload = get_sample_ingest_payload()
    # Induce mismatch
    payload["context"]["correlation_id"] = "DIFFERENT_CORR"
    
    response = await client.post("/alerts/evaluate", json=payload)
    assert response.status_code == 400
    assert "Correlation ID mismatch" in response.json()["detail"]

@pytest.mark.asyncio
async def test_alert_consistency_validation_location_tolerance(client: AsyncClient):
    payload = get_sample_ingest_payload()
    # Induce location discrepancy beyond 0.001 tolerance (e.g. 0.002)
    payload["context"]["location"]["latitude"] = 19.125
    
    response = await client.post("/alerts/evaluate", json=payload)
    assert response.status_code == 400
    assert "Location tolerance exceeded" in response.json()["detail"]

@pytest.mark.asyncio
async def test_alert_engine_priority_rules(client: AsyncClient):
    # Rule 1: confidence >= 0.85 AND severity = HIGH -> HIGH
    p1 = get_sample_ingest_payload(event_id="E_H", confidence=0.88, severity="HIGH")
    res1 = await client.post("/alerts/evaluate", json=p1)
    assert res1.status_code == 201
    assert res1.json()["priority"] == "HIGH"

    # Rule 2: confidence >= 0.70 -> MEDIUM (even if severity is LOW)
    p2 = get_sample_ingest_payload(event_id="E_M", confidence=0.72, severity="LOW")
    res2 = await client.post("/alerts/evaluate", json=p2)
    assert res2.status_code == 201
    assert res2.json()["priority"] == "MEDIUM"

    # Rule 3: otherwise -> LOW
    p3 = get_sample_ingest_payload(event_id="E_L", confidence=0.65, severity="HIGH")
    res3 = await client.post("/alerts/evaluate", json=p3)
    assert res3.status_code == 201
    assert res3.json()["priority"] == "LOW"

@pytest.mark.asyncio
async def test_alert_evaluation_idempotency(client: AsyncClient):
    payload = get_sample_ingest_payload(event_id="EVT_IDEMPOTENT_TEST", correlation_id="CORR_IDEMP")
    
    # First submit -> 201 Created
    response1 = await client.post("/alerts/evaluate", json=payload)
    assert response1.status_code == 201
    id1 = response1.json()["id"]

    # Second submit -> 200 OK (returned immediately from database cache)
    response2 = await client.post("/alerts/evaluate", json=payload)
    assert response2.status_code == 200
    assert response2.json()["id"] == id1

@pytest.mark.asyncio
async def test_list_alerts_rbac(client: AsyncClient, test_users: dict):
    # Ingest an alert first so list is not empty
    payload = get_sample_ingest_payload(event_id="EVT_LIST_TEST", correlation_id="CORR_LIST")
    await client.post("/alerts/evaluate", json=payload)

    # Operator token -> VIEW_ALERTS is allowed
    headers = {"Authorization": f"Bearer {test_users['operator']['token']}"}
    response = await client.get("/alerts", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Analyst token -> VIEW_ALERTS is forbidden (Analyst has VIEW_GIS, VIEW_HISTORICAL, VIEW_RISK only)
    headers = {"Authorization": f"Bearer {test_users['analyst']['token']}"}
    response = await client.get("/alerts", headers=headers)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_alert_status_transition_rbac(client: AsyncClient, test_users: dict):
    # Ingest an alert to test
    payload = get_sample_ingest_payload(event_id="EVT_TRANSITION_TEST", correlation_id="CORR_TRANS")
    res = await client.post("/alerts/evaluate", json=payload)
    alert_id = res.json()["id"]

    # Analyst token (no permission) updates status -> 403
    headers_analyst = {"Authorization": f"Bearer {test_users['analyst']['token']}"}
    patch_res1 = await client.patch(f"/alerts/{alert_id}", json={"status": "ACKNOWLEDGED"}, headers=headers_analyst)
    assert patch_res1.status_code == 403

    # Operator token (has ACKNOWLEDGE_ALERTS permission) updates status -> 200
    headers_operator = {"Authorization": f"Bearer {test_users['operator']['token']}"}
    patch_res2 = await client.patch(f"/alerts/{alert_id}", json={"status": "ACKNOWLEDGED"}, headers=headers_operator)
    assert patch_res2.status_code == 200
    assert patch_res2.json()["status"] == "ACKNOWLEDGED"
    assert patch_res2.json()["acknowledged_by"] is not None
    assert patch_res2.json()["acknowledged_at"] is not None
