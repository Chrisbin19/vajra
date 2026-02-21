"""
VAJRA — Shared FastAPI Auth Dependency

Defines verify_api_key so it can be imported cleanly by any route file.
Kept in its own module to avoid circular imports
(main.py imports routers; routers should not import from main.py).

Why FastAPI Security/Depends instead of middleware?
  Middleware approach  → works but is INVISIBLE in /docs Swagger UI.
  Security/Depends     → FastAPI auto-generates "Authorize 🔒" button in /docs.
                         Judges click it, enter the key once, all requests authenticated.
                         This is the standard production FastAPI pattern.

Usage in any endpoint:
    from api.dependencies import verify_api_key
    from fastapi import Depends

    @router.post("/some/endpoint")
    async def my_endpoint(..., api_key: str = Depends(verify_api_key)):
        ...
"""
import os
from fastapi import Security, HTTPException
from fastapi.security.api_key import APIKeyHeader

# Tells FastAPI to look for this header and render it in /docs OpenAPI schema
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

# Default demo key — judges use this if VAJRA_API_KEY is not set in .env
DEMO_KEY = "vajra-demo-key-2026"


async def verify_api_key(api_key: str = Security(API_KEY_HEADER)) -> str:
    """
    FastAPI security dependency — validates the X-API-Key request header.

    Key resolution order:
      1. os.getenv("VAJRA_API_KEY")  — override via .env for production
      2. DEMO_KEY = "vajra-demo-key-2026" — default for judges/demo

    Raises HTTP 403 if key is missing or wrong.
    Returns the validated key string on success.
    """
    expected = os.getenv("VAJRA_API_KEY", DEMO_KEY)
    if api_key != expected:
        raise HTTPException(
            status_code=403,
            detail="Invalid or missing API key. Include X-API-Key header.",
        )
    return api_key