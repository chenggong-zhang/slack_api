from __future__ import annotations

import logging
from typing import Dict

from slack_digest_bot.digest.renderer import render_digest_blocks
from slack_digest_bot.slack.slack_client import SlackClient

log = logging.getLogger(__name__)


def deliver_digest(slack_client: SlackClient, user_id: str, digest_json: Dict) -> None:
    text, blocks = render_digest_blocks(digest_json)
    dm_channel = slack_client.open_dm(user_id)
    slack_client.post_message(dm_channel, text=text, blocks=blocks)
