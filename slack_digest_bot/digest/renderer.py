from __future__ import annotations

from typing import Dict, List, Tuple


def _format_items(items: List[Dict], title: str) -> List[Dict]:
    if not items:
        return [{"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*\n_None_"}}]
    blocks: List[Dict] = [{"type": "section", "text": {"type": "mrkdwn", "text": f"*{title}*"}}]
    for item in items:
        text = item.get("text") or item.get("question_text") or item.get("action")
        channel = item.get("channel") or item.get("channel_id")
        author = item.get("author")
        ts = item.get("ts")
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"- {text} (_{channel}_ by {author} at {ts})",
                },
            }
        )
    return blocks


def render_digest_blocks(digest_json: Dict) -> Tuple[str, List[Dict]]:
    overview = digest_json.get("overview", "")
    mentions = digest_json.get("mentions_me", [])
    broadcasts = digest_json.get("broadcasts", [])
    unanswered = digest_json.get("unanswered_questions", [])
    actions = digest_json.get("suggested_actions", [])

    blocks: List[Dict] = []
    if overview:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*Overview*\n{overview}"}})
    blocks += _format_items(mentions, "Mentions")
    blocks += _format_items(broadcasts, "Broadcasts")
    blocks += _format_items(unanswered, "Unanswered Questions")

    if actions:
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": "*Suggested Actions*"}})
        for action in actions:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"- ({action.get('priority','med')}) {action.get('action')} — {action.get('rationale','')}",
                    },
                }
            )
    else:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Suggested Actions*\n_None_"},
            }
        )

    plain_text = "Daily digest ready."
    return plain_text, blocks
