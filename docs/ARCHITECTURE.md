# Architecture

Hospira AI is a public demo split into a React/Vite frontend and a FastAPI backend. The frontend opens directly to the Hotel Assistant and stores a random anonymous session ID in browser local storage. It sends that ID in `X-Anonymous-Session` on API requests.

FastAPI uses the header value as a demo-session scope for conversation and memory queries. The existing `user_id` columns are retained for schema compatibility but now store anonymous session IDs, not authenticated identities. Missing headers receive a fresh ephemeral scope, so stateless API callers do not accidentally share a hardcoded user.

The backend owns SQL persistence, hotel knowledge, centralized availability calculations, conversation summaries, memory retrieval, and AI calls. Groq responses are validated with Pydantic, and backend room/availability data remains authoritative. SQLite is supported locally; PostgreSQL through asyncpg is supported for deployment. Alembic provides the initial migration.
