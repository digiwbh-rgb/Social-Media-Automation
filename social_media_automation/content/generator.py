"""Claude API integration for AI-powered social media content generation."""

import logging
from dataclasses import dataclass
from typing import Optional

import anthropic

from ..config import ClaudeConfig
from ..storage.models import GeneratedContent

logger = logging.getLogger(__name__)

PLATFORM_CONSTRAINTS = {
    "twitter": (
        "280 characters max. Be punchy and engaging. "
        "Include 1-2 relevant hashtags if appropriate. "
        "No em-dashes or excessive punctuation."
    ),
    "linkedin": (
        "Professional tone. Up to 3000 characters. "
        "Can include a short hook on the first line, "
        "then a few paragraphs with insights or value. "
        "End with a call-to-action or question to drive engagement."
    ),
}

TONE_DESCRIPTIONS = {
    "professional": "formal, authoritative, and credible",
    "casual": "conversational, friendly, and approachable",
    "humorous": "witty, light-hearted, and entertaining — but still on-brand",
    "inspirational": "motivating, uplifting, and empowering",
    "educational": "informative, clear, and value-driven",
}


@dataclass
class GenerationRequest:
    topic: str
    platform: str
    tone: str = "professional"
    additional_context: Optional[str] = None
    num_variants: int = 1


class ContentGenerator:
    """Uses the Claude API to draft platform-specific social media posts."""

    def __init__(self, config: ClaudeConfig) -> None:
        if not config.api_key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Set ANTHROPIC_API_KEY or run: sma config set-claude-key <key>"
            )
        self._client = anthropic.Anthropic(api_key=config.api_key)
        self._config = config

    def generate(self, request: GenerationRequest) -> list[GeneratedContent]:
        """Return a list of GeneratedContent drafts (one per variant)."""
        platform = request.platform.lower()
        constraints = PLATFORM_CONSTRAINTS.get(
            platform, "Keep it concise and engaging."
        )
        tone_desc = TONE_DESCRIPTIONS.get(request.tone, request.tone)

        variants_instruction = (
            f"Generate {request.num_variants} distinct variant(s), "
            "separated by '---VARIANT---' on its own line."
            if request.num_variants > 1
            else "Generate exactly one post."
        )

        context_block = (
            f"\n\nAdditional context: {request.additional_context}"
            if request.additional_context
            else ""
        )

        prompt = f"""You are a social media copywriter. Create a {platform.capitalize()} post about the following topic.

Topic: {request.topic}{context_block}

Tone: {tone_desc}
Platform constraints: {constraints}
{variants_instruction}

Output only the post text(s) — no labels, no explanations, no quotation marks around the post.
"""

        logger.debug("Generating content via Claude for topic=%r platform=%s", request.topic, platform)

        message = self._client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = message.content[0].text.strip()
        splits = raw.split("---VARIANT---")

        results = []
        for variant_text in splits[: request.num_variants]:
            text = variant_text.strip()
            if text:
                results.append(
                    GeneratedContent(
                        id=None,
                        topic=request.topic,
                        platform=platform,
                        tone=request.tone,
                        content=text,
                    )
                )

        logger.info(
            "Generated %d content variant(s) for topic=%r on %s.",
            len(results), request.topic, platform,
        )
        return results

    def improve_post(self, content: str, platform: str, feedback: str) -> str:
        """Rewrite an existing post based on feedback."""
        constraints = PLATFORM_CONSTRAINTS.get(platform.lower(), "")
        prompt = f"""Improve the following {platform} post based on this feedback.

Original post:
{content}

Feedback: {feedback}
Platform constraints: {constraints}

Return only the improved post text — no labels or explanations.
"""
        message = self._client.messages.create(
            model=self._config.model,
            max_tokens=self._config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
