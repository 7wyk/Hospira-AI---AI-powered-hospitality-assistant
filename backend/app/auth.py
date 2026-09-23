from fastapi import Header, HTTPException
from jose import JWTError, jwt
from .config import get_settings

async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    settings = get_settings()
    try:
        if settings.supabase_jwt_secret:
            payload = jwt.decode(token, settings.supabase_jwt_secret, algorithms=["HS256"], audience="authenticated")
        elif settings.is_production:
            raise HTTPException(status_code=503, detail="Authentication provider is not configured")
        else:
            payload = jwt.get_unverified_claims(token)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("missing subject")
        return {"id": user_id, "email": payload.get("email"), "name": (payload.get("user_metadata") or {}).get("full_name")}
    except HTTPException:
        raise
    except (JWTError, ValueError):
        raise HTTPException(status_code=401, detail="Invalid or expired authentication token")
