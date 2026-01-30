from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional

from openai import OpenAI

from slack_digest_bot.app.settings import get_settings
from slack_digest_bot.digest.preprocess import PreprocessResult
from slack_digest_bot.nl.prompts import DIGEST_SYSTEM_PROMPT
from slack_digest_bot.storage.models import Message

log = logging.getLogger(__name__)

settings = get_settings()
openai_client = OpenAI(api_key=settings.openai_api_key.get_secret_value())


def _serialize_message(msg: Message) -> Dict:
    return {
        "channel_id": msg.channel_id,
        "ts": msg.slack_ts,
        "author": msg.user_id,
        "text": msg.text,
        "thread_ts": msg.thread_ts,
    }


def generate_digest(
    *,
    user_id: str,
    preprocessed: PreprocessResult,
    messages: Iterable[Message],
    timezone: Optional[str] = None,
) -> Dict:
    """Call OpenAI to produce structured digest JSON."""
    messages_payload = [_serialize_message(m) for m in messages]
    payload = {
        "timezone": timezone,
        "messages": messages_payload,
        "mentions_me": [_serialize_message(m) for m in preprocessed.mentions_me],
        "broadcasts": [_serialize_message(m) for m in preprocessed.broadcasts],
        "unanswered_questions": [_serialize_message(m) for m in preprocessed.unanswered_questions],
        "instructions": "Return JSON with overview, mentions_me, broadcasts, unanswered_questions, suggested_actions.",
    }

    response = openai_client.chat.completions.create(
        model=settings.openai_model_digest,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": DIGEST_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Build a daily Slack digest for the requesting user. "
                    "Only use the provided payload JSON."
                ),
            },
            {"role": "user", "content": str(payload)},
        ],
        temperature=0.2,
    )

    raw_content = response.choices[0].message.content or "{}"
    try:
        import json

        digest_json = json.loads(raw_content)
    except Exception:
        log.exception("Failed to parse digest JSON; returning fallback")
        digest_json = {
            "overview": "Summary unavailable.",
            "mentions_me": [],
            "broadcasts": [],
            "unanswered_questions": [],
            "suggested_actions": [],
        }
    return digest_json
