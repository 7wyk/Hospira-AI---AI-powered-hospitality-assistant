# Architecture

Hospira AI is split into a React/Vite frontend and a FastAPI backend. The frontend owns Supabase Auth session handling, protected route navigation, conversation UI, and the demo availability form. The backend owns authorization, PostgreSQL/SQLite persistence, hotel knowledge, centralized availability calculations, conversation summaries, memory retrieval, and AI calls.

## Request flow

1. A user registers or logs in with Supabase Auth.
2. Supabase persists the browser session and the frontend sends its access token as a bearer token.
3. FastAPI validates the token, derives the user ID from its subject claim, and applies ownership filters to every conversation and memory query.
4. Chat requests load limited recent messages, the current summary, active room, relevant active memories, and hotel knowledge.
5. The Groq adapter is called when `GROQ_API_KEY` exists. Its JSON is validated with Pydantic; backend room and availability data remains authoritative. A grounded fallback is used when Groq is unavailable.
6. The response, summary, room context, and durable room-interest memory are persisted in one transaction.

Production uses Supabase PostgreSQL through SQLAlchemy asyncpg. Local development can use SQLite. Alembic provides the executable initial migration.
