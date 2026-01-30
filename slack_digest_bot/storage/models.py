from __future__ import annotations

import datetime as dt
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from slack_digest_bot.storage.db import Base


class Installation(Base):
    __tablename__ = "installations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[str] = mapped_column(String(64), index=True)
    enterprise_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    bot_token_encrypted: Mapped[str] = mapped_column(String(512))
    installed_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[str] = mapped_column(String(64), index=True)
    timezone: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    digest_time_local: Mapped[str] = mapped_column(String(5), default="09:00")  # HH:MM
    last_digest_sent_at: Mapped[Optional[dt.datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    subscriptions: Mapped[list["ChannelSubscription"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    tracking_prefs: Mapped[Optional["TrackingPreferences"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_users_team_user", "team_id", "user_id"),)


class ChannelSubscription(Base):
    __tablename__ = "channel_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    channel_id: Mapped[str] = mapped_column(String(64), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    priority_weight: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="subscriptions")

    __table_args__ = (
        Index("ix_channel_sub_team_channel", "team_id", "channel_id"),
        UniqueConstraint("team_id", "user_id", "channel_id", name="uq_sub_per_user_channel"),
    )


class TrackingPreferences(Base):
    __tablename__ = "tracking_prefs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[str] = mapped_column(String(64), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    include_overview: Mapped[bool] = mapped_column(Boolean, default=True)
    include_mentions_me: Mapped[bool] = mapped_column(Boolean, default=True)
    include_broadcasts: Mapped[bool] = mapped_column(Boolean, default=True)
    include_unanswered_questions: Mapped[bool] = mapped_column(Boolean, default=True)
    include_suggested_actions: Mapped[bool] = mapped_column(Boolean, default=True)
    max_channels: Mapped[int] = mapped_column(Integer, default=10)
    custom_rules_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="tracking_prefs")

    __table_args__ = (Index("ix_tracking_prefs_team_user", "team_id", "user_id"),)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    team_id: Mapped[str] = mapped_column(String(64), index=True)
    channel_id: Mapped[str] = mapped_column(String(64), index=True)
    slack_ts: Mapped[str] = mapped_column(String(32), index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    thread_ts: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    subtype: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), default=func.now())

    __table_args__ = (
        UniqueConstraint("team_id", "channel_id", "slack_ts", name="uq_message_ts"),
        Index("ix_messages_team_user_created", "team_id", "user_id", "created_at"),
        Index("ix_messages_team_thread", "team_id", "thread_ts"),
    )
