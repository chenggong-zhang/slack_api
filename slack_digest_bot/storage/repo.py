from __future__ import annotations

import datetime as dt
from typing import Iterable, List, Optional, Sequence, Tuple

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from slack_digest_bot.storage.models import ChannelSubscription, Message, TrackingPreferences, User


class Repository:
    """Lightweight data-access layer to keep handlers thin."""

    def __init__(self, session: Session):
        self.session = session

    # Users & preferences -------------------------------------------------
    def get_or_create_user(self, team_id: str, user_id: str, timezone: Optional[str] = None) -> User:
        user = (
            self.session.execute(
                select(User).where(and_(User.team_id == team_id, User.user_id == user_id))
            )
            .scalars()
            .first()
        )
        if user:
            if timezone and user.timezone != timezone:
                user.timezone = timezone
            return user

        user = User(team_id=team_id, user_id=user_id, timezone=timezone)
        self.session.add(user)
        self.session.flush()
        # Ensure preferences exist
        prefs = TrackingPreferences(team_id=team_id, user_id=user.id)
        self.session.add(prefs)
        self.session.flush()
        user.tracking_prefs = prefs
        return user

    def get_user_with_prefs(self, team_id: str, user_id: str) -> Optional[User]:
        return (
            self.session.execute(
                select(User)
                .options(joinedload(User.tracking_prefs), joinedload(User.subscriptions))
                .where(and_(User.team_id == team_id, User.user_id == user_id))
            )
            .scalars()
            .first()
        )

    def set_digest_time(self, user: User, time_local: str) -> None:
        user.digest_time_local = time_local

    def set_max_channels(self, user: User, max_channels: int) -> None:
        prefs = self._ensure_prefs(user)
        prefs.max_channels = max_channels

    def set_preferences(self, user: User, **kwargs) -> TrackingPreferences:
        prefs = self._ensure_prefs(user)
        for key, value in kwargs.items():
            if hasattr(prefs, key) and value is not None:
                setattr(prefs, key, value)
        return prefs

    def _ensure_prefs(self, user: User) -> TrackingPreferences:
        if not user.tracking_prefs:
            prefs = TrackingPreferences(team_id=user.team_id, user_id=user.id)
            self.session.add(prefs)
            self.session.flush()
            user.tracking_prefs = prefs
        return user.tracking_prefs

    # Channel subscriptions -----------------------------------------------
    def list_tracked_channels(self, user: User) -> List[str]:
        return [
            sub.channel_id
            for sub in user.subscriptions
            if sub.enabled
        ]

    def add_channels(self, user: User, channels: Sequence[str]) -> Tuple[List[str], List[str]]:
        prefs = self._ensure_prefs(user)
        existing_ids = {sub.channel_id for sub in user.subscriptions}
        added, skipped = [], []

        for channel in channels:
            if channel in existing_ids:
                skipped.append(channel)
                continue
            if len([s for s in user.subscriptions if s.enabled]) >= prefs.max_channels:
                skipped.append(channel)
                continue
            sub = ChannelSubscription(team_id=user.team_id, user_id=user.id, channel_id=channel)
            user.subscriptions.append(sub)
            added.append(channel)
        if added:
            self.session.flush()
        return added, skipped

    def remove_channels(self, user: User, channels: Sequence[str]) -> List[str]:
        removed: List[str] = []
        for sub in list(user.subscriptions):
            if sub.channel_id in channels and sub.enabled:
                sub.enabled = False
                removed.append(sub.channel_id)
        if removed:
            self.session.flush()
        return removed

    def tracked_channels_for_team(self, team_id: str) -> List[str]:
        result = self.session.execute(
            select(ChannelSubscription.channel_id)
            .where(and_(ChannelSubscription.team_id == team_id, ChannelSubscription.enabled.is_(True)))
            .distinct()
        )
        return [row[0] for row in result.all()]

    # Messages ------------------------------------------------------------
    def upsert_message(
        self,
        *,
        team_id: str,
        channel_id: str,
        slack_ts: str,
        user_id: Optional[str],
        text: str,
        thread_ts: Optional[str],
        subtype: Optional[str],
        raw_json: Optional[dict] = None,
        created_at: Optional[dt.datetime] = None,
    ) -> Message:
        existing = (
            self.session.execute(
                select(Message).where(
                    and_(
                        Message.team_id == team_id,
                        Message.channel_id == channel_id,
                        Message.slack_ts == slack_ts,
                    )
                )
            )
            .scalars()
            .first()
        )
        if existing:
            existing.text = text
            existing.thread_ts = thread_ts
            existing.subtype = subtype
            existing.raw_json = raw_json
            existing.is_deleted = False
            return existing

        message = Message(
            team_id=team_id,
            channel_id=channel_id,
            slack_ts=slack_ts,
            user_id=user_id,
            text=text,
            thread_ts=thread_ts,
            subtype=subtype,
            raw_json=raw_json,
            created_at=created_at or dt.datetime.now(dt.timezone.utc),
        )
        self.session.add(message)
        try:
            self.session.flush()
        except IntegrityError:
            self.session.rollback()
            # Another worker inserted; fetch it
            message = (
                self.session.execute(
                    select(Message).where(
                        and_(
                            Message.team_id == team_id,
                            Message.channel_id == channel_id,
                            Message.slack_ts == slack_ts,
                        )
                    )
                )
                .scalars()
                .one()
            )
        return message

    def mark_message_deleted(self, team_id: str, channel_id: str, slack_ts: str) -> None:
        self.session.execute(
            update(Message)
            .where(
                and_(
                    Message.team_id == team_id,
                    Message.channel_id == channel_id,
                    Message.slack_ts == slack_ts,
                )
            )
            .values(is_deleted=True)
        )

    def fetch_messages_for_user(
        self,
        team_id: str,
        user_id: str,
        since: dt.datetime,
        until: Optional[dt.datetime] = None,
    ) -> List[Message]:
        user = self.get_user_with_prefs(team_id, user_id)
        if not user:
            return []
        channel_ids = [sub.channel_id for sub in user.subscriptions if sub.enabled]
        if not channel_ids:
            return []

        stmt = select(Message).where(
            and_(
                Message.team_id == team_id,
                Message.channel_id.in_(channel_ids),
                Message.created_at >= since,
                Message.is_deleted.is_(False),
            )
        )
        if until:
            stmt = stmt.where(Message.created_at < until)

        return list(
            self.session.execute(stmt.order_by(Message.created_at.asc())).scalars().all()
        )

    def cleanup_old_messages(self, before: dt.datetime) -> int:
        result = self.session.execute(
            Message.__table__.delete().where(Message.created_at < before)
        )
        return result.rowcount or 0
