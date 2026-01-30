import datetime as dt

from slack_digest_bot.digest.preprocess import preprocess_messages
from slack_digest_bot.storage.models import Message


def make_msg(text: str, ts: str, channel="C123", user="U1", thread_ts=None):
    return Message(
        team_id="T1",
        channel_id=channel,
        slack_ts=ts,
        user_id=user,
        text=text,
        thread_ts=thread_ts,
    )


def test_detects_mentions_broadcasts_and_questions():
    messages = [
        make_msg("Hello <@U1>", "1.0"),
        make_msg("<!here> deployment now", "2.0"),
        make_msg("Can someone review?", "3.0"),
    ]
    result = preprocess_messages(messages, user_id="U1")
    assert len(result.mentions_me) == 1
    assert len(result.broadcasts) == 1
    assert len(result.question_candidates) == 1


def test_unanswered_questions_in_threads_and_channels():
    # Thread starter with no replies -> unanswered
    t1 = make_msg("Question one?", "10.0", thread_ts="10.0")
    # Non-thread message with quick follow-up reply within 5 minutes -> answered
    q2 = make_msg("Any update?", "20.0")
    reply = make_msg("Yes here", "20.1")
    result = preprocess_messages([t1, q2, reply], user_id="U1")
    unanswered_ts = {m.slack_ts for m in result.unanswered_questions}
    assert "10.0" in unanswered_ts
    assert "20.0" not in unanswered_ts
