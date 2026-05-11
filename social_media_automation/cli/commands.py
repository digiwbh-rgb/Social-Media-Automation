"""CLI commands implemented with Click."""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

import click
from tabulate import tabulate

from ..config import load_config, save_config
from ..content.generator import ContentGenerator, GenerationRequest
from ..platforms.factory import get_client
from ..scheduler.runner import Scheduler
from ..storage.models import Database, Platform, Post, PostStatus

logger = logging.getLogger(__name__)

PLATFORMS = [p.value for p in Platform]
TONES = ["professional", "casual", "humorous", "inspirational", "educational"]


# ── Helpers ────────────────────────────────────────────────────────────────

def _get_db() -> Database:
    config = load_config()
    return Database(config.db_path)


def _echo_success(msg: str) -> None:
    click.echo(click.style(f"✓ {msg}", fg="green"))


def _echo_error(msg: str) -> None:
    click.echo(click.style(f"✗ {msg}", fg="red"), err=True)


def _echo_info(msg: str) -> None:
    click.echo(click.style(f"  {msg}", fg="cyan"))


def _parse_datetime(value: str) -> datetime:
    """Parse ISO-8601 datetime string; assume UTC if no timezone given."""
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise click.BadParameter(
        f"Cannot parse '{value}'. Use ISO format: YYYY-MM-DDTHH:MM or YYYY-MM-DD HH:MM"
    )


def _format_posts_table(posts) -> str:
    rows = []
    for p in posts:
        sched = p.scheduled_at.strftime("%Y-%m-%d %H:%M") if p.scheduled_at else "-"
        pub = p.published_at.strftime("%Y-%m-%d %H:%M") if p.published_at else "-"
        preview = (p.content[:60] + "…") if len(p.content) > 60 else p.content
        rows.append([p.id, p.platform, p.status, sched, pub, preview])
    return tabulate(
        rows,
        headers=["ID", "Platform", "Status", "Scheduled", "Published", "Content"],
        tablefmt="rounded_outline",
    )


# ── Root group ─────────────────────────────────────────────────────────────

