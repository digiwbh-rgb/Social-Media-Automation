"""LinkedIn API v2 client for creating text posts (UGC Posts)."""

import logging
from typing import Optional

import requests

from .base import PlatformClient, PlatformError, RateLimitError
from ..config import LinkedInConfig

logger = logging.getLogger(__name__)

UGC_POSTS_ENDPOINT = "https://api.linkedin.com/v2/ugcPosts"
USERINFO_ENDPOINT = "https://api.linkedin.com/v2/userinfo"
POST_MAX_LEN = 3000


class LinkedInClient(PlatformClient):
    """Wraps LinkedIn UGC Posts API for creating text shares."""

    platform_name = "linkedin"

    def __init__(self, config: LinkedInConfig) -> None:
        self._config = config

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._config.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def _check_config(self) -> None:
        if not self._config.access_token:
            raise PlatformError(
                "LinkedIn access token missing. Set LINKEDIN_ACCESS_TOKEN."
            )
        if not self._config.person_urn:
            raise PlatformError(
                "LinkedIn person URN missing. Set LINKEDIN_PERSON_URN "
                "(format: urn:li:person:<id>)."
            )

    def post(self, content: str) -> str:
        """Create a LinkedIn UGC post and return the post URN."""
        self._check_config()

        if len(content) > POST_MAX_LEN:
            raise PlatformError(
                f"Content exceeds LinkedIn's {POST_MAX_LEN}-character limit "
                f"({len(content)} chars)."
            )

        payload = {
            "author": self._config.person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        response = requests.post(
            UGC_POSTS_ENDPOINT,
            headers=self._headers(),
            json=payload,
            timeout=30,
        )
        return self._handle_response(response)

    def verify_credentials(self) -> bool:
        try:
            self._check_config()
            resp = requests.get(
                USERINFO_ENDPOINT, headers=self._headers(), timeout=15
            )
            return resp.status_code == 200
        except Exception as exc:
            logger.debug("LinkedIn credential check failed: %s", exc)
            return False

    def _handle_response(self, response: requests.Response) -> str:
        if response.status_code == 429:
            retry_after: Optional[float] = None
            try:
                retry_after = float(response.headers.get("retry-after", 60))
            except (TypeError, ValueError):
                retry_after = 60.0
            raise RateLimitError("LinkedIn rate limit exceeded.", retry_after=retry_after)

        if response.status_code in (401, 403):
            raise PlatformError(
                f"LinkedIn auth error {response.status_code}: {response.text}"
            )

        if not response.ok:
            raise Exception(
                f"LinkedIn API error {response.status_code}: {response.text}"
            )

        # LinkedIn returns the post URN in the X-RestLi-Id header
        post_urn = response.headers.get("X-RestLi-Id", "")
        logger.info("LinkedIn post created (urn=%s).", post_urn)
        return post_urn
