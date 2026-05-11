"""Base class and shared retry/rate-limit utilities for platform clients."""

import logging
import time
from abc import ABC, abstractmethod
from typing import Optional

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0  # seconds; doubles each attempt (exponential backoff)


class RateLimitError(Exception):
    """Raised when a platform enforces a rate limit."""
    def __init__(self, message: str, retry_after: Optional[float] = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class PlatformError(Exception):
    """Generic non-retryable platform error."""


class PlatformClient(ABC):
    """Abstract base for social-media platform clients."""

    platform_name: str = ""

    @abstractmethod
    def post(self, content: str) -> str:
        """Publish content and return the platform-assigned post ID."""

    @abstractmethod
    def verify_credentials(self) -> bool:
        """Return True if stored credentials are valid."""

    # ── Retry helper ──────────────────────────────────────────────────────

    def post_with_retry(self, content: str) -> str:
        """Call post() with exponential backoff on transient failures."""
        delay = RETRY_BASE_DELAY
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                return self.post(content)
            except RateLimitError as exc:
                wait = exc.retry_after or delay
                logger.warning(
                    "[%s] Rate-limited. Waiting %.0fs before retry %d/%d.",
                    self.platform_name, wait, attempt, MAX_RETRIES,
                )
                time.sleep(wait)
                delay *= 2
            except PlatformError:
                raise  # Non-retryable — propagate immediately
            except Exception as exc:
                if attempt == MAX_RETRIES:
                    raise PlatformError(
                        f"[{self.platform_name}] Failed after {MAX_RETRIES} attempts: {exc}"
                    ) from exc
                logger.warning(
                    "[%s] Transient error (attempt %d/%d): %s",
                    self.platform_name, attempt, MAX_RETRIES, exc,
                )
                time.sleep(delay)
                delay *= 2
        raise PlatformError(f"[{self.platform_name}] Exhausted retries")
