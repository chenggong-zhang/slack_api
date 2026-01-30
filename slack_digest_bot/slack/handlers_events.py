from __future__ import annotations

import logging
from typing import Any, Dict

from slack_bolt import App

from slack_digest_bot.storage.db import session_scope
from slack_digest_bot.storage.repo import Repository

log = logging.getLogger(__name__)


def _extract_team_id(body: Dict[str, Any]) -> str:
    team_id = body.get("team_id") or body.get("team")
    if not team_id and "team" in body.get("authorizations", [{}])[0]:
        team_id = body["authorizations"][0].get("team_id")
    return team_id


def register_message_handlers(app: App) -> None:
    @app.event("message")
    def handle_message_events(body: Dict[str, Any], ack, logger, event):
        if event.get("channel_type") == "im":
            # DM messages are handled by the DM router; avoid double-ack
            return
        ack()
        team_id = _extract_team_id(body)
        if not team_id:
            logger.warning("No team_id in event; skipping")
            return

        channel_id = event.get("channel")
        if not channel_id:
            return

        subtype = event.get("subtype")
        if event.get("bot_id"):
            return

        with session_scope() as session:
            repo = Repository(session)
            tracked_channels = repo.tracked_channels_for_team(team_id)
            if channel_id not in tracked_channels:
                return

            if subtype == "message_deleted":
                deleted_ts = event.get("deleted_ts") or event.get("previous_message", {}).get("ts")
                if deleted_ts:
                    repo.mark_message_deleted(team_id, channel_id, deleted_ts)
                return

            if subtype == "message_changed":
                message = event.get("message", {})
                repo.upsert_message(
                    team_id=team_id,
                    channel_id=channel_id,
                    slack_ts=message.get("ts"),
                    user_id=message.get("user"),
                    text=message.get("text", ""),
                    thread_ts=message.get("thread_ts"),
                    subtype=message.get("subtype"),
                    raw_json=message,
                )
                return

            repo.upsert_message(
                team_id=team_id,
                channel_id=channel_id,
                slack_ts=event.get("ts"),
                user_id=event.get("user"),
                text=event.get("text", ""),
                thread_ts=event.get("thread_ts"),
                subtype=subtype,
                raw_json=event,
            )
