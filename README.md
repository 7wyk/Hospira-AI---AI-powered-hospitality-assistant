# Hospira AI

Hospira AI is a hotel assistant for **Aurelia Hotel**. It provides grounded room information, recommendations, demo availability, persistent conversations, meaningful summaries, and user-specific room context. It explicitly does not create real bookings.

## Stack

The frontend uses React, Vite, TypeScript, React Router, Supabase Auth, and Lucide React. The backend uses FastAPI, Pydantic v2, SQLAlchemy async, Alembic, Supabase PostgreSQL, and a backend-only Groq adapter with validated fallback behavior.

## Run locally

1. Copy `.env.example` to `.env`.
2. Configure `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` for the frontend. The login/register pages require these values.
3. Configure `SUPABASE_JWT_SECRET` and `GROQ_API_KEY` for production-like backend behavior. Without a Groq key, local development uses a safe, grounded fallback; it never invents hotel facts.
4. Backend: `cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && PYTHONPATH=. uvicorn app.main:app --reload --port 8000`
5. Frontend: `cd frontend && npm install && npm run dev`
6. Open `http://localhost:5173/login`.

For local-only development, the default SQLite URL works. Production must use a PostgreSQL URL such as the Supabase connection string; production configuration validation rejects SQLite.

## Database migrations

The application creates local tables on startup for convenience. For deployment, configure `DATABASE_URL` and run the Alembic pipeline from the repository root with `alembic upgrade head`, or apply `backend/alembic/versions/0001_initial.sql` in Supabase. PostgreSQL URLs are normalized to SQLAlchemy's asyncpg driver.

## Authentication

Registration and login use Supabase Auth email/password methods. Supabase persists the session in the browser, the protected chat route restores it on refresh, and FastAPI validates the bearer token. Ownership always comes from the validated token subject; frontend user IDs are never trusted.

## AI and memory

When `GROQ_API_KEY` is configured, the backend calls Groq's OpenAI-compatible chat endpoint with structured JSON output instructions and validates the result with Pydantic. If the call fails or no key is configured, a grounded fallback handles hotel facts safely. Backend data remains authoritative for room facts, prices, capacities, and availability. Recent messages, a meaningful conversation summary, active room, and relevant persistent room memories are used for context. Room interests are user-owned and soft-deletable.

## Tests

Run `cd backend && PYTHONPATH=. pytest -q`. Run `cd frontend && npm run typecheck && npm run build`. The backend tests cover authentication rejection, grounded Premium Room follow-up, same-conversation pronoun context, summaries, availability calculations, invalid dates, and unsupported requests.

## Deployment

Deploy `frontend` to Vercel with `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY`. Deploy `backend` to Render or another Python host with `DATABASE_URL` pointing to Supabase PostgreSQL, `SUPABASE_JWT_SECRET`, `GROQ_API_KEY`, `GROQ_MODEL`, `CORS_ORIGINS`, and a secure `SECRET_KEY`. Use `uvicorn app.main:app --host 0.0.0.0 --port $PORT` as the start command and run migrations before serving traffic.
