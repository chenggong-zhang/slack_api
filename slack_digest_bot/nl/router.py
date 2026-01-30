from __future__ import annotations

import json
import logging
from typing import Dict, List, Tuple

from openai import OpenAI

from slack_digest_bot.app.settings import get_settings
from slack_digest_bot.nl.prompts import DM_SYSTEM_PROMPT
from slack_digest_bot.nl.tool_schemas import tool_definitions
from slack_digest_bot.slack.slack_client import SlackClient
from slack_digest_bot.storage.db import session_scope
from slack_digest_bot.storage.repo import Repository

log = logging.getLogger(__name__)

settings = get_settings()
openai_client = OpenAI(api_key=settings.openai_api_key.get_secret_value())


def resolve_channels(
    slack_client: SlackClient, channels: List[str]
) -> Tuple[List[str], List[str]]:
    resolved, failed = [], []
    for ch in channels:
        cid = slack_client.resolve_channel_id(ch)
        if cid:
            resolved.append(cid)
        else:
            failed.append(ch)
    return resolved, failed


def format_configuration(repo: Repository, team_id: str, user_id: str) -> str:
    user = repo.get_user_with_prefs(team_id, user_id)
    if not user:
        return "No configuration found."
    prefs = repo._ensure_prefs(user)
    enabled_channels = [sub.channel_id for sub in user.subscriptions if sub.enabled]
    lines = [
        f"Digest time: {user.digest_time_local}",
        f"Tracked channels ({len(enabled_channels)}/{prefs.max_channels}): {', '.join(enabled_channels) or 'none'}",
        f"Sections -> overview:{prefs.include_overview}, mentions:{prefs.include_mentions_me}, broadcasts:{prefs.include_broadcasts}, unanswered:{prefs.include_unanswered_questions}, actions:{prefs.include_suggested_actions}",
    ]
    if prefs.custom_rules_json:
        lines.append(f"Custom rules: {prefs.custom_rules_json}")
    return "\n".join(lines)


def handle_dm_message(team_id: str, user_id: str, text: str, slack_client: SlackClient) -> str:
    with session_scope() as session:
        repo = Repository(session)
        repo.get_or_create_user(team_id, user_id)

        completion = openai_client.chat.completions.create(
            model=settings.openai_model_nl,
            messages=[
                {"role": "system", "content": DM_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            tools=tool_definitions(),
        )

        message = completion.choices[0].message
        tool_calls = message.tool_calls or []
        logs: List[str] = []

        for call in tool_calls:
            name = call.function.name
            args = json.loads(call.function.arguments or "{}")
            if name == "add_channels":
                resolved, failed = resolve_channels(slack_client, args.get("channels", []))
                added, skipped = repo.add_channels(user=repo.get_or_create_user(team_id, user_id), channels=resolved)
                if added:
                    logs.append(f"Added: {', '.join(added)}")
                if skipped:
                    logs.append(f"Skipped (at limit or already tracked): {', '.join(skipped)}")
                if failed:
                    logs.append(f"Could not resolve: {', '.join(failed)}")
            elif name == "remove_channels":
                removed = repo.remove_channels(repo.get_or_create_user(team_id, user_id), args.get("channels", []))
                logs.append(f"Removed: {', '.join(removed) if removed else 'none'}")
            elif name == "set_max_channels":
                repo.set_max_channels(repo.get_or_create_user(team_id, user_id), args["max_channels"])
                logs.append(f"Max channels set to {args['max_channels']}")
            elif name == "set_digest_time":
                repo.set_digest_time(repo.get_or_create_user(team_id, user_id), args["time_local"])
                logs.append(f"Digest time set to {args['time_local']}")
            elif name == "set_preferences":
                repo.set_preferences(repo.get_or_create_user(team_id, user_id), **args)
                logs.append("Preferences updated")
            elif name == "list_configuration":
                logs.append("Current configuration requested.")
            else:
                log.warning("Unhandled tool call: %s", name)

        config_summary = format_configuration(repo, team_id, user_id)

    if tool_calls:
        prefix = "Updated your settings:\n" if logs else "Configuration unchanged.\n"
    else:
        prefix = "Here's what I'm tracking:\n"

    return prefix + "\n".join(logs) + ("\n\n" if logs else "\n") + config_summary
