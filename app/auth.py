from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader

from app.config import settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_user_key(api_key: str = Security(api_key_header)):
    if api_key not in (settings.api_key_user, settings.api_key_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="invalid_api_key")
    return api_key


async def require_admin_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin_api_key_required")
    return api_key
