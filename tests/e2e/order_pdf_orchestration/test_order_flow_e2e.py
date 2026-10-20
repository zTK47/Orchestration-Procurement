"""End-to-end over HTTP: OPO-UC-001 ... OPO-UC-006 with the mock adapters."""
OFFER_TEXT = (
    "Offer 2026-118 from Office Tech AG\n"
    "Dell Latitude 5440 Laptop - CHF 1'250.00\n"
    "Logitech MX Keys Keyboard - CHF 89.90\n"
    "USB-C Docking Station - CHF 189.00\n"
)


def _ok(response, status=200):
    assert response.status_code == status, response.text
    return response.json()


def _offer(client) -> str:
    body = _ok(client.post("/supplier-offers", json={"supplierId": "SUP-OT", "rawText": OFFER_TEXT}), 201)
    return body["offerId"]


def _generate(client, prompt: str) -> dict:
    return _ok(
        client.post("/order-requests", json={"supplierOfferId": _offer(client), "promptText": prompt}), 201
    )


def test_happy_path_from_offer_to_sent_with_pdf(opo_client):
    suppliers = _ok(opo_client.get("/suppliers"))
    assert {"id": "SUP-OT", "name": "Office Tech AG", "contactReference": "orders@officetech.example"} in suppliers

    generated = _generate(opo_client, "I need 3 Dell Latitude laptops and 5 MX Keys keyboards")
    assert generated["status"] == "GENERATED"
    assert [(i["description"], i["quantity"]) for i in generated["lineItems"]] == [
        ("Dell Latitude 5440 Laptop", 3), ("Logitech MX Keys Keyboard", 5),
    ]
    assert generated["total"] == {"amount": 4199.5, "currency": "CHF"}
    base = f"/order-requests/{generated['orderRequestId']}"

    assert _ok(opo_client.post(f"{base}/validate"))["status"] == "VALIDATED"

    no_pdf = opo_client.post(f"{base}/send")
    assert no_pdf.status_code == 422
    assert "PDF" in no_pdf.json()["detail"]

    rendered = _ok(opo_client.post(f"{base}/pdf"))
    assert rendered["pdfReference"]
    pdf = opo_client.get(f"{base}/pdf")
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content.startswith(b"%PDF-")

    sent = _ok(opo_client.post(f"{base}/send"))
    assert sent["status"] == "SENT"
    assert sent["supplierReference"].startswith("SUP-ORD-")
    assert sent["workflow"]["nextState"] is None

    assert opo_client.post(f"{base}/send").status_code == 422
    assert len(opo_client.gateway.sent) == 1
    assert _ok(opo_client.get(base))["status"] == "SENT"


def test_unmatched_item_goes_to_a_human_who_revises_it(opo_client):
    generated = _generate(opo_client, "2 office chairs and 1 docking station")
    base = f"/order-requests/{generated['orderRequestId']}"

    checked = _ok(opo_client.post(f"{base}/validate"))
    assert checked["status"] == "NEEDS_CLARIFICATION"
    assert any("office chairs" in note for note in checked["validation"]["notes"])
    assert opo_client.post(f"{base}/pdf").status_code == 422

    revised = _ok(
        opo_client.put(
            f"{base}/line-items",
            json={"lineItems": [{"description": "USB-C Docking Station", "quantity": 1,
                                 "unitPrice": 189.0, "currency": "CHF"}]},
        )
    )
    assert revised["status"] == "GENERATED"
    assert revised["validation"]["notes"] == []

    assert _ok(opo_client.post(f"{base}/validate"))["status"] == "VALIDATED"


def test_errors_are_mapped_to_http_status_codes(opo_client):
    unknown_supplier = opo_client.post("/supplier-offers", json={"supplierId": "SUP-404", "rawText": "x"})
    assert unknown_supplier.status_code == 422

    assert opo_client.post("/supplier-offers", json={"supplierId": "SUP-OT", "rawText": ""}).status_code == 422
    assert opo_client.post("/supplier-offers", json={"supplierId": "SUP-OT", "rawText": "  "}).status_code == 422

    unknown_offer = opo_client.post("/order-requests", json={"supplierOfferId": "OF-404", "promptText": "1 dock"})
    assert unknown_offer.status_code == 422

    assert opo_client.get("/order-requests/nope").status_code == 404
    assert opo_client.get("/supplier-offers/nope").status_code == 404

    generated = _generate(opo_client, "1 office chair")
    base = f"/order-requests/{generated['orderRequestId']}"
    _ok(opo_client.post(f"{base}/validate"))
    bad_quantity = opo_client.put(
        f"{base}/line-items",
        json={"lineItems": [{"description": "Dock", "quantity": 0, "unitPrice": 1, "currency": "CHF"}]},
    )
    assert bad_quantity.status_code == 422
    assert opo_client.get(f"{base}/pdf").status_code == 404


def test_demo_page_and_health(opo_client):
    page = opo_client.get("/")
    assert page.status_code == 200
    assert "Free Text Order Orchestration" in page.text
    assert _ok(opo_client.get("/health")) == {"status": "ok"}
