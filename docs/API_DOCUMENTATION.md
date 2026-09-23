# API documentation

The demo routes are public and do not require bearer tokens. The frontend sends `X-Anonymous-Session: <random-browser-session-id>` to scope conversation and memory data. If omitted, the backend creates an ephemeral scope for that request, so callers should provide a stable value when they want persistence.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` or `/api/v1/health` | Public service health |
| GET/POST | `/api/v1/conversations` | List or create conversations in the current demo session |
| GET/PATCH/DELETE | `/api/v1/conversations/{id}` | Open, rename, or delete a conversation in the current demo session |
| POST | `/api/v1/chat/message` | Persist a message, generate a validated response, and update summary/memory |
| GET | `/api/v1/memory` | List active memories in the current demo session |
| DELETE | `/api/v1/memory/{id}` | Soft-delete a memory in the current demo session |
| GET | `/api/v1/rooms` | List hotel rooms |
| GET | `/api/v1/rooms/{room_id}` | Return one room |
| POST | `/api/v1/availability/search` | Validate dates/guest count and return demo availability and totals |

No endpoint creates a reservation. Anonymous session IDs are convenience scopes, not authenticated identities or account-level security boundaries.
