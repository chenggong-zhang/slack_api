from __future__ import annotations

import datetime as dt
import logging
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from slack_digest_bot.app.settings import get_settings
from slack_digest_bot.digest.delivery import deliver_digest
from slack_digest_bot.digest.llm_digest import generate_digest
from slack_digest_bot.digest.preprocess import preprocess_messages
from slack_digest_bot.slack.slack_client import SlackClient
from slack_digest_bot.storage.db import session_scope
from slack_digest_bot.storage.repo import Repository

log = logging.getLogger(__name__)
settings = get_settings()


class DigestScheduler:
    def __init__(self, slack_client: SlackClient):
        self.scheduler = BackgroundScheduler(timezone="UTC")
        self.slack_client = slack_client

    def start(self) -> None:
        self.scheduler.start()
        self._schedule_retention_job()

    def schedule_user(self, team_id: str, user_id: str, timezone: str, time_local: str) -> None:
        hour, minute = map(int, time_local.split(":"))
        tz = ZoneInfo(timezone) if timezone else dt.timezone.utc
        trigger = CronTrigger(hour=hour, minute=minute, timezone=tz)
        job_id = f"digest-{team_id}-{user_id}"
        self.scheduler.add_job(
            self._run_digest_job,
            id=job_id,
            trigger=trigger,
            replace_existing=True,
            args=[team_id, user_id],
        )
        log.info("Scheduled digest for %s at %s %s", user_id, time_local, timezone or "UTC")

    def _run_digest_job(self, team_id: str, user_id: str) -> None:
        with session_scope() as session:
            repo = Repository(session)
            user = repo.get_user_with_prefs(team_id, user_id)
            if not user:
                return

            now = dt.datetime.now(dt.timezone.utc)
            since = user.last_digest_sent_at or now - dt.timedelta(days=1)
            messages = repo.fetch_messages_for_user(team_id, user_id, since=since, until=now)

            preprocessed = preprocess_messages(messages, user_id)
            digest_json = generate_digest(
                user_id=user_id, preprocessed=preprocessed, messages=messages, timezone=user.timezone
            )
            deliver_digest(self.slack_client, user_id, digest_json)
            user.last_digest_sent_at = now

    def bootstrap_from_db(self) -> None:
        from sqlalchemy import select
        from slack_digest_bot.storage.models import User

        with session_scope() as session:
            repo = Repository(session)
            results = session.execute(select(User)).scalars().all()
            for user in results:
                prefs = repo._ensure_prefs(user)
                tz = user.timezone or "UTC"
                self.schedule_user(user.team_id, user.user_id, tz, user.digest_time_local)

    def _schedule_retention_job(self) -> None:
        cutoff_days = settings.message_retention_days
        self.scheduler.add_job(
            self._run_retention,
            trigger=CronTrigger(hour=3, minute=0, timezone=dt.timezone.utc),
            replace_existing=True,
        )
        log.info("Retention job scheduled; pruning messages older than %s days", cutoff_days)

    def _run_retention(self) -> None:
        cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=settings.message_retention_days)
        with session_scope() as session:
            repo = Repository(session)
            deleted = repo.cleanup_old_messages(before=cutoff)
            log.info("Retention cleanup removed %s messages", deleted)
