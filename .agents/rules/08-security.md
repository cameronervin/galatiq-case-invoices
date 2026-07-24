# Security Rules

Treat invoice files, vendor details, payment data, prompts, and provider responses as sensitive.

- Validate input and supported file types.
- Keep keys in environment variables and CORS origins explicit.
- Use parameterized SQLite queries.
- Keep payment behind validated approval state and make suspicious/rejected cases visible.
- Redact file contents, vendor/payment details, prompts, model inputs, tokens, and keys from logs.
- Never trust client-provided validation, approval, payment, or run-status fields.

Ask before adding production auth, new persistent stores, paid providers, or live payment behavior.

