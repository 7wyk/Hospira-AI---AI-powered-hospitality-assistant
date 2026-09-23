# Setup

Hospira AI is currently a public demo. It does not require login, registration, email confirmation, Supabase Auth, or frontend account configuration.

Copy `.env.example` to `.env`. The frontend requires only `VITE_API_BASE_URL` (or uses `http://localhost:8000/api/v1` by default). The backend requires `DATABASE_URL`, `CORS_ORIGINS`, and optionally `GROQ_API_KEY` and `GROQ_MODEL`. Keep `SECRET_KEY`, database credentials, and Groq keys server-side; never put them in `VITE_` variables.

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

Open `http://localhost:5173/`. The assistant loads directly at the root route.

## Anonymous session behavior

The frontend creates a random browser-local ID and sends it in `X-Anonymous-Session`. This scopes conversation history and memories without pretending the visitor is authenticated. Clearing local storage, using another browser profile, or using another device starts a new demo scope. This provides convenience and basic separation, not account-grade security or privacy.

## Database and deployment

Local development uses SQLite. For deployment, set `DATABASE_URL` to a Supabase PostgreSQL connection string and run `alembic upgrade head` from the repository root. Deploy the frontend with `VITE_API_BASE_URL`; deploy the backend with `DATABASE_URL`, `GROQ_API_KEY`, `GROQ_MODEL`, `CORS_ORIGINS`, and a secure `SECRET_KEY`.
