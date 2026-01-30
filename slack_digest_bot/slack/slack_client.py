from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)


log = logging.getLogger(__name__)


class SlackClient:
    """Thin wrapper around Slack WebClient with retry logic."""

    def __init__(self, bot_token: str):
        self.client = WebClient(token=bot_token)

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential_jitter(initial=1, max=6),
        retry=retry_if_exception_type(SlackApiError),
    )
    def call(self, method: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            return self.client.api_call(method, json=kwargs)
        except SlackApiError:
            log.exception("Slack API call failed: %s", method)
            raise

    def open_dm(self, user_id: str) -> str:
        resp = self.call("conversations.open", users=user_id)
        return resp["channel"]["id"]

    def post_message(self, channel: str, text: str, blocks: Optional[list] = None) -> None:
        payload: Dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        self.call("chat.postMessage", **payload)

    def resolve_channel_id(self, name_or_id: str) -> Optional[str]:
        """Resolve '#name' to channel ID; return input if already looks like an ID."""
        if name_or_id.startswith("C") and len(name_or_id) >= 8:
            return name_or_id
        target = name_or_id.lstrip("#")
        cursor = None
        while True:
            resp = self.call(
                "conversations.list",
                exclude_archived=True,
                types="public_channel,private_channel",
                limit=200,
                cursor=cursor,
            )
            for ch in resp.get("channels", []):
                if ch.get("name") == target:
                    return ch.get("id")
            cursor = resp.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        return None