@click.group()
@click.option("--debug", is_flag=True, help="Enable debug logging.")
def cli(debug: bool) -> None:
    """Social Media Automation Tool — schedule, generate, and publish posts."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


# ── config group ──────────────────────────────────────────────────────────

@cli.group("config")
def config_group():
    """Manage API credentials and application settings."""


@config_group.command("set-twitter")
@click.option("--api-key", prompt="Twitter API Key", help="Twitter API key (consumer key).")
@click.option("--api-secret", prompt="Twitter API Secret", hide_input=True)
@click.option("--access-token", prompt="Access Token")
@click.option("--access-token-secret", prompt="Access Token Secret", hide_input=True)
@click.option("--bearer-token", default="", prompt="Bearer Token (optional)", prompt_required=False)
def config_set_twitter(api_key, api_secret, access_token, access_token_secret, bearer_token):
    """Store Twitter OAuth credentials."""
    config = load_config()
    config.twitter.api_key = api_key
    config.twitter.api_secret = api_secret
    config.twitter.access_token = access_token
    config.twitter.access_token_secret = access_token_secret
    config.twitter.bearer_token = bearer_token
    save_config(config)
    _echo_success("Twitter credentials saved.")


@config_group.command("set-linkedin")
@click.option("--client-id", prompt="LinkedIn Client ID")
@click.option("--client-secret", prompt="LinkedIn Client Secret", hide_input=True)
@click.option("--access-token", prompt="LinkedIn Access Token", hide_input=True)
@click.option("--person-urn", prompt="Person URN (urn:li:person:<id>)")
def config_set_linkedin(client_id, client_secret, access_token, person_urn):
    """Store LinkedIn OAuth credentials."""
    config = load_config()
    config.linkedin.client_id = client_id
    config.linkedin.client_secret = client_secret
    config.linkedin.access_token = access_token
    config.linkedin.person_urn = person_urn
    save_config(config)
    _echo_success("LinkedIn credentials saved.")


@config_group.command("set-claude")
@click.option("--api-key", prompt="Anthropic API Key", hide_input=True)
@click.option("--model", default="claude-sonnet-4-6", show_default=True)
def config_set_claude(api_key, model):
    """Store Claude / Anthropic API key."""
    config = load_config()
    config.claude.api_key = api_key
    config.claude.model = model
    save_config(config)
    _echo_success("Claude credentials saved.")


@config_group.command("show")
def config_show():
    """Display current configuration (secrets masked)."""
    config = load_config()

    def mask(value: str) -> str:
        if not value:
            return "(not set)"
        return value[:4] + "****" + value[-2:] if len(value) > 6 else "****"

    rows = [
        ["Twitter API Key", mask(config.twitter.api_key)],
        ["Twitter Bearer Token", mask(config.twitter.bearer_token)],
        ["Twitter Access Token", mask(config.twitter.access_token)],
        ["LinkedIn Client ID", mask(config.linkedin.client_id)],
        ["LinkedIn Access Token", mask(config.linkedin.access_token)],
        ["LinkedIn Person URN", config.linkedin.person_urn or "(not set)"],
        ["Claude API Key", mask(config.claude.api_key)],
        ["Claude Model", config.claude.model],
        ["DB Path", config.db_path],
        ["Scheduler Interval", f"{config.scheduler_interval_seconds}s"],
    ]
    click.echo(tabulate(rows, headers=["Setting", "Value"], tablefmt="rounded_outline"))


@config_group.command("verify")
@click.argument("platform", type=click.Choice(PLATFORMS))
def config_verify(platform):
    """Test that credentials for a platform are valid."""
    config = load_config()
    try:
        client = get_client(platform, config)
        if client.verify_credentials():
            _echo_success(f"{platform.capitalize()} credentials are valid.")
        else:
            _echo_error(f"{platform.capitalize()} credential verification failed.")
            sys.exit(1)
    except Exception as exc:
        _echo_error(str(exc))
        sys.exit(1)


# ── post group ────────────────────────────────────────────────────────────

@cli.group("post")
def post_group():
    """Create, list, and manage scheduled posts."""


@post_group.command("schedule")
@click.argument("platform", type=click.Choice(PLATFORMS))
@click.option("--content", "-c", help="Post text. Omit to enter in $EDITOR.")
@click.option(
    "--at",
    "scheduled_at",
    required=True,
    help="Schedule datetime in ISO format: 2025-06-01T14:30",
)
def post_schedule(platform, content, scheduled_at):
    """Schedule a post for future publishing."""
    if not content:
        content = click.edit("# Enter your post content here (delete this line)\n")
        if not content:
            _echo_error("No content provided.")
            sys.exit(1)
        content = "\n".join(
            line for line in content.splitlines() if not line.startswith("#")
        ).strip()

    try:
        sched_dt = _parse_datetime(scheduled_at)
    except click.BadParameter as exc:
        _echo_error(str(exc))
        sys.exit(1)

    db = _get_db()
    post = db.create_post(Post(
        id=None,
        platform=platform,
        content=content,
        scheduled_at=sched_dt,
    ))
    _echo_success(f"Post #{post.id} scheduled for {sched_dt.strftime('%Y-%m-%d %H:%M')} on {platform}.")


@post_group.command("publish-now")
@click.argument("platform", type=click.Choice(PLATFORMS))
@click.option("--content", "-c", required=True, help="Post text to publish immediately.")
def post_publish_now(platform, content):
    """Publish a post immediately without scheduling."""
    config = load_config()
    try:
        client = get_client(platform, config)
        platform_id = client.post_with_retry(content)
        _echo_success(f"Published on {platform}. Platform ID: {platform_id}")
    except Exception as exc:
        _echo_error(f"Failed to publish: {exc}")
        sys.exit(1)


@post_group.command("list")
@click.option("--platform", type=click.Choice(PLATFORMS + ["all"]), default="all")
@click.option(
    "--status",
    type=click.Choice([s.value for s in PostStatus] + ["all"]),
    default="all",
)
@click.option("--limit", default=20, show_default=True)
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
def post_list(platform, status, limit, as_json):
    """List scheduled and published posts."""
    db = _get_db()
    posts = db.list_posts(
        platform=None if platform == "all" else platform,
        status=None if status == "all" else status,
        limit=limit,
    )

    if as_json:
        data = [
            {
                "id": p.id,
                "platform": p.platform,
                "status": p.status,
                "scheduled_at": p.scheduled_at.isoformat() if p.scheduled_at else None,
                "published_at": p.published_at.isoformat() if p.published_at else None,
                "content": p.content,
                "platform_id": p.platform_id,
                "error_message": p.error_message,
                "retry_count": p.retry_count,
            }
            for p in posts
        ]
        click.echo(json.dumps(data, indent=2))
        return

    if not posts:
        _echo_info("No posts found.")
        return
    click.echo(_format_posts_table(posts))


@post_group.command("show")
@click.argument("post_id", type=int)
def post_show(post_id):
    """Show full details for a post."""
    db = _get_db()
    post = db.get_post(post_id)
    if not post:
        _echo_error(f"Post #{post_id} not found.")
        sys.exit(1)

    rows = [
        ["ID", post.id],
        ["Platform", post.platform],
        ["Status", post.status],
        ["Scheduled At", post.scheduled_at],
        ["Published At", post.published_at or "-"],
        ["Platform ID", post.platform_id or "-"],
        ["Retry Count", post.retry_count],
        ["Error", post.error_message or "-"],
        ["Created At", post.created_at],
        ["Content", post.content],
    ]
    click.echo(tabulate(rows, tablefmt="rounded_outline"))


@post_group.command("cancel")
@click.argument("post_id", type=int)
@click.confirmation_option(prompt="Cancel this post?")
def post_cancel(post_id):
    """Cancel a pending post."""
    db = _get_db()
    post = db.get_post(post_id)
    if not post:
        _echo_error(f"Post #{post_id} not found.")
        sys.exit(1)
    if post.status != PostStatus.PENDING:
        _echo_error(f"Post #{post_id} is {post.status}, not pending — cannot cancel.")
        sys.exit(1)
    db.update_post_status(post_id, PostStatus.CANCELLED)
    _echo_success(f"Post #{post_id} cancelled.")


@post_group.command("delete")
@click.argument("post_id", type=int)
@click.confirmation_option(prompt="Permanently delete this post?")
def post_delete(post_id):
    """Permanently delete a post record."""
    db = _get_db()
    if db.delete_post(post_id):
        _echo_success(f"Post #{post_id} deleted.")
    else:
        _echo_error(f"Post #{post_id} not found.")
        sys.exit(1)


# ── generate group ────────────────────────────────────────────────────────

@cli.group("generate")
def generate_group():
    """Generate content using the Claude AI."""


@generate_group.command("content")
@click.argument("platform", type=click.Choice(PLATFORMS))
@click.option("--topic", "-t", required=True, help="Topic or subject for the post.")
@click.option("--tone", type=click.Choice(TONES), default="professional", show_default=True)
@click.option("--context", "-x", default=None, help="Optional extra context for Claude.")
@click.option("--variants", "-n", default=1, type=click.IntRange(1, 5), show_default=True)
@click.option("--save", is_flag=True, help="Save generated content to the database.")
@click.option(
    "--schedule-at",
    default=None,
    help="Immediately schedule the first variant at this datetime.",
)
def generate_content(platform, topic, tone, context, variants, save, schedule_at):
    """Generate AI-written post content for a platform."""
    config = load_config()
    try:
        generator = ContentGenerator(config.claude)
    except ValueError as exc:
        _echo_error(str(exc))
        sys.exit(1)

    _echo_info(f"Generating {variants} variant(s) for {platform} on topic: {topic!r} …")

    try:
        results = generator.generate(
            GenerationRequest(
                topic=topic,
                platform=platform,
                tone=tone,
                additional_context=context,
                num_variants=variants,
            )
        )
    except Exception as exc:
        _echo_error(f"Content generation failed: {exc}")
        sys.exit(1)

    db = _get_db() if save or schedule_at else None

    for i, gc in enumerate(results, 1):
        click.echo(f"\n{'─' * 60}")
        click.echo(click.style(f"Variant {i}/{len(results)}", bold=True))
        click.echo(f"{'─' * 60}")
        click.echo(gc.content)
        char_count = len(gc.content)
        click.echo(click.style(f"\n[{char_count} characters]", dim=True))

        if db:
            saved_gc = db.save_generated_content(gc)
            _echo_info(f"Saved as generated content #{saved_gc.id}.")

            if schedule_at and i == 1:
                try:
                    sched_dt = _parse_datetime(schedule_at)
                    post = db.create_post(Post(
                        id=None,
                        platform=platform,
                        content=gc.content,
                        scheduled_at=sched_dt,
                    ))
                    db.mark_content_used(saved_gc.id)
                    _echo_success(
                        f"Variant 1 scheduled as post #{post.id} "
                        f"at {sched_dt.strftime('%Y-%m-%d %H:%M')}."
                    )
                except Exception as exc:
                    _echo_error(f"Could not schedule post: {exc}")


@generate_group.command("improve")
@click.argument("post_id", type=int)
@click.option("--feedback", "-f", required=True, help="Feedback / instructions for improvement.")
@click.option("--apply", is_flag=True, help="Update the post in the DB with the improved content.")
def generate_improve(post_id, feedback, apply):
    """Use Claude to improve an existing post based on feedback."""
    config = load_config()
    db = _get_db()

    post = db.get_post(post_id)
    if not post:
        _echo_error(f"Post #{post_id} not found.")
        sys.exit(1)

    try:
        generator = ContentGenerator(config.claude)
        improved = generator.improve_post(post.content, post.platform, feedback)
    except Exception as exc:
        _echo_error(f"Improvement failed: {exc}")
        sys.exit(1)

    click.echo(f"\n{'─' * 60}")
    click.echo(click.style("Improved content:", bold=True))
    click.echo(f"{'─' * 60}")
    click.echo(improved)
    click.echo(click.style(f"\n[{len(improved)} characters]", dim=True))

    if apply:
        if post.status != PostStatus.PENDING:
            _echo_error(f"Post #{post_id} is {post.status} — can only update pending posts.")
            sys.exit(1)
        # Direct DB update via a small ad-hoc query
        with db.transaction() as conn:
            conn.execute(
                "UPDATE posts SET content = ?, updated_at = datetime('now') WHERE id = ?",
                (improved, post_id),
            )
        _echo_success(f"Post #{post_id} updated with improved content.")


@generate_group.command("list")
@click.option("--platform", type=click.Choice(PLATFORMS + ["all"]), default="all")
@click.option("--unused-only", is_flag=True)
def generate_list(platform, unused_only):
    """List previously generated content drafts."""
    db = _get_db()
    items = db.list_generated_content(
        platform=None if platform == "all" else platform,
        unused_only=unused_only,
    )
    if not items:
        _echo_info("No generated content found.")
        return

    rows = [
        [
            gc.id,
            gc.platform,
            gc.tone,
            "yes" if gc.used else "no",
            gc.topic[:40],
            (gc.content[:60] + "…") if len(gc.content) > 60 else gc.content,
        ]
        for gc in items
    ]
    click.echo(
        tabulate(rows, headers=["ID", "Platform", "Tone", "Used", "Topic", "Preview"], tablefmt="rounded_outline")
    )


# ── scheduler group ───────────────────────────────────────────────────────

@cli.group("scheduler")
def scheduler_group():
    """Control the background post scheduler."""


@scheduler_group.command("start")
def scheduler_start():
    """Start the scheduler (runs in the foreground; use a process manager for daemons)."""
    config = load_config()
    db = Database(config.db_path)
    scheduler = Scheduler(config, db)
    click.echo(
        click.style(
            f"Starting scheduler (interval={config.scheduler_interval_seconds}s). "
            "Press Ctrl+C to stop.",
            fg="yellow",
        )
    )
    scheduler.run_forever()


@scheduler_group.command("run-once")
def scheduler_run_once():
    """Immediately publish all posts that are due right now."""
    config = load_config()
    db = Database(config.db_path)
    scheduler = Scheduler(config, db)
    published = scheduler.tick()
    _echo_success(f"Published {published} post(s).")
