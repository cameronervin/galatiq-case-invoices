# Invoice Processing Design Tokens

Source of truth: `frontend/src/app/globals.css`.

| Token | Current value | Use |
| --- | --- | --- |
| `--background` | `#f5f6f8` | Workspace background |
| `--surface` | `#ffffff` | Cards and panels |
| `--text` | `#18212f` | Primary text |
| `--muted` | `#667085` | Supporting text |
| `--border` | `#d9dee7` | Dividers and controls |
| `--accent` | `#315efb` | Focus and primary actions |

Prefer CSS variables, readable system typography, modest radii, and restrained motion. Add semantic success, warning, danger, and workflow-state tokens only when corresponding UI behavior is implemented. Avoid arbitrary colors, decorative effects, or third-party branding.

