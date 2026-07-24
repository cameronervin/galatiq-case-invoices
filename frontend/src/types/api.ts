import type { components } from "@/types/generated-api";

type ApiSchemas = components["schemas"];

export type RunStatus = ApiSchemas["RunStatus"];
export type RunStage = ApiSchemas["RunStage"];
export type FindingSeverity = ApiSchemas["FindingSeverity"];
export type Money = ApiSchemas["Money"];
export type InvoiceItem = Required<ApiSchemas["InvoiceItem"]>;
export type InvoiceData = Omit<Required<ApiSchemas["InvoiceData"]>, "items"> & {
  items: InvoiceItem[];
};
export type Finding = Required<ApiSchemas["ValidationFinding"]>;
export type Recommendation = Omit<
  Required<ApiSchemas["ApprovalRecommendation"]>,
  "reason_codes"
> & { reason_codes: string[] };
export type HumanReview = ApiSchemas["HumanReview"];
export type Payment = Required<ApiSchemas["PaymentResult"]>;
export type RunEvent = Required<ApiSchemas["RunEvent"]>;
export type RunSummary = ApiSchemas["RunSummary"];
export type RunCreationResponse = ApiSchemas["RunCreationResponse"];
export type RunDetail = Omit<
  Required<ApiSchemas["RunDetail"]>,
  "invoice" | "findings" | "recommendation" | "review" | "payment" | "events"
> & {
  invoice: InvoiceData | null;
  findings: Finding[];
  recommendation: Recommendation | null;
  review: HumanReview | null;
  payment: Payment | null;
  events: RunEvent[];
};
export type RunListResponse = ApiSchemas["RunListResponse"];
export type ReviewRequest = ApiSchemas["ReviewRequest"];
export type ErrorEnvelope = ApiSchemas["ErrorEnvelope"];
