export interface RunFeedback {
  error?: string;
  notice?: string;
}

export function uniqueMessages(
  messages: Array<string | undefined>
): string[] {
  return [
    ...new Set(
      messages.filter((message): message is string => Boolean(message))
    )
  ];
}

export function messageFor(error: unknown): string {
  return error instanceof Error
    ? error.message
    : "The request could not be completed.";
}
