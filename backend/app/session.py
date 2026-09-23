from uuid import uuid4
from fastapi import Header, HTTPException

async def anonymous_session(x_anonymous_session: str | None = Header(default=None, alias="X-Anonymous-Session")) -> str:
    """Return a browser-owned demo session; no authenticated identity is implied."""
    if not x_anonymous_session:
        # Stateless API callers get an isolated ephemeral scope; the frontend persists its own ID.
        return f"ephemeral-{uuid4()}"
    value = x_anonymous_session.strip()
    if len(value) < 16 or len(value) > 128 or any(ch not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for ch in value):
        raise HTTPException(status_code=400, detail="Invalid anonymous session identifier")
    return value
