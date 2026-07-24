from backend.app.schemas.invoice import InvoiceData


def extraction_feedback(invoice: InvoiceData) -> list[str]:
    """Return bounded repair guidance for absent core extraction fields."""
    feedback = []
    if not invoice.vendor_name:
        feedback.append("vendor_name is missing")
    if not invoice.items:
        feedback.append("items are missing")
    if invoice.total is None:
        feedback.append("total is missing")
    return feedback
