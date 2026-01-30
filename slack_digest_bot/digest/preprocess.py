from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List

from slack_digest_bot.storage.models import Message

BROADCAST_TOKENS = {"<!here>", "<!channel>", "<!everyone>"}
QUESTION_PREFIX = re.compile(r"^(who|what|when|where|why|how|can someone)", re.IGNORECASE)


@dataclass
class PreprocessResult:
    mentions_me: List[Message]
    broadcasts: List[Message]
    question_candidates: List[Message]
    unanswered_questions: List[Message]


def contains_mention(text: str, user_id: str) -> bool:
    return f"<@{user_id}>" in text


def is_broadcast(text: str) -> bool:
    return any(token in text for token in BROADCAST_TOKENS)


def is_question_candidate(text: str) -> bool:
    normalized = text.strip()
    if "?" in normalized:
        return True
    return bool(QUESTION_PREFIX.match(normalized))


def detect_unanswered(all_messages: List[Message], question_candidates: List[Message]) -> List[Message]:
    unanswered: List[Message] = []
    messages_by_thread: Dict[str, List[Message]] = {}
    for msg in all_messages:
        if msg.thread_ts:
            messages_by_thread.setdefault(msg.thread_ts, []).append(msg)

    # Threaded messages: unanswered if starter is a question with no replies
    for thread_ts, msgs in messages_by_thread.items():
        ordered = sorted(msgs, key=lambda m: m.slack_ts)
        starter = ordered[0]
        if starter not in question_candidates:
            continue
        if len(ordered) == 1:
            unanswered.append(starter)

    # Non-threaded: simple window heuristic using all messages
    channel_buckets: Dict[str, List[Message]] = {}
    for msg in all_messages:
        if not msg.thread_ts:
            channel_buckets.setdefault(msg.channel_id, []).append(msg)
    for msgs in channel_buckets.values():
        ordered = sorted(msgs, key=lambda m: m.slack_ts)
        for idx, msg in enumerate(ordered):
            if msg not in question_candidates:
                continue
            window = ordered[idx + 1 : idx + 6]  # next few messages
            if not window:
                unanswered.append(msg)
                continue
            current_time = dt.datetime.fromtimestamp(float(msg.slack_ts))
            replied = False
            for nxt in window:
                next_time = dt.datetime.fromtimestamp(float(nxt.slack_ts))
                if (next_time - current_time) <= dt.timedelta(minutes=20):
                    replied = True
                    break
            if not replied:
                unanswered.append(msg)
    return unanswered


def preprocess_messages(messages: Iterable[Message], user_id: str) -> PreprocessResult:
    messages_list = list(messages)
    mentions = [m for m in messages_list if contains_mention(m.text, user_id)]
    broadcasts = [m for m in messages_list if is_broadcast(m.text)]
    question_candidates = [m for m in messages_list if is_question_candidate(m.text)]
    unanswered = detect_unanswered(messages_list, question_candidates)
    return PreprocessResult(
        mentions_me=mentions,
        broadcasts=broadcasts,
        question_candidates=question_candidates,
        unanswered_questions=unanswered,
    )
