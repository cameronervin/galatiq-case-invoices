import { isFinding, isInvoiceData, isRecommendation } from "./invoiceArtifacts";

describe("invoice artifact decoders", () => {
  it("accepts a complete invoice and rejects malformed nested money", () => {
    const invoice = validInvoice();

    expect(isInvoiceData(invoice)).toBe(true);
    expect(
      isInvoiceData({
        ...invoice,
        items: [{ ...invoice.items[0], unit_price: { amount: 12, currency: "USD" } }]
      })
    ).toBe(false);
  });

  it("requires nullable invoice fields to be present", () => {
    const { due_date: _dueDate, ...missingDueDate } = validInvoice();

    expect(isInvoiceData(missingDueDate)).toBe(false);
  });

  it("rejects non-finite line numbers and finding item references", () => {
    const invoice = validInvoice();
    expect(
      isInvoiceData({
        ...invoice,
        items: [{ ...invoice.items[0], line_number: Number.NaN }]
      })
    ).toBe(false);
    expect(
      isFinding({
        code: "INVALID_QUANTITY",
        severity: "blocking",
        message: "Quantity must be finite.",
        field_path: "items.0.quantity",
        item_line_number: Number.POSITIVE_INFINITY,
        expected: "finite",
        actual: "Infinity"
      })
    ).toBe(false);
  });

  it("validates every recommendation reason code", () => {
    expect(
      isRecommendation({
        proposed_route: "review",
        final_route: "review",
        reason_codes: ["LOW_CONFIDENCE", 42],
        summary: "Review required.",
        reflection_count: 1,
        decided_by: "agent"
      })
    ).toBe(false);
  });
});

function validInvoice() {
  return {
    vendor_name: "Acme",
    invoice_number: "INV-1",
    revision: null,
    invoice_date: "2026-01-01",
    due_date: null,
    payment_terms: null,
    currency: "USD",
    extraction_confidence: "high",
    items: [
      {
        line_number: 1,
        source_name: "Widget",
        normalized_item_code: "WIDGET",
        quantity: 2,
        unit_price: { amount: "5.00", currency: "USD" },
        line_total: { amount: "10.00", currency: "USD" }
      }
    ],
    subtotal: { amount: "10.00", currency: "USD" },
    tax: null,
    shipping: null,
    total: { amount: "10.00", currency: "USD" }
  };
}
