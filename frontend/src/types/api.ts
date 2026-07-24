export interface HealthResponse {
  status: string;
  service: string;
}

export interface QueuedAgentRun {
  run_id: string;
  task_id: string;
  invoice_path: string;
  status: "queued";
}
