# Hospira AI

Hospira AI is a hotel assistant for **Aurelia Hotel**. It provides grounded room information, recommendations, demo availability, persistent conversations, and user-specific room context. It explicitly does not create real bookings.

## Run locally

1. Copy `.env.example` to `.env`. The default SQLite URL works without external services.
2. Backend: `cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && PYTHONPATH=. uvicorn app.main:app --reload --port 8000`
3. Frontend: `cd frontend && npm install && npm run dev`
4. Open `http://localhost:5173`.

The local preview accepts a JWT in the sign-in screen. In a deployed environment, configure Supabase Auth and set `SUPABASE_JWT_SECRET`; the backend validates the bearer token and uses its `sub` claim as the owner identity. The Groq integration point is isolated in `app/ai.py`; the grounded local service is the safe fallback when no Groq key is configured.

## Architecture

The React/Vite frontend communicates only with FastAPI REST endpoints. SQLAlchemy models support Supabase PostgreSQL and a local SQLite development database. The memory service stores room interests with source conversation, confidence, active state, and user ownership. Follow-up resolution uses recent conversation state and one high-confidence room memory, otherwise it asks for clarification rather than guessing.

## Tests

Run `cd backend && PYTHONPATH=. pytest -q`. The suite covers health, grounded room answers, cross-conversation Premium Room resolution, and safe unsupported-question behavior.

## Deployment

Deploy `frontend` to Vercel and `backend` to Render or another Python service. Set `VITE_API_BASE_URL`, Supabase URL/keys, `DATABASE_URL`, `SUPABASE_JWT_SECRET`, `GROQ_API_KEY`, and `CORS_ORIGINS`. Apply `backend/alembic/versions/0001_initial.sql` to Supabase or use Alembic in a production migration pipeline.
