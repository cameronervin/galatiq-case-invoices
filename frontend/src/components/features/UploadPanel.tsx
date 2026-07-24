"use client";

import { useRef, useState } from "react";

const acceptedExtensions = new Set(["csv", "json", "xml", "txt", "pdf"]);
const maxFileBytes = 10 * 1024 * 1024;

interface UploadPanelProps {
  pending: boolean;
  onUpload: (file: File) => Promise<boolean>;
}

export function UploadPanel({ pending, onUpload }: UploadPanelProps) {
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  async function submitInvoice(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError("");
    const uploaded = await onUpload(file!);
    if (uploaded) {
      setFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  return (
    <form className="upload-card" aria-busy={pending} onSubmit={submitInvoice}>
      <div>
        <p className="panel-kicker">New run</p>
        <h2>Process an invoice</h2>
        <p>CSV, JSON, XML, TXT, or PDF · up to 10 MB</p>
        {error ? (
          <p className="alert alert-error" id="invoice-file-error" role="alert">
            {error}
          </p>
        ) : null}
      </div>
      <div className="upload-actions">
        <label className="file-picker" htmlFor="invoice-file">
          <span>{file?.name ?? "Choose invoice"}</span>
          <input
            ref={fileInputRef}
            id="invoice-file"
            type="file"
            accept=".csv,.json,.xml,.txt,.pdf"
            aria-describedby={error ? "invoice-file-error" : undefined}
            aria-invalid={Boolean(error)}
            aria-label="Choose invoice"
            onChange={(event) => {
              setError("");
              setFile(event.target.files?.[0] ?? null);
            }}
          />
        </label>
        <button className="button button-primary" disabled={pending} type="submit">
          {pending ? "Submitting…" : "Process invoice"}
        </button>
      </div>
    </form>
  );
}

function validateFile(file: File | null): string {
  if (!file) {
    return "Choose an invoice before processing.";
  }
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!acceptedExtensions.has(extension)) {
    return "Choose a CSV, JSON, XML, TXT, or PDF invoice.";
  }
  if (file.size > maxFileBytes) {
    return "The invoice must be 10 MB or smaller.";
  }
  return "";
}
