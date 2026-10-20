"""End-to-end: direct catalog intake, and domain errors as HTTP 422."""


def _catalog(client, sku, quantity):
    return client.post(
        "/procurement-requests/from-catalog",
        json={"requesterId": "U-REQ-1", "costCenterId": "CC-IT", "sku": sku, "quantity": quantity},
    )


def test_catalog_selection_resolves_directly(client):
    response = _catalog(client, "LEN-T14-G3", 2)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "RESOLVED"
    assert body["resolvedData"]["totalAmount"] == 2400.0
    assert body["validation"]["stockCheck"] == "PASSED"


def test_catalog_selection_with_unknown_sku_returns_422(client):
    assert _catalog(client, "NOT-A-REAL-SKU", 1).status_code == 422


def test_catalog_selection_from_unapproved_supplier_returns_422(client):
    # HP-X360 is supplied by SUP-002, which is unapproved in the seed data.
    assert _catalog(client, "HP-X360", 1).status_code == 422


def test_approving_with_wrong_role_returns_422(client):
    request_id = _catalog(client, "LEN-T14-G3", 5).json()["requestId"]
    client.post(f"/procurement-requests/{request_id}/validate")
    client.post(f"/procurement-requests/{request_id}/create-order")

    response = client.post(
        f"/procurement-requests/{request_id}/approvals",
        json={"approverId": "U-REQ-1", "level": "MANAGER", "decision": "APPROVED"},
    )
    assert response.status_code == 422


def test_sending_an_unapproved_order_to_the_erp_returns_422(client):
    request_id = _catalog(client, "LEN-T14-G3", 5).json()["requestId"]
    assert client.post(f"/procurement-requests/{request_id}/send-order").status_code == 422
