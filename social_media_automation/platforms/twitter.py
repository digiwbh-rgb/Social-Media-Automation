"""Twitter/X v2 API client using OAuth 1.0a (user context) for posting."""

import logging
from typing import Optional

import requests
from requests_oauthlib import OAuth1

from .base import PlatformClient, PlatformError, RateLimitError
from ..config import TwitterConfig

logger = logging.getLogger(__name__)

TWEET_MAX_LEN = 280
TWEETS_ENDPOINT = "https://api.twitter.com/2/tweets"
VERIFY_ENDPOINT = "https://api.twitter.com/2/users/me"


class TwitterClient(PlatformClient):
    """Wraps Twitter API v2 for authenticated tweet creation."""

    platform_name = "twitter"

    def __init__(self, config: TwitterConfig) -> None:
        self._config = config
        self._auth = OAuth1(
            config.api_key,
            config.api_secret,
            config.access_token,
            config.access_token_secret,
        )

    def _check_config(self) -> None:
        required = [
            self._config.api_key,
            self._config.api_secret,
            self._config.access_token,
            self._config.access_token_secret,
        ]
        if not all(required):
            raise PlatformError(
                "Twitter credentials incomplete. Set TWITTER_API_KEY, "
                "TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, and "
                "TWITTER_ACCESS_TOKEN_SECRET."
            )

    def post(self, content: str) -> str:
        """Create a tweet and return the tweet ID."""
        self._check_config()

        if len(content) > TWEET_MAX_LEN:
            raise PlatformError(
                f"Content exceeds Twitter's {TWEET_MAX_LEN}-character limit "
                f"({len(content)} chars)."
            )

        response = requests.post(
            TWEETS_ENDPOINT,
            auth=self._auth,
            json={"text": content},
            timeout=30,
        )
        return self._handle_response(response)

    def verify_credentials(self) -> bool:
        try:
            self._check_config()
            resp = requests.get(VERIFY_ENDPOINT, auth=self._auth, timeout=15)
            return resp.status_code == 200
        except Exception as exc:
            logger.debug("Twitter credential check failed: %s", exc)
            return False

    # ── Internal ──────────────────────────────────────────────────────────

    def _handle_response(self, response: requests.Response) -> str:
        if response.status_code == 429:
            retry_after: Optional[float] = None
            try:
                retry_after = float(response.headers.get("retry-after", 60))
            except (TypeError, ValueError):
                retry_after = 60.0
            raise RateLimitError(
                f"Twitter rate limit exceeded.", retry_after=retry_after
            )

        if response.status_code in (401, 403):
            raise PlatformError(
                f"Twitter auth error {response.status_code}: {response.text}"
            )

        if not response.ok:
            raise Exception(
                f"Twitter API error {response.status_code}: {response.text}"
            )

        data = response.json()
        tweet_id: str = data["data"]["id"]
        logger.info("Tweet posted successfully (id=%s).", tweet_id)
        return tweet_id
