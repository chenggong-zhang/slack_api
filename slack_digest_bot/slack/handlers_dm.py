from __future__ import annotations

import logging
from typing import Any, Dict

from slack_bolt import App

from slack_digest_bot.nl.router import handle_dm_message
from slack_digest_bot.slack.slack_client import SlackClient

log = logging.getLogger(__name__)


def register_dm_handlers(app: App, slack_client: SlackClient) -> None:
    @app.event("message")
    def handle_dm(body: Dict[str, Any], event, ack, logger):
        # Filter for direct messages only
        channel_type = event.get("channel_type")
        if channel_type != "im":
            return
        ack()

        team_id = body.get("team") or event.get("team")
        user_id = event.get("user")
        text = event.get("text", "")
        if not (team_id and user_id and text):
            return

        try:
            response_text = handle_dm_message(team_id, user_id, text, slack_client)
            dm_channel = event.get("channel") or slack_client.open_dm(user_id)
            slack_client.post_message(dm_channel, response_text)
        except Exception:
            logger.exception("Failed to process DM")
            slack_client.post_message(
                event.get("channel") or slack_client.open_dm(user_id),
                "Sorry, I hit a snag while updating your settings.",
            )
