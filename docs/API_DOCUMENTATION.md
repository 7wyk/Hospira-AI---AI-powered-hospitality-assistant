# API documentation

All routes except health require `Authorization: Bearer <Supabase access token>`. FastAPI derives ownership from the validated token subject.

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` or `/api/v1/health` | Public service health |
| GET/POST | `/api/v1/conversations` | List or create the current user's conversations |
| GET/PATCH/DELETE | `/api/v1/conversations/{id}` | Open, rename, or delete an owned conversation |
| POST | `/api/v1/chat/message` | Persist a user message, generate a validated assistant response, update summary/memory |
| GET | `/api/v1/memory` | List active memories for the current user |
| DELETE | `/api/v1/memory/{id}` | Soft-delete an owned memory |
| GET | `/api/v1/rooms` | List structured hotel rooms |
| GET | `/api/v1/rooms/{room_id}` | Return one knowledge-base room |
| POST | `/api/v1/availability/search` | Validate dates/guest count and return demo availability and totals |

Chat responses contain the conversation ID, assistant message ID, natural-language response, validated intent/confidence/context basis, optional room reference, and memory candidates. Availability responses contain capacity, demo availability, nightly rate, nights, and estimated total. No endpoint creates a reservation.
