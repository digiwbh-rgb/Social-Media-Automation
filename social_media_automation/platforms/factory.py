"""Factory that builds the right PlatformClient from config."""

from ..config import AppConfig
from .base import PlatformClient, PlatformError
from .twitter import TwitterClient
from .linkedin import LinkedInClient


def get_client(platform: str, config: AppConfig) -> PlatformClient:
    platform = platform.lower()
    if platform == "twitter":
        return TwitterClient(config.twitter)
    if platform == "linkedin":
        return LinkedInClient(config.linkedin)
    raise PlatformError(f"Unsupported platform: '{platform}'. Choose twitter or linkedin.")
