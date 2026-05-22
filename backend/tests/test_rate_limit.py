import pytest
from fastapi import HTTPException

from app.services.rate_limit import InMemoryRateLimiter


def test_rate_limiter_rejects_after_limit():
    limiter = InMemoryRateLimiter(limit=2, window_seconds=60)
    limiter.check("org")
    limiter.check("org")
    with pytest.raises(HTTPException) as exc:
        limiter.check("org")
    assert exc.value.status_code == 429
