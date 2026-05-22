from app.api.reports import minimal_pdf_bytes


def test_minimal_pdf_bytes_returns_pdf_document():
    payload = minimal_pdf_bytes("Demo report")
    assert payload.startswith(b"%PDF")
    assert b"Demo report" in payload
