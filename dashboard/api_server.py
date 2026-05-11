"""
Flask API server that bridges the static dashboard to the Python backend.

Usage:
    pip install flask flask-cors
    python dashboard/api_server.py          # http://localhost:8080

The dashboard auto-detects this server via GET /api/ping.
When offline it falls back to localStorage-backed mock data.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Make the parent package importable when running from the repo root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from social_media_automation.config import load_config, save_config
from social_media_automation.content.generator import ContentGenerator, GenerationRequest
from social_media_automation.platforms.base import PlatformError
from social_media_automation.platforms.factory import get_client
from social_media_automation.scheduler.runner import Scheduler
from social_media_automation.storage.models import Database, Post, PostStatus

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app, origins=["*"])  # restrict in production

# ── Helpers ────────────────────────────────────────────────────────────────

def _db() -> Database:
    return Database(load_config().db_path)


def _post_to_dict(p: Post) -> dict:
    return {
        "id":            p.id,
        "platform":      p.platform,
        "content":       p.content,
        "status":        p.status,
        "scheduled_at":  p.scheduled_at.isoformat() if p.scheduled_at else None,
        "published_at":  p.published_at.isoformat() if p.published_at else None,
        "platform_id":   p.platform_id,
        "error_message": p.error_message,
        "retry_count":   p.retry_count,
        "created_at":    p.created_at.isoformat() if p.created_at else None,
    }


def _err(msg: str, code: int = 400):
    return jsonify({"error": msg}), code


# ── Static files ───────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# ── Connectivity probe ─────────────────────────────────────────────────────

@app.route("/api/ping")
def ping():
    return jsonify({"ok": True})


# ── Stats ──────────────────────────────────────────────────────────────────

@app.route("/api/stats")
def stats():
    db    = _db()
    posts = db.list_posts(limit=10_000)
    count = lambda s: sum(1 for p in posts if p.status == s)
    pending = sorted(
        [p for p in posts if p.status == PostStatus.PENDING],
        key=lambda p: p.scheduled_at or datetime.max,
    )
    return jsonify({
        "total":     len(posts),
        "pending":   count(PostStatus.PENDING),
        "published": count(PostStatus.PUBLISHED),
        "failed":    count(PostStatus.FAILED),
        "cancelled": count(PostStatus.CANCELLED),
        "next_due":  pending[0].scheduled_at.isoformat() if pending else None,
    })


# ── Posts ──────────────────────────────────────────────────────────────────

@app.route("/api/posts", methods=["GET"])
def list_posts():
    platform = request.args.get("platform") or None
    status   = request.args.get("status")   or None
    limit    = min(int(request.args.get("limit", 100)), 500)
    posts    = _db().list_posts(platform=platform, status=status, limit=limit)
    return jsonify([_post_to_dict(p) for p in posts])


@app.route("/api/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    post = _db().get_post(post_id)
    if not post:
        return _err(f"Post #{post_id} not found", 404)
    return jsonify(_post_to_dict(post))


@app.route("/api/posts", methods=["POST"])
def create_post():
    data = request.get_json() or {}
    platform     = data.get("platform", "").strip()
    content      = data.get("content", "").strip()
    scheduled_at = data.get("scheduled_at", "").strip()

    if platform not in ("twitter", "linkedin"):
        return _err("platform must be 'twitter' or 'linkedin'")
    if not content:
        return _err("content is required")
    if not scheduled_at:
        return _err("scheduled_at is required")

    try:
        sched_dt = datetime.fromisoformat(scheduled_at)
    except ValueError:
        return _err("Invalid scheduled_at format. Use ISO-8601.")

    post = _db().create_post(Post(
        id=None, platform=platform, content=content, scheduled_at=sched_dt,
    ))
    return jsonify(_post_to_dict(post)), 201


@app.route("/api/posts/<int:post_id>/cancel", methods=["POST"])
def cancel_post(post_id):
    db   = _db()
    post = db.get_post(post_id)
    if not post:
        return _err(f"Post #{post_id} not found", 404)
    if post.status != PostStatus.PENDING:
        return _err(f"Post #{post_id} is {post.status}, cannot cancel")
    db.update_post_status(post_id, PostStatus.CANCELLED)
    return jsonify(_post_to_dict(db.get_post(post_id)))


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    if not _db().delete_post(post_id):
        return _err(f"Post #{post_id} not found", 404)
    return jsonify({"ok": True})


# ── Publish now ────────────────────────────────────────────────────────────

@app.route("/api/publish-now", methods=["POST"])
def publish_now():
    data     = request.get_json() or {}
    platform = data.get("platform", "").strip()
    content  = data.get("content", "").strip()

    if not platform or not content:
        return _err("platform and content are required")

    config = load_config()
    try:
        client      = get_client(platform, config)
        platform_id = client.post_with_retry(content)
        return jsonify({"ok": True, "platform_id": platform_id})
    except PlatformError as e:
        return _err(str(e), 422)
    except Exception as e:
        return _err(str(e), 500)


# ── Scheduler ──────────────────────────────────────────────────────────────

@app.route("/api/scheduler/run-once", methods=["POST"])
def scheduler_run_once():
    config    = load_config()
    db        = _db()
    scheduler = Scheduler(config, db)
    published = scheduler.tick()
    return jsonify({"ok": True, "published": published})


# ── Generated content ──────────────────────────────────────────────────────

@app.route("/api/generated", methods=["GET"])
def list_generated():
    platform    = request.args.get("platform") or None
    unused_only = request.args.get("unused_only") == "1"
    db          = _db()
    items       = db.list_generated_content(platform=platform, unused_only=unused_only)
    return jsonify([{
        "id":         g.id,
        "topic":      g.topic,
        "platform":   g.platform,
        "tone":       g.tone,
        "content":    g.content,
        "used":       g.used,
        "created_at": g.created_at.isoformat() if g.created_at else None,
    } for g in items])


@app.route("/api/generate", methods=["POST"])
def generate():
    data     = request.get_json() or {}
    platform = data.get("platform", "twitter")
    topic    = (data.get("topic") or "").strip()
    tone     = data.get("tone", "professional")
    context  = data.get("context", "")
    variants = int(data.get("variants", 1))

    if not topic:
        return _err("topic is required")

    config = load_config()
    if not config.claude.api_key:
        return _err("Claude API key not configured. Add ANTHROPIC_API_KEY.", 422)

    try:
        generator = ContentGenerator(config.claude)
        results   = generator.generate(GenerationRequest(
            topic=topic, platform=platform, tone=tone,
            additional_context=context or None, num_variants=variants,
        ))
    except Exception as e:
        return _err(str(e), 500)

    db    = _db()
    saved = [db.save_generated_content(gc) for gc in results]
    return jsonify([{
        "id":       g.id,
        "topic":    g.topic,
        "platform": g.platform,
        "tone":     g.tone,
        "content":  g.content,
        "used":     g.used,
    } for g in saved])


@app.route("/api/generated/schedule", methods=["POST"])
def schedule_from_generated():
    data         = request.get_json() or {}
    gc_id        = data.get("id")
    scheduled_at = data.get("scheduled_at", "").strip()

    if not gc_id or not scheduled_at:
        return _err("id and scheduled_at are required")

    try:
        sched_dt = datetime.fromisoformat(scheduled_at)
    except ValueError:
        return _err("Invalid scheduled_at format.")

    db   = _db()
    items = db.list_generated_content()
    item  = next((g for g in items if g.id == gc_id), None)
    if not item:
        return _err("Generated content not found", 404)

    db.mark_content_used(gc_id)
    post = db.create_post(Post(
        id=None, platform=item.platform, content=item.content, scheduled_at=sched_dt,
    ))
    return jsonify(_post_to_dict(post)), 201


# ── Config ─────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def get_config():
    cfg = load_config()

    def mask(v: str) -> str:
        if not v: return ""
        return v[:3] + "****" if len(v) > 3 else "****"

    return jsonify({
        "twitter": {
            "api_key":              mask(cfg.twitter.api_key),
            "api_secret":           mask(cfg.twitter.api_secret),
            "access_token":         mask(cfg.twitter.access_token),
            "access_token_secret":  mask(cfg.twitter.access_token_secret),
            "bearer_token":         mask(cfg.twitter.bearer_token),
        },
        "linkedin": {
            "client_id":     mask(cfg.linkedin.client_id),
            "client_secret": mask(cfg.linkedin.client_secret),
            "access_token":  mask(cfg.linkedin.access_token),
            "person_urn":    cfg.linkedin.person_urn,
        },
        "claude": {
            "api_key":    mask(cfg.claude.api_key),
            "model":      cfg.claude.model,
            "max_tokens": cfg.claude.max_tokens,
        },
        "db_path":            cfg.db_path,
        "scheduler_interval": cfg.scheduler_interval_seconds,
    })


@app.route("/api/config", methods=["POST"])
def save_config_endpoint():
    data   = request.get_json() or {}
    config = load_config()

    tw = data.get("twitter", {})
    li = data.get("linkedin", {})
    cl = data.get("claude", {})

    # Only overwrite fields that were explicitly provided (non-empty)
    def _set(current, new): return new if new else current

    config.twitter.api_key             = _set(config.twitter.api_key,             tw.get("api_key", ""))
    config.twitter.api_secret          = _set(config.twitter.api_secret,          tw.get("api_secret", ""))
    config.twitter.access_token        = _set(config.twitter.access_token,        tw.get("access_token", ""))
    config.twitter.access_token_secret = _set(config.twitter.access_token_secret, tw.get("access_token_secret", ""))
    config.twitter.bearer_token        = _set(config.twitter.bearer_token,        tw.get("bearer_token", ""))

    config.linkedin.client_id     = _set(config.linkedin.client_id,     li.get("client_id", ""))
    config.linkedin.client_secret = _set(config.linkedin.client_secret, li.get("client_secret", ""))
    config.linkedin.access_token  = _set(config.linkedin.access_token,  li.get("access_token", ""))
    config.linkedin.person_urn    = _set(config.linkedin.person_urn,    li.get("person_urn", ""))

    config.claude.api_key    = _set(config.claude.api_key, cl.get("api_key", ""))
    config.claude.model      = cl.get("model") or config.claude.model
    config.claude.max_tokens = int(cl.get("max_tokens") or config.claude.max_tokens)

    if data.get("db_path"):            config.db_path = data["db_path"]
    if data.get("scheduler_interval"): config.scheduler_interval_seconds = int(data["scheduler_interval"])

    save_config(config)
    return jsonify({"ok": True})


@app.route("/api/config/verify/<platform>", methods=["POST"])
def verify_config(platform):
    if platform not in ("twitter", "linkedin"):
        return _err("Unknown platform")
    config = load_config()
    try:
        client = get_client(platform, config)
        ok     = client.verify_credentials()
        return jsonify({"ok": ok, "message": "" if ok else "Credentials invalid or API unreachable."})
    except PlatformError as e:
        return jsonify({"ok": False, "message": str(e)})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})


# ── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"\n  Social Media Automation Dashboard")
    print(f"  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("DEBUG") == "1")
