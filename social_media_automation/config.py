"""Configuration management — loads from env vars and persists tokens securely."""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


CONFIG_DIR = Path.home() / ".social_media_automation"
CONFIG_FILE = CONFIG_DIR / "config.json"
TOKENS_FILE = CONFIG_DIR / "tokens.json"  # stored separately, chmod 600
DB_FILE = CONFIG_DIR / "posts.db"


@dataclass
class TwitterConfig:
    api_key: str = ""
    api_secret: str = ""
    access_token: str = ""
    access_token_secret: str = ""
    bearer_token: str = ""


@dataclass
class LinkedInConfig:
    client_id: str = ""
    client_secret: str = ""
    access_token: str = ""
    person_urn: str = ""  # urn:li:person:<id>


@dataclass
class ClaudeConfig:
    api_key: str = ""
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 1024


@dataclass
class AppConfig:
    twitter: TwitterConfig = field(default_factory=TwitterConfig)
    linkedin: LinkedInConfig = field(default_factory=LinkedInConfig)
    claude: ClaudeConfig = field(default_factory=ClaudeConfig)
    db_path: str = str(DB_FILE)
    scheduler_interval_seconds: int = 60


def _ensure_config_dir() -> None:
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def load_config() -> AppConfig:
    """Load config from file + env var overrides (env vars take precedence)."""
    _ensure_config_dir()

    stored: dict = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            stored = json.load(f)

    tokens: dict = {}
    if TOKENS_FILE.exists():
        with open(TOKENS_FILE) as f:
            tokens = json.load(f)

    tw = stored.get("twitter", {})
    tok_tw = tokens.get("twitter", {})
    li = stored.get("linkedin", {})
    tok_li = tokens.get("linkedin", {})
    cl = stored.get("claude", {})

    config = AppConfig(
        twitter=TwitterConfig(
            api_key=os.getenv("TWITTER_API_KEY", tw.get("api_key", "")),
            api_secret=os.getenv("TWITTER_API_SECRET", tw.get("api_secret", "")),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN", tok_tw.get("access_token", "")),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET", tok_tw.get("access_token_secret", "")),
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN", tw.get("bearer_token", "")),
        ),
        linkedin=LinkedInConfig(
            client_id=os.getenv("LINKEDIN_CLIENT_ID", li.get("client_id", "")),
            client_secret=os.getenv("LINKEDIN_CLIENT_SECRET", li.get("client_secret", "")),
            access_token=os.getenv("LINKEDIN_ACCESS_TOKEN", tok_li.get("access_token", "")),
            person_urn=os.getenv("LINKEDIN_PERSON_URN", li.get("person_urn", "")),
        ),
        claude=ClaudeConfig(
            api_key=os.getenv("ANTHROPIC_API_KEY", cl.get("api_key", "")),
            model=os.getenv("CLAUDE_MODEL", cl.get("model", "claude-sonnet-4-6")),
            max_tokens=int(os.getenv("CLAUDE_MAX_TOKENS", cl.get("max_tokens", 1024))),
        ),
        db_path=os.getenv("DB_PATH", stored.get("db_path", str(DB_FILE))),
        scheduler_interval_seconds=int(
            os.getenv("SCHEDULER_INTERVAL", stored.get("scheduler_interval_seconds", 60))
        ),
    )
    return config


def save_config(config: AppConfig) -> None:
    """Persist non-secret config values; tokens go to the restricted tokens file."""
    _ensure_config_dir()

    cfg_data = {
        "twitter": {
            "api_key": config.twitter.api_key,
            "api_secret": config.twitter.api_secret,
            "bearer_token": config.twitter.bearer_token,
        },
        "linkedin": {
            "client_id": config.linkedin.client_id,
            "client_secret": config.linkedin.client_secret,
            "person_urn": config.linkedin.person_urn,
        },
        "claude": {
            "api_key": config.claude.api_key,
            "model": config.claude.model,
            "max_tokens": config.claude.max_tokens,
        },
        "db_path": config.db_path,
        "scheduler_interval_seconds": config.scheduler_interval_seconds,
    }

    token_data = {
        "twitter": {
            "access_token": config.twitter.access_token,
            "access_token_secret": config.twitter.access_token_secret,
        },
        "linkedin": {
            "access_token": config.linkedin.access_token,
        },
    }

    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg_data, f, indent=2)

    # Tokens file: owner read-only
    TOKENS_FILE.touch(mode=0o600, exist_ok=True)
    with open(TOKENS_FILE, "w") as f:
        json.dump(token_data, f, indent=2)
    TOKENS_FILE.chmod(0o600)
