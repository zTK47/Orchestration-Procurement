"""End-to-end: free-text intake through the full pipeline over HTTP, using the
seed data (same as demo.py, scenario A)."""


def _post(client, path, json=None):
    response = client.post(path, json=json)
    assert response.status_code in (200, 201), response.text
    return response.json()


def test_full_pipeline_from_text_to_completed(client):
    body = _post(
        client,
        "/procurement-requests",
        {"requesterId": "U-REQ-1", "costCenterId": "CC-IT",
         "rawText": "I need 5 new Lenovo Laptops for the IT department"},
    )
    assert body["status"] == "PARSED"
    assert body["workflow"]["nextState"] == "RESOLVED"
    base = f"/procurement-requests/{body['requestId']}"

    resolved = _post(client, f"{base}/resolve")
    assert resolved["resolvedData"]["sku"] == "LEN-T14-G3"
    assert resolved["resolvedData"]["unitPrice"] == 1200.0

    validated = _post(client, f"{base}/validate")
    assert validated["validation"]["budgetCheck"] == "PASSED"

    ordered = _post(client, f"{base}/create-order")
    assert ordered["status"] == "PENDING_APPROVAL"
    assert ordered["validation"]["requiresApproval"] is True
    assert ordered["validation"]["approvalLevel"] == "MANAGER"

    approved = _post(
        client, f"{base}/approvals",
        {"approverId": "U-MAN-1", "level": "MANAGER", "decision": "APPROVED"},
    )
    assert approved["status"] == "APPROVED"

    sent = _post(client, f"{base}/send-order")
    assert sent["status"] == "ORDER_SENT"
    assert sent["erpReference"].startswith("PO-")

    assert _post(client, f"{base}/goods-receipt")["status"] == "GOODS_RECEIPT"

    completed = _post(client, f"{base}/complete")
    assert completed["status"] == "COMPLETED"
    assert completed["workflow"]["nextState"] is None
    assert completed["workflow"]["history"] == [
        "CREATED", "PARSED", "RESOLVED", "VALIDATED", "PENDING_APPROVAL",
        "APPROVED", "ORDER_SENT", "GOODS_RECEIPT", "COMPLETED",
    ]


def test_get_unknown_request_returns_404(client):
    assert client.get("/procurement-requests/does-not-exist").status_code == 404


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_frontend_is_served_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Procurement Orchestrator" in response.text
