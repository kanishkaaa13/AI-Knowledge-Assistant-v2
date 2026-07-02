from __future__ import annotations

import threading
import time
from collections import deque

from fastapi import HTTPException, Request, status

from app.core.config import settings


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str, *, limit: int, window_seconds: int) -> None:
        now = time.time()
        cutoff = now - window_seconds

        with self._lock:
            bucket = self._buckets.setdefault(key, deque())
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) >= limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests. Please slow down and try again shortly.",
                )

            bucket.append(now)


rate_limiter = InMemoryRateLimiter()


def client_identifier(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    if forwarded:
        return forwarded
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def apply_rate_limit(
    request: Request,
    *,
    scope: str,
    limit: int,
    user_id: str | None = None,
) -> None:
    identity = user_id or client_identifier(request)
    key = f"{scope}:{identity}"
    rate_limiter.check(
        key,
        limit=limit,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )
