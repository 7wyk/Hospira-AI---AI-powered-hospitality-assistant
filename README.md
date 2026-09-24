# Hospira AI — Aurelia Hotel Assistant

Hospira AI is a public hotel-assistant demo for **Aurelia Hotel**. It provides grounded hotel information, room recommendations, demo availability search, conversation history, and lightweight browser-scoped memory without requiring login or registration.

**Live demo:** https://hospira-ai-ai-powered-hospitality-a.vercel.app  
**Repository:** https://github.com/7wyk/Hospira-AI---AI-powered-hospitality-assistant

> **Demo only:** no real reservation is created.

---

## Features

- Conversational hotel assistant for rooms, amenities, policies, breakfast, parking, Wi-Fi, accessibility, luggage storage, check-in, and check-out.
- Room recommendations based on guest count and the supplied hotel knowledge base.
- Demo availability search by check-in date, check-out date, and guest count.
- Anonymous browser sessions with conversation history.
- Lightweight room-interest memory scoped to the anonymous browser session.
- Groq-backed structured AI responses when configured.
- Deterministic grounded fallback responses when Groq is unavailable or a model response cannot be used safely.
- Responsive hotel-style frontend.
- No login, registration, password recovery, or real booking flow.

## Technology stack

### Frontend

- React
- Vite
- TypeScript
- Lucide React
- Responsive CSS

### Backend

- FastAPI
- Pydantic v2
- SQLAlchemy 2.x with async support
- Alembic
- `asyncpg` / `psycopg`
- `aiosqlite`
- `httpx`

### Data and AI

- SQLite for local development
- PostgreSQL for production through `DATABASE_URL`
- Supabase PostgreSQL used by the deployed backend
- Groq API for runtime AI inference

### Deployment

- Frontend: Vercel
- Backend: Render
- Production database: Supabase PostgreSQL

---

## Architecture

```text
┌─────────────────────────────────────────────┐
│                  Vercel                     │
│         React + Vite + TypeScript           │
│                                             │
│  Chat UI • Room questions • Availability    │
└──────────────────────┬──────────────────────┘
                       │ HTTPS / JSON
                       ▼
┌─────────────────────────────────────────────┐
│                  Render                     │
│               FastAPI backend               │
│                                             │
│ Sessions • Conversations • Memory           │
│ Availability • AI orchestration             │
└───────────────┬─────────────────┬───────────┘
                │                 │
                ▼                 ▼
     ┌─────────────────┐   ┌─────────────────┐
     │ Supabase         │   │ Groq API        │
     │ PostgreSQL       │   │ AI responses    │
     │ conversations    │   │ + structured    │
     │ memories         │   │ JSON validation │
     └─────────────────┘   └─────────────────┘
```

### Data flow

1. The browser creates a random anonymous session ID and stores it in `localStorage`.
2. API requests send the value through the `X-Anonymous-Session` header.
3. FastAPI uses that value as the conversation/memory scope.
4. Authoritative hotel facts come from `backend/app/knowledge.py`.
5. When a Groq key is configured, the backend sends hotel and conversation context to the Groq chat-completions API.
6. The model response is validated with a Pydantic schema.
7. If Groq is unavailable or its output is unusable, the grounded fallback in `backend/app/ai.py` handles the request.
8. Conversation and memory records are persisted with SQLAlchemy.
9. Availability results are calculated from the backend room data and are explicitly demo information.

---

## Repository structure

```text
Hospira-AI---AI-powered-hospitality-assistant/
│
├── backend/
│   ├── app/
│   │   ├── ai.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── knowledge.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── services.py
│   │   └── session.py
│   ├── alembic/
│   │   └── versions/
│   │       └── 0001_initial.py
│   ├── alembic.ini
│   ├── requirements.txt
│   └── tests/
│       └── test_core.py
│
├── frontend/
│   ├── src/
│   │   ├── AvailabilityForm.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── package.json
│   └── ...
│
├── docs/
├── .env.example
├── .gitignore
└── README.md
```

---

## Local development

### Prerequisites

- Python 3.13 recommended for the current pinned dependency set.
- Node.js and npm.
- Git.

### Clone

```bash
git clone https://github.com/7wyk/Hospira-AI---AI-powered-hospitality-assistant.git
cd Hospira-AI---AI-powered-hospitality-assistant
```

### Environment configuration

Use `.env.example` as the template. The backend uses local SQLite by default:

```env
APP_ENV=development
DEBUG=true
SECRET_KEY=replace_with_a_secure_secret
DATABASE_URL=sqlite+aiosqlite:///./hospira.db
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant
CORS_ORIGINS=http://localhost:5173
```

