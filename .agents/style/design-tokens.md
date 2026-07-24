# Invoice Processing Design Tokens

Source of truth: `frontend/src/app/globals.css`.

| Token | Current value | Use |
| --- | --- | --- |
| `--canvas` | `#f2f3ef` | Workspace background |
| `--surface` | `#fffef9` | Primary panels |
| `--ink` | `#17211d` | Primary text |
| `--muted` | `#637069` | Supporting text |
| `--line` | `#d7dcd5` | Dividers and controls |
| `--forest` | `#174e3b` | Focused brand/action color |
| `--mint` | `#dcefe4` | Completed and successful state |
| `--amber-soft` | `#fff0d4` | Review-required state |
| `--red-soft` | `#fbe5e2` | Rejected and failed state |
| `--blue-soft` | `#e2eef6` | Queued and running state |

Use semantic state tokens with text labels, visible focus, readable system/body
typography, restrained motion, and modest radii. Preserve the editorial heading
type only for the workspace title; operational data remains plain and compact.
