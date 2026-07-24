import type { ReactNode } from "react";

interface StatusBadgeProps {
  children: ReactNode;
}

export function StatusBadge({ children }: StatusBadgeProps) {
  return <span className="status-badge">{children}</span>;
}