`GROQ_API_KEY` is optional. When it is missing, the backend uses the grounded fallback path.

**Never commit `.env` files or API keys.**

### Backend — Windows PowerShell

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:PYTHONPATH="."
python -m uvicorn app.main:app --reload --port 8000
```

Backend:

```text
http://localhost:8000
```

Swagger/OpenAPI:

```text
http://localhost:8000/docs
```

### Backend — macOS/Linux

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000
```

### Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally:

```text
http://localhost:5173
```

The current production frontend is configured to call the deployed Render API. For a fully isolated local full-stack environment, the frontend API base can be switched to the local API endpoint (`http://localhost:8000/api/v1`).

---

## Database migrations

The repository includes an Alembic migration at `backend/alembic/versions/0001_initial.py`.

For local migration work:

```powershell
cd backend
$env:PYTHONPATH="."
alembic upgrade head
```

The production backend uses PostgreSQL through `DATABASE_URL`. The initial production schema was migrated successfully during deployment.

For future production schema changes, run the migration before the application version that depends on it (for example through a deployment pre-deploy migration step where supported by the host).

---

## Hotel knowledge

Current illustrative room data:

| Room | Capacity | Rate / night |
|---|---:|---:|
| Standard Room | 2 | $129 |
| Deluxe Room | 2 | $179 |
| Premium Room | 2 | $239 |
| Family Room | 4 | $269 |
| Aurelia Suite | 3 | $389 |

Selected hotel information:

- Check-in: 3:00 PM
- Check-out: 11:00 AM
- Reception: 24 hours
- Breakfast: 7:00–10:30 AM in the Garden Room
- Heated indoor pool: 6:00 AM–10:00 PM
- Complimentary high-speed Wi-Fi
- On-site parking: $18/night
- Accessible rooms and step-free public access available on request
- Complimentary luggage storage before check-in and after check-out

The source of truth is `backend/app/knowledge.py`.

---

## API overview

### Base URLs

Local:

```text
http://localhost:8000/api/v1
```

Production:

```text
https://hospira-ai-ai-powered-hospitality.onrender.com/api/v1
```

### Health

```http
GET /api/v1/health
```

Example:

```bash
curl https://hospira-ai-ai-powered-hospitality.onrender.com/api/v1/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "hospira-ai",
  "mode": "public-demo"
}
```

### List conversations

Anonymous session IDs must be at least 16 characters long.

```bash
curl -i \
  -H "X-Anonymous-Session: demo-session-12345678" \
  https://hospira-ai-ai-powered-hospitality.onrender.com/api/v1/conversations
```

### Create a conversation

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Anonymous-Session: demo-session-12345678" \
  -d '{"title":"Premium Room"}' \
  https://hospira-ai-ai-powered-hospitality.onrender.com/api/v1/conversations
```

### Send a chat message

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-Anonymous-Session: demo-session-12345678" \
  -d '{"conversation_id":null,"message":"Tell me about the Premium Room"}' \
  https://hospira-ai-ai-powered-hospitality.onrender.com/api/v1/chat/message
```

### Search demo availability

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"check_in":"2026-10-01","check_out":"2026-10-04","guests":2}' \
  https://hospira-ai-ai-powered-hospitality.onrender.com/api/v1/availability/search
