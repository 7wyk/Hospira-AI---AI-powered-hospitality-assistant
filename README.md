# Hospira AI

Hospira AI is a public hotel assistant demo for **Aurelia Hotel**. It opens directly to the assistant without login, registration, email confirmation, or authentication screens. It provides grounded room information, recommendations, demo availability, persistent conversations, summaries, and browser-scoped room context. It does not create real bookings.

## Stack

The frontend uses React, Vite, TypeScript, and Lucide React. The backend uses FastAPI, Pydantic v2, SQLAlchemy async, Alembic, SQLite locally or Supabase PostgreSQL in deployment, and a backend-only Groq adapter with validated fallback behavior.

## Anonymous sessions and privacy

On first load, the browser generates a random anonymous session ID and stores it in `localStorage`. Every API request sends that value in the `X-Anonymous-Session` header. The backend uses it as a demo-session scope for conversations and memories; it does not represent an authenticated identity. A different browser or cleared storage receives a different scope. Anyone with access to the same browser profile can see its saved demo conversations, so this is not equivalent to account-level security. Do not store sensitive personal information in the public demo.

## Run locally

1. Copy `.env.example` to `.env`.
2. Add `GROQ_API_KEY` only to the backend environment if live Groq responses are desired. Without it, the safe grounded fallback is used.
3. Backend:

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

4. In a second terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

5. Open `http://localhost:5173/`. The Hotel Assistant opens directly.

The default local database is `sqlite+aiosqlite:///./hospira.db`. Production can use a Supabase PostgreSQL connection string in `DATABASE_URL`; no Supabase Auth variables are required.

## Database migrations

For a clean migration test, run `DATABASE_URL=sqlite:///./migration-test.db alembic upgrade head` from the repository root. The existing `user_id` database columns are retained as anonymous session-owner columns for migration compatibility; they no longer contain authenticated Supabase user IDs.

## AI and grounding

When `GROQ_API_KEY` is configured, the backend calls Groq's OpenAI-compatible chat endpoint with structured JSON output instructions and validates the result with Pydantic. If the call fails or no key is configured, the grounded fallback handles hotel facts safely. Backend knowledge remains authoritative for room facts, prices, capacities, and availability.

## Tests

```bash
cd backend
PYTHONPATH=. pytest -q
cd ../frontend
npm install
npm run typecheck
npm run build
```

## Deployment

Deploy the frontend to Vercel with only `VITE_API_BASE_URL`. Deploy the backend to Render or another Python host with `DATABASE_URL`, `GROQ_API_KEY`, `GROQ_MODEL`, `CORS_ORIGINS`, and a secure server-side `SECRET_KEY`. The public demo intentionally provides no user authentication or account recovery.
