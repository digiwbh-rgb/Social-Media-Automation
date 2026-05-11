"""Tests for the SQLite storage layer."""

import tempfile
from datetime import datetime, timedelta

import pytest

from social_media_automation.storage.models import Database, Post, PostStatus


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    yield Database(path)
    import os; os.unlink(path)


def _make_post(platform="twitter", minutes_from_now=10) -> Post:
    return Post(
        id=None,
        platform=platform,
        content="Test post content",
        scheduled_at=datetime.utcnow() + timedelta(minutes=minutes_from_now),
    )


class TestPostCRUD:
    def test_create_and_get(self, db):
        post = db.create_post(_make_post())
        assert post.id is not None

        fetched = db.get_post(post.id)
        assert fetched.content == "Test post content"
        assert fetched.platform == "twitter"
        assert fetched.status == PostStatus.PENDING

    def test_list_posts_filter_by_platform(self, db):
        db.create_post(_make_post("twitter"))
        db.create_post(_make_post("linkedin"))

        twitter_posts = db.list_posts(platform="twitter")
        assert all(p.platform == "twitter" for p in twitter_posts)
        assert len(twitter_posts) == 1

    def test_list_posts_filter_by_status(self, db):
        post = db.create_post(_make_post())
        db.update_post_status(post.id, PostStatus.PUBLISHED)

        pending = db.list_posts(status=PostStatus.PENDING)
        published = db.list_posts(status=PostStatus.PUBLISHED)

        assert len(pending) == 0
        assert len(published) == 1

    def test_get_due_posts(self, db):
        past = Post(id=None, platform="twitter", content="Past", scheduled_at=datetime(2000, 1, 1))
        future = Post(id=None, platform="twitter", content="Future", scheduled_at=datetime(2099, 1, 1))
        db.create_post(past)
        db.create_post(future)

        due = db.get_due_posts(datetime.utcnow())
        assert len(due) == 1
        assert due[0].content == "Past"

    def test_update_status_to_published(self, db):
        post = db.create_post(_make_post())
        pub_time = datetime.utcnow()
        db.update_post_status(
            post.id,
            PostStatus.PUBLISHED,
            platform_id="tweet_abc123",
            published_at=pub_time,
        )
        updated = db.get_post(post.id)
        assert updated.status == PostStatus.PUBLISHED
        assert updated.platform_id == "tweet_abc123"

    def test_update_status_with_error(self, db):
        post = db.create_post(_make_post())
        db.update_post_status(post.id, PostStatus.FAILED, error_message="Auth error")
        updated = db.get_post(post.id)
        assert updated.status == PostStatus.FAILED
        assert updated.error_message == "Auth error"

    def test_delete_post(self, db):
        post = db.create_post(_make_post())
        assert db.delete_post(post.id) is True
        assert db.get_post(post.id) is None

    def test_delete_nonexistent(self, db):
        assert db.delete_post(99999) is False


class TestGeneratedContent:
    def test_save_and_list(self, db):
        from social_media_automation.storage.models import GeneratedContent

        gc = GeneratedContent(
            id=None, topic="AI trends", platform="linkedin",
            tone="professional", content="Some generated text."
        )
        saved = db.save_generated_content(gc)
        assert saved.id is not None

        items = db.list_generated_content(platform="linkedin")
        assert len(items) == 1
        assert items[0].topic == "AI trends"

    def test_mark_used(self, db):
        from social_media_automation.storage.models import GeneratedContent

        gc = GeneratedContent(
            id=None, topic="test", platform="twitter",
            tone="casual", content="Hey!"
        )
        saved = db.save_generated_content(gc)
        db.mark_content_used(saved.id)

        unused = db.list_generated_content(unused_only=True)
        assert all(not item.used for item in unused)
