import type { Money } from "@/types/api";

export function formatMoney(money: Money | null): string {
  return money ? `${money.amount} ${money.currency}` : "—";
}

export function formatTimestamp(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit"
  }).format(new Date(value));
}
