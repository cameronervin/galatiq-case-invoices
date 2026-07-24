# API Rules

Base path: `/api/v1`. The current implemented surface is `GET /health`; document and test new endpoints before treating them as available.

- Keep routes thin and use Pydantic request/response models.
- Return server-generated run IDs, workflow state, validation findings, approval decisions, and payment outcomes.
- Use explicit validation and transition errors.
- Do not expose internal provider responses, secrets, local filesystem paths, or unreviewed payment controls.
- Keep frontend types aligned with API responses.

