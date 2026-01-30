from __future__ import annotations

import logging

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from slack_digest_bot.app.settings import Settings
from slack_digest_bot.slack.handlers_dm import register_dm_handlers
from slack_digest_bot.slack.handlers_events import register_message_handlers
from slack_digest_bot.slack.slack_client import SlackClient

log = logging.getLogger(__name__)


def build_bolt_app(settings: Settings) -> tuple[App, SlackClient]:
    app = App(
        token=settings.slack_bot_token.get_secret_value(),
        signing_secret=settings.slack_signing_secret.get_secret_value()
        if settings.slack_signing_secret
        else None,
        process_before_response=True,
    )

    slack_client = SlackClient(settings.slack_bot_token.get_secret_value())

    register_message_handlers(app)
    register_dm_handlers(app, slack_client)

    @app.error
    def handle_errors(error, body, logger):
        logger.error("Slack Bolt error: %s", error, exc_info=True)

    return app, slack_client


def run_socket_mode(app: App, settings: Settings) -> None:
    handler = SocketModeHandler(
        app, app_token=settings.slack_app_token.get_secret_value() if settings.slack_app_token else None
    )
    handler.start()
