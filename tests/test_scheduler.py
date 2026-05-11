"""Tests for the scheduler's tick() logic."""

import tempfile
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from social_media_automation.config import AppConfig, TwitterConfig, LinkedInConfig, ClaudeConfig
from social_media_automation.scheduler.runner import Scheduler
from social_media_automation.storage.models import Database, Post, PostStatus


def _config() -> AppConfig:
    return AppConfig(
        twitter=TwitterConfig(
            api_key="k", api_secret="s",
            access_token="t", access_token_secret="ts",
        ),
        linkedin=LinkedInConfig(
            client_id="c", client_secret="cs",
            access_token="li", person_urn="urn:li:person:X",
        ),
        claude=ClaudeConfig(api_key="ant"),
        scheduler_interval_seconds=1,
    )


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=True) as f:
        yield Database(f.name)


def _due_post(db: Database, platform="twitter") -> Post:
    return db.create_post(Post(
        id=None,
        platform=platform,
        content="Scheduled content",
        scheduled_at=datetime(2000, 1, 1),  # always in the past
    ))


class TestSchedulerTick:
    def test_publishes_due_post(self, db):
        post = _due_post(db)
        mock_client = MagicMock()
        mock_client.post_with_retry.return_value = "platform_id_1"

        with patch("social_media_automation.scheduler.runner.get_client", return_value=mock_client):
            scheduler = Scheduler(_config(), db)
            published = scheduler.tick()

        assert published == 1
        updated = db.get_post(post.id)
        assert updated.status == PostStatus.PUBLISHED
        assert updated.platform_id == "platform_id_1"

    def test_no_posts_due(self, db):
        db.create_post(Post(
            id=None, platform="twitter", content="Future",
            scheduled_at=datetime(2099, 1, 1),
        ))
        scheduler = Scheduler(_config(), db)
        assert scheduler.tick() == 0

    def test_marks_failed_after_max_retries(self, db):
        from social_media_automation.platforms.base import PlatformError
        post = _due_post(db)
        # Simulate already at MAX_RETRIES - 1
        db.update_post_status(post.id, PostStatus.PENDING, retry_count=2)

        mock_client = MagicMock()
        mock_client.post_with_retry.side_effect = PlatformError("Auth failed")

        with patch("social_media_automation.scheduler.runner.get_client", return_value=mock_client):
            scheduler = Scheduler(_config(), db)
            scheduler.tick()

        updated = db.get_post(post.id)
        assert updated.status == PostStatus.FAILED
        assert "Auth failed" in updated.error_message

    def test_keeps_pending_on_first_failure(self, db):
        from social_media_automation.platforms.base import PlatformError
        post = _due_post(db)

        mock_client = MagicMock()
        mock_client.post_with_retry.side_effect = PlatformError("Transient")

        with patch("social_media_automation.scheduler.runner.get_client", return_value=mock_client):
            scheduler = Scheduler(_config(), db)
            scheduler.tick()

        updated = db.get_post(post.id)
        assert updated.status == PostStatus.PENDING
        assert updated.retry_count == 1
