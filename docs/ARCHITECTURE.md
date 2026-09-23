# Architecture

The frontend is a Vite React client. The backend is a FastAPI application with Pydantic contracts, SQLAlchemy persistence, a hotel knowledge module, grounded response service, and bearer-token authentication dependency. User ownership is derived from the validated token, never from a client-supplied user ID.
