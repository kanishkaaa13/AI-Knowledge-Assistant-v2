from __future__ import annotations

import jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.rate_limit import apply_rate_limit, client_identifier


PUBLIC_PATH_PREFIXES = {
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Production-specific caching
        if settings.APP_ENV.lower() == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class JWTContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request.state.user_id = None
        request.state.client_id = client_identifier(request)

        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(
                    token,
                    settings.JWT_SECRET_KEY,
                    algorithms=["HS256"],
                    options={"require": ["sub", "exp"]},
                )
                request.state.user_id = payload.get("sub")
            except jwt.PyJWTError:
                request.state.user_id = None

        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        if path in PUBLIC_PATH_PREFIXES or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        limit = settings.RATE_LIMIT_MAX_REQUESTS
        if "/auth/" in path:
            limit = settings.RATE_LIMIT_AUTH_MAX_REQUESTS
        elif "/documents/upload" in path:
            limit = settings.RATE_LIMIT_UPLOAD_MAX_REQUESTS

        apply_rate_limit(
            request,
            scope=path,
            limit=limit,
            user_id=getattr(request.state, "user_id", None),
        )
        return await call_next(request)


class CORSFallbackMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        origin = request.headers.get("origin", "")
        
        # Check against main app allowed origins
        from app.main import is_origin_allowed
        
        if is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        return response
