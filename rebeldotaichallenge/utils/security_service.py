from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from rebeldotaichallenge._params import API_KEY


class SecurityService:
    if not API_KEY:
        raise ValueError("API_KEY is not set")
    api_key_header = APIKeyHeader(
        name="X-API-Key", auto_error=False, scheme_name="API Key"
    )

    @staticmethod
    async def get_api_key(api_key: str = Security(api_key_header)):
        """Verify the general API key."""
        if not api_key or api_key != API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing API Key",
            )
        return api_key
