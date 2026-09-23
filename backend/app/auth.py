from fastapi import Header, HTTPException
from jose import jwt, JWTError
from .config import get_settings

async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Authentication required")
    token = authorization.split(" ", 1)[1]
    settings = get_settings()
    try:
        if settings.supabase_jwt_secret:
            payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
        else:
            payload = jwt.get_unverified_claims(token)
        user_id = payload.get("sub")
        if not user_id: raise ValueError()
        return {"id": user_id, "email": payload.get("email"), "name": (payload.get("user_metadata") or {}).get("full_name")}
    except (JWTError, ValueError):
        raise HTTPException(401, "Invalid or expired authentication token")
