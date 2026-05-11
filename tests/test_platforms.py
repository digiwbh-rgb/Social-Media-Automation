"""Tests for platform clients using mocked HTTP responses."""

import pytest
import responses as resp_lib

from social_media_automation.config import TwitterConfig, LinkedInConfig
from social_media_automation.platforms.base import PlatformError, RateLimitError
from social_media_automation.platforms.twitter import TwitterClient, TWEETS_ENDPOINT, VERIFY_ENDPOINT
from social_media_automation.platforms.linkedin import LinkedInClient, UGC_POSTS_ENDPOINT, USERINFO_ENDPOINT


def _twitter_config() -> TwitterConfig:
    return TwitterConfig(
        api_key="key", api_secret="secret",
        access_token="token", access_token_secret="token_secret",
    )


def _linkedin_config() -> LinkedInConfig:
    return LinkedInConfig(
        client_id="cid", client_secret="csec",
        access_token="li_token", person_urn="urn:li:person:ABC123",
    )


class TestTwitterClient:
    @resp_lib.activate
    def test_post_success(self):
        resp_lib.add(
            resp_lib.POST, TWEETS_ENDPOINT,
            json={"data": {"id": "123456789", "text": "Hello world"}},
            status=200,
        )
        client = TwitterClient(_twitter_config())
        tweet_id = client.post("Hello world")
        assert tweet_id == "123456789"

    @resp_lib.activate
    def test_post_rate_limited(self):
        resp_lib.add(
            resp_lib.POST, TWEETS_ENDPOINT,
            json={"title": "Too Many Requests"},
            status=429,
            headers={"retry-after": "1"},
        )
        client = TwitterClient(_twitter_config())
        with pytest.raises(RateLimitError):
            client.post("Hello")

    @resp_lib.activate
    def test_post_auth_error(self):
        resp_lib.add(resp_lib.POST, TWEETS_ENDPOINT, json={"error": "Forbidden"}, status=403)
        client = TwitterClient(_twitter_config())
        with pytest.raises(PlatformError, match="auth error 403"):
            client.post("Hello")

    def test_post_too_long(self):
        client = TwitterClient(_twitter_config())
        long_text = "x" * 281
        with pytest.raises(PlatformError, match="character limit"):
            client.post(long_text)

    def test_missing_credentials(self):
        client = TwitterClient(TwitterConfig())
        with pytest.raises(PlatformError, match="credentials incomplete"):
            client.post("Hello")

    @resp_lib.activate
    def test_verify_credentials_ok(self):
        resp_lib.add(resp_lib.GET, VERIFY_ENDPOINT, json={"data": {"id": "1"}}, status=200)
        assert TwitterClient(_twitter_config()).verify_credentials() is True

    @resp_lib.activate
    def test_verify_credentials_fail(self):
        resp_lib.add(resp_lib.GET, VERIFY_ENDPOINT, json={}, status=401)
        assert TwitterClient(_twitter_config()).verify_credentials() is False


class TestLinkedInClient:
    @resp_lib.activate
    def test_post_success(self):
        resp_lib.add(
            resp_lib.POST, UGC_POSTS_ENDPOINT,
            json={}, status=201,
            headers={"X-RestLi-Id": "urn:li:ugcPost:999"},
        )
        client = LinkedInClient(_linkedin_config())
        post_urn = client.post("Hello LinkedIn")
        assert post_urn == "urn:li:ugcPost:999"

    @resp_lib.activate
    def test_post_rate_limited(self):
        resp_lib.add(
            resp_lib.POST, UGC_POSTS_ENDPOINT,
            json={"message": "Too many requests"},
            status=429,
            headers={"retry-after": "1"},
        )
        client = LinkedInClient(_linkedin_config())
        with pytest.raises(RateLimitError):
            client.post("Hello")

    @resp_lib.activate
    def test_post_auth_error(self):
        resp_lib.add(resp_lib.POST, UGC_POSTS_ENDPOINT, json={}, status=401)
        client = LinkedInClient(_linkedin_config())
        with pytest.raises(PlatformError, match="auth error 401"):
            client.post("Hello")

    def test_post_too_long(self):
        client = LinkedInClient(_linkedin_config())
        with pytest.raises(PlatformError, match="character limit"):
            client.post("x" * 3001)

    def test_missing_token(self):
        client = LinkedInClient(LinkedInConfig(person_urn="urn:li:person:X"))
        with pytest.raises(PlatformError, match="access token missing"):
            client.post("Hello")

    def test_missing_person_urn(self):
        client = LinkedInClient(LinkedInConfig(access_token="tok"))
        with pytest.raises(PlatformError, match="person URN missing"):
            client.post("Hello")


class TestRetryLogic:
    @resp_lib.activate
    def test_retries_on_transient_error(self, monkeypatch):
        """post_with_retry should retry on non-auth, non-rate-limit errors."""
        monkeypatch.setattr("social_media_automation.platforms.base.RETRY_BASE_DELAY", 0.01)
        monkeypatch.setattr("social_media_automation.platforms.base.MAX_RETRIES", 3)

        # Fail twice then succeed on third attempt
        resp_lib.add(resp_lib.POST, TWEETS_ENDPOINT, json={}, status=500)
        resp_lib.add(resp_lib.POST, TWEETS_ENDPOINT, json={}, status=500)
        resp_lib.add(
            resp_lib.POST, TWEETS_ENDPOINT,
            json={"data": {"id": "777"}}, status=200,
        )
        client = TwitterClient(_twitter_config())
        tweet_id = client.post_with_retry("Retry test")
        assert tweet_id == "777"
