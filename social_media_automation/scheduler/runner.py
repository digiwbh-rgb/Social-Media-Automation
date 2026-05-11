"""Post scheduler — polls the DB for due posts and publishes them."""

import logging
import signal
import time
from datetime import datetime, timezone
from typing import Optional

from ..config import AppConfig
from ..platforms.base import PlatformError
from ..platforms.factory import get_client
from ..storage.models import Database, Post, PostStatus

logger = logging.getLogger(__name__)

MAX_POST_RETRIES = 3


class Scheduler:
    """
    Background scheduler that polls for due posts and publishes them.

    Run as a daemon process with run_forever(), or call tick() in your
    own loop for testing / integration.
    """

    def __init__(self, config: AppConfig, db: Database) -> None:
        self._config = config
        self._db = db
        self._running = False

    def run_forever(self) -> None:
        """Block and process due posts every scheduler_interval_seconds."""
        self._running = True
        self._register_signals()

        interval = self._config.scheduler_interval_seconds
        logger.info("Scheduler started (interval=%ds).", interval)

        while self._running:
            try:
                self.tick()
            except Exception as exc:
                logger.error("Unexpected scheduler error: %s", exc, exc_info=True)
            time.sleep(interval)

        logger.info("Scheduler stopped.")

    def tick(self) -> int:
        """Process all posts due right now. Returns the number published."""
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        due = self._db.get_due_posts(now)

        if not due:
            logger.debug("No posts due at %s.", now.isoformat(timespec="seconds"))
            return 0

        logger.info("Processing %d due post(s).", len(due))
        published = 0
        for post in due:
            if self._publish(post):
                published += 1
        return published

    def _publish(self, post: Post) -> bool:
        logger.info(
            "Publishing post id=%d platform=%s scheduled_at=%s",
            post.id, post.platform, post.scheduled_at,
        )
        try:
            client = get_client(post.platform, self._config)
            platform_id = client.post_with_retry(post.content)
            self._db.update_post_status(
                post.id,
                PostStatus.PUBLISHED,
                platform_id=platform_id,
                published_at=datetime.utcnow(),
            )
            logger.info("Post id=%d published (platform_id=%s).", post.id, platform_id)
            return True

        except PlatformError as exc:
            new_retry = (post.retry_count or 0) + 1
            if new_retry >= MAX_POST_RETRIES:
                logger.error(
                    "Post id=%d failed permanently after %d attempts: %s",
                    post.id, new_retry, exc,
                )
                self._db.update_post_status(
                    post.id,
                    PostStatus.FAILED,
                    error_message=str(exc),
                    retry_count=new_retry,
                )
            else:
                logger.warning(
                    "Post id=%d failed (attempt %d/%d): %s — will retry.",
                    post.id, new_retry, MAX_POST_RETRIES, exc,
                )
                # Keep status PENDING so next tick retries
                self._db.update_post_status(
                    post.id,
                    PostStatus.PENDING,
                    error_message=str(exc),
                    retry_count=new_retry,
                )
            return False

        except Exception as exc:
            logger.exception("Unexpected error publishing post id=%d: %s", post.id, exc)
            self._db.update_post_status(
                post.id,
                PostStatus.FAILED,
                error_message=f"Unexpected error: {exc}",
            )
            return False

    def _register_signals(self) -> None:
        def _stop(signum, frame):
            logger.info("Received signal %d — stopping scheduler.", signum)
            self._running = False

        signal.signal(signal.SIGTERM, _stop)
        signal.signal(signal.SIGINT, _stop)

    def stop(self) -> None:
        self._running = False
