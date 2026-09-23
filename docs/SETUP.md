# Setup

Copy `.env.example` to `.env`. The frontend requires `VITE_API_BASE_URL`, `VITE_SUPABASE_URL`, and `VITE_SUPABASE_ANON_KEY`. The backend requires `DATABASE_URL`, `SUPABASE_JWT_SECRET` in production, `CORS_ORIGINS`, and a secure `SECRET_KEY`. Add `GROQ_API_KEY` and `GROQ_MODEL` to enable live Groq responses. Groq and service-role secrets must never be placed in frontend variables.

## Local run

```bash
cd backend
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open `/login`, register with Supabase Auth, and then use the protected chat route. The backend's safe grounded fallback works without a Groq key for local tests.

## Migrations

For a clean local migration test, run `DATABASE_URL=sqlite:///./migration-test.db alembic upgrade head` from the repository root. For production, set `DATABASE_URL` to the Supabase PostgreSQL connection string and run `alembic upgrade head` before starting Uvicorn. PostgreSQL URLs are converted to SQLAlchemy's asyncpg driver by the application engine.

## Deployment

Deploy `frontend` to Vercel with the three `VITE_` values. Deploy `backend` to Render with the PostgreSQL URL, Supabase JWT secret, Groq values, CORS origin, and `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Do not claim the application is live until both health and authenticated flows are verified in the deployed environments.
