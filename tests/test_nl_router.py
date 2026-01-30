import json
from types import SimpleNamespace

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from slack_digest_bot.nl import router
from slack_digest_bot.storage import db
from slack_digest_bot.storage.db import Base
from slack_digest_bot.storage.repo import Repository


class FakeSlackClient:
    def resolve_channel_id(self, value: str):
        return value


def setup_inmemory_db(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    monkeypatch.setattr(db, "engine", engine)
    monkeypatch.setattr(db, "SessionLocal", SessionLocal)


def make_fake_completion():
    tool_call = SimpleNamespace(
        function=SimpleNamespace(name="add_channels", arguments=json.dumps({"channels": ["C1"]})),
    )
    message = SimpleNamespace(tool_calls=[tool_call], content=None)
    choices = [SimpleNamespace(message=message)]
    return SimpleNamespace(choices=choices)


def test_nl_router_applies_tool_calls(monkeypatch):
    setup_inmemory_db(monkeypatch)
    monkeypatch.setattr(router, "openai_client", SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **kwargs: make_fake_completion()))))

    text = router.handle_dm_message(team_id="T1", user_id="U1", text="track #general", slack_client=FakeSlackClient())
    with db.session_scope() as session:
        repo = Repository(session)
        user = repo.get_user_with_prefs("T1", "U1")
        channels = [sub.channel_id for sub in user.subscriptions if sub.enabled]
    assert "C1" in channels
    assert "Added" in text
