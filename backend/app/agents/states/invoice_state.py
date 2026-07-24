from typing import NotRequired, TypedDict


class InvoiceProcessingState(TypedDict):
    run_id: str
    invoice_path: str
    status: str
    current_stage: str
    messages: NotRequired[list[str]]
    errors: NotRequired[list[str]]

