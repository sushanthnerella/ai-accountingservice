import pytest
import io
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_org_client_and_document_workflow(async_client: AsyncClient):
    # 1. Register and Login CA Partner
    await async_client.post("/api/v1/auth/register", json={
        "email": "partner@capractice.in",
        "password": "Password123!",
        "full_name": "Senior Partner"
    })
    login_res = await async_client.post("/api/v1/auth/login", json={
        "email": "partner@capractice.in",
        "password": "Password123!"
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create CA Firm Organization
    org_res = await async_client.post("/api/v1/organizations", headers=headers, json={
        "name": "Sharma & Associates LLP",
        "slug": "sharma-ca-firm",
        "org_type": "CA_FIRM"
    })
    assert org_res.status_code == 201
    org_id = org_res.json()["data"]["id"]

    # Add Org Header
    headers["X-Organization-Id"] = org_id

    # 3. Create Client Business under Org
    client_res = await async_client.post("/api/v1/clients", headers=headers, json={
        "legal_name": "Apex Digital Services Pvt Ltd",
        "trade_name": "Apex Digital",
        "business_type": "PVT_LTD",
        "pan": "ABCDE1234F",
        "gstin": "27ABCDE1234F1Z5",
        "state_code": "27",
        "is_composition_scheme": False
    })
    assert client_res.status_code == 201
    client_id = client_res.json()["data"]["id"]
    headers["X-Client-Business-Id"] = client_id

    # 4. Multi-File Document Upload
    pdf_file = ("invoice_001.pdf", io.BytesIO(b"%PDF-1.4 sample invoice content"), "application/pdf")
    png_file = ("receipt_002.png", io.BytesIO(b"\x89PNG\r\n\x1a\nfake png content"), "image/png")

    upload_res = await async_client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=[("files", pdf_file), ("files", png_file)],
        data={"category": "AUTO_DETECT"}
    )
    assert upload_res.status_code == 202
    batch_data = upload_res.json()["data"]
    assert batch_data["total_files"] == 2
    assert len(batch_data["uploaded_files"]) == 2
    assert batch_data["uploaded_files"][0]["is_duplicate"] is False
    assert batch_data["uploaded_files"][1]["is_duplicate"] is False

    doc1_id = batch_data["uploaded_files"][0]["document_id"]

    # 5. Upload Duplicate File
    dup_pdf = ("invoice_001_copy.pdf", io.BytesIO(b"%PDF-1.4 sample invoice content"), "application/pdf")
    dup_res = await async_client.post(
        "/api/v1/documents/upload",
        headers=headers,
        files=[("files", dup_pdf)],
        data={"category": "SALES_INVOICE"}
    )
    assert dup_res.status_code == 202
    dup_data = dup_res.json()["data"]
    assert dup_data["uploaded_files"][0]["is_duplicate"] is True
    assert dup_data["uploaded_files"][0]["duplicate_of_id"] == doc1_id

    # 6. List Documents
    docs_res = await async_client.get("/api/v1/documents", headers=headers)
    assert docs_res.status_code == 200
    assert len(docs_res.json()["data"]) == 3

    # 7. Audit Trail check
    audit_res = await async_client.get("/api/v1/audit", headers=headers)
    assert audit_res.status_code == 200
    events = audit_res.json()["data"]
    event_types = [e["event_type"] for e in events]
    assert "ORG_CREATED" in event_types
    assert "CLIENT_CREATED" in event_types
    assert "DOC_UPLOADED" in event_types
    assert "DOC_DUPLICATE_DETECTED" in event_types
