# Setup

Use `.env.example` as the configuration template. For production, use Supabase Auth for registration and login, Supabase PostgreSQL for `DATABASE_URL`, and a server-side Groq key. Never expose service-role, JWT-secret, database credentials, or Groq keys to the frontend.
