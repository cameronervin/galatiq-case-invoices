import { StatusBadge } from "@/components/ui/StatusBadge";

export function ProcessingWorkspace() {
  return (
    <main className="workspace">
      <p className="eyebrow">Invoice processing</p>
      <h1>Invoice processing workspace</h1>
      <p className="lede">
        The application shell, API boundary, and asynchronous worker foundation are
        ready. Business workflow implementation comes next.
      </p>

      <section className="status-card" aria-labelledby="scaffold-status">
        <div>
          <h2 id="scaffold-status">Project foundation</h2>
          <p>
            FastAPI, LangGraph, Celery, and Next.js are connected through explicit
            extension points.
          </p>
        </div>
        <StatusBadge>Scaffold ready</StatusBadge>
      </section>
    </main>
  );
}

