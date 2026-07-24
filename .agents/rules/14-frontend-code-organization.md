# Frontend Code Organization

```text
frontend/src/app/                 App Router routes
frontend/src/components/features/Feature components
frontend/src/components/layout/  Shared shell
frontend/src/components/ui/      Local primitives
frontend/src/lib/api/             API client
frontend/src/lib/constants/       Routes and constants
frontend/src/types/               Shared contracts
```

Route files default export; reusable components use named exports. Keep components focused, contracts typed, and API calls behind the client boundary. Do not imply that unimplemented API actions or workflow states are available.
