import { formatMoney } from "@/components/features/run-detail/formatters";
import type { InvoiceData } from "@/types/api";

export function InvoiceDetails({ invoice }: { invoice: InvoiceData }) {
  return (
    <section className="detail-section" aria-labelledby="invoice-heading">
      <div className="section-heading compact">
        <div>
          <p className="panel-kicker">Extracted record</p>
          <h3 id="invoice-heading">
            Invoice {invoice.invoice_number ?? "number unavailable"}
          </h3>
        </div>
        <span className="confidence">{invoice.extraction_confidence} confidence</span>
      </div>
      <dl className="invoice-facts">
        <Fact label="Vendor" value={invoice.vendor_name} />
        <Fact label="Invoice date" value={invoice.invoice_date} />
        <Fact label="Due date" value={invoice.due_date} />
        <Fact label="Terms" value={invoice.payment_terms} />
        <Fact label="Total" value={formatMoney(invoice.total)} />
        <Fact label="Currency" value={invoice.currency} />
      </dl>
      {invoice.items.length ? (
        <div className="table-wrap">
          <table>
            <caption className="sr-only">Extracted invoice line items</caption>
            <thead>
              <tr>
                <th scope="col">Item</th>
                <th scope="col">Qty</th>
                <th scope="col">Unit price</th>
                <th scope="col">Line total</th>
              </tr>
            </thead>
            <tbody>
              {invoice.items.map((item) => (
                <tr key={item.line_number}>
                  <td>
                    <strong>{item.normalized_item_code ?? "Unmatched"}</strong>
                    <span>{item.source_name ?? `Line ${item.line_number}`}</span>
                  </td>
                  <td>{item.quantity ?? "—"}</td>
                  <td>{formatMoney(item.unit_price)}</td>
                  <td>{formatMoney(item.line_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string | null }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value ?? "—"}</dd>
    </div>
  );
}
