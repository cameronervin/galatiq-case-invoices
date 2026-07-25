# Invoice Processing Design Tokens

Source of truth: `frontend/src/app/styles/foundations.css`. The thin
`frontend/src/app/globals.css` entrypoint imports the responsibility-focused
stylesheets in deliberate cascade order.

| Token | Current value | Use |
| --- | --- | --- |
| `--canvas` | `#f3f4f0` | Workspace background |
| `--surface` | `#fffef9` | Primary panels |
| `--ink` | `#17211d` | Primary text |
| `--muted` | `#637069` | Supporting text |
| `--line` | `#d7dcd5` | Dividers and controls |
| `--forest` | `#174e3b` | Focused brand/action color |
| `--mint` | `#dcefe4` | Completed and successful state |
| `--amber-soft` | `#fff0d4` | Review-required state |
| `--red-soft` | `#fbe5e2` | Rejected and failed state |
| `--blue-soft` | `#e2eef6` | Queued and running state |

Use semantic state tokens with text labels, visible focus, readable system
typography, restrained motion, and 3-7px radii. Keep the workspace flat and
operational: rules establish hierarchy, while shadows and decorative gradients
are intentionally absent.