```

For a 3-night Premium Room example, the illustrative total is `$239 × 3 = $717`. No booking is created.

### Other available endpoints

```text
GET    /api/v1/rooms
GET    /api/v1/rooms/{room_id}
GET    /api/v1/memory
DELETE /api/v1/memory/{memory_id}
GET    /api/v1/conversations/{conversation_id}
PATCH  /api/v1/conversations/{conversation_id}
DELETE /api/v1/conversations/{conversation_id}
```

---

## Product, UX, engineering, and AI decisions

### Product

- Public demo with no registration friction.
- Hotel-specific assistant rather than a general-purpose chatbot.
- Availability is intentionally a demo capability, not a reservation system.
- Real booking and payment workflows are not exposed.

### UX

- Premium hotel visual direction using restrained typography, ivory/off-white surfaces, dark navy text, and sage-green accents.
- Quick prompts help a first-time visitor start a useful conversation.
- Availability search is expandable so it does not dominate the initial screen.
- Conversation history is visible in the sidebar.
- Anonymous session state persists in the current browser.
- Responsive layout adapts the sidebar and availability form on smaller screens.

### Engineering

- FastAPI provides a compact REST API with explicit Pydantic request/response schemas.
- SQLAlchemy handles persistence and keeps database access separate from UI code.
- Alembic provides repeatable schema migrations.
- Backend owns authoritative room facts and availability rules.
- CORS is configured on the API for the deployed frontend origin.
- Secrets remain server-side.

### AI

- Groq is called only by the backend; the browser does not receive the Groq key.
- The model receives supplied hotel knowledge and conversation context rather than unrestricted factual authority.
- Responses are requested in structured JSON and validated with Pydantic.
- The fallback path prevents fabricated room facts when the model is unavailable or uncertain.
- Unsupported general-knowledge questions are redirected toward hotel scope.

---

## Evaluation and test scenarios

### Automated tests

`backend/tests/test_core.py` covers:

- Public health endpoint.
- Anonymous conversation access.
- Anonymous session isolation.
- Chat persistence.
- Availability endpoint.
- Grounded Premium Room answer generation.
- Memory-based room resolution.
- Same-conversation pronoun resolution.
- Safe handling of unsupported questions.
- Conversation summary generation.
- Availability total calculation.
- Invalid availability dates.

Run:

```bash
cd backend
PYTHONPATH=. pytest -q
```

### Frontend verification

```bash
cd frontend
npm run typecheck
npm run build
```

### Observed deployment results

During the deployment session used for the current demo:

| Scenario | Observed result |
|---|---|
| Local FastAPI startup | Swagger UI loaded successfully at `/docs` |
| Local frontend startup | React/Vite UI loaded successfully |
| Render build | Build completed successfully |
| Render health endpoint | `GET /api/v1/health` returned `200 OK` |
| Render conversation endpoint with valid anonymous session | `200 OK` with the Vercel origin allowed by CORS |
| Database migration | Initial Alembic migration completed successfully during deployment |
| Vercel production deployment | Deployment reached `Ready` |
| Vercel → Render API connection | Working in the deployed frontend |
| Public demo behavior | No login or real booking flow |

Re-run the automated test commands after future changes.

---

## Deployment

### Render backend

Current production API:

```text
https://hospira-ai-ai-powered-hospitality.onrender.com
```

Current service configuration:

```text
Root Directory: .
Build Command: pip install -r backend/requirements.txt
Start Command: cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check Path: /api/v1/health
```

Backend environment variables are configured in Render, not in Git:

```text
PYTHON_VERSION=3.13.5
APP_ENV=production
DEBUG=false
SECRET_KEY=<secure-server-secret>
DATABASE_URL=<Supabase PostgreSQL connection string>
GROQ_API_KEY=<Groq API key>
GROQ_MODEL=llama-3.1-8b-instant
CORS_ORIGINS=https://hospira-ai-ai-powered-hospitality-a.vercel.app
```

Keep credentials out of commits and screenshots.

### Vercel frontend

Current production demo:

```text
https://hospira-ai-ai-powered-hospitality-a.vercel.app
```

Current configuration:

```text
Root Directory: frontend
Framework: Vite
Build Command: npm run build
Output Directory: dist
Install Command: npm install
```

The browser-facing application uses the deployed Render API. No database credentials, Groq keys, or server secrets belong in Vercel's frontend bundle.

---

## Anonymous sessions and privacy

The application deliberately does not authenticate visitors.

On first load, the browser generates a random anonymous session ID and stores it in `localStorage`. Each API call sends the ID through `X-Anonymous-Session`.

Important limitations:

- The session ID is not authentication.
- Clearing browser storage creates a new session scope.
- A different browser has a different scope.
- Anyone with access to the same browser profile can see its saved demo conversations.
- The public demo should not be used to store sensitive personal information.

---

## Security and operational notes

- `.env` files are excluded from source control.
- Groq credentials and database credentials are server-side only.
- The application should be treated as a demo rather than a production booking system.
- Free Render instances can sleep when idle, so first requests after inactivity can be slower.
- Production-grade authentication, rate limiting, monitoring, and booking integrations are still required before handling real guest transactions.

---

## Future improvements

- Move the frontend API URL fully back to environment-based configuration for easier local/staging/prod switching.
- Add disposable PostgreSQL integration tests.
- Add authentication and account-level data isolation for any real-world deployment.
- Add rate limiting and abuse protection for the public API.
- Add structured logging, monitoring, and error tracking.
- Replace demo availability with a real reservation/provider integration when product requirements call for it.
- Expand the hotel content and room comparison experience.

---

## Quick start

```bash
# backend
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# frontend - second terminal
cd frontend
npm install
npm run dev
```

Local frontend:

```text
http://localhost:5173
```

Production demo:

```text
https://hospira-ai-ai-powered-hospitality-a.vercel.app
```
