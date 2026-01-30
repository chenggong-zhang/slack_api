import datetime as dt

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from slack_digest_bot.storage import db
from slack_digest_bot.storage.db import Base
from slack_digest_bot.storage.models import Message
from slack_digest_bot.storage.repo import Repository


def setup_inmemory_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    return SessionLocal()


def test_fetch_messages_filters_to_tracked_channels():
    session = setup_inmemory_session()
    repo = Repository(session)
    user = repo.get_or_create_user("T1", "U1")
    repo.add_channels(user, ["C-track"])
    repo.add_channels(user, ["C-other"])  # disabled later
    repo.remove_channels(user, ["C-other"])

    now = dt.datetime.now(dt.timezone.utc)
    repo.upsert_message(
        team_id="T1",
        channel_id="C-track",
        slack_ts="1.0",
        user_id="U2",
        text="hello",
        thread_ts=None,
        subtype=None,
    )
    repo.upsert_message(
        team_id="T1",
        channel_id="C-untracked",
        slack_ts="2.0",
        user_id="U3",
        text="ignore",
        thread_ts=None,
        subtype=None,
    )

    messages = repo.fetch_messages_for_user("T1", "U1", since=now - dt.timedelta(days=1))
    assert len(messages) == 1
    assert messages[0].channel_id == "C-track"
