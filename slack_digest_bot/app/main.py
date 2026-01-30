import logging
import os

from slack_digest_bot.app.logging_config import configure_logging
from slack_digest_bot.app.settings import get_settings
from slack_digest_bot.digest.scheduler import DigestScheduler
from slack_digest_bot.slack.bolt_app import build_bolt_app, run_socket_mode
from slack_digest_bot.storage.db import init_db


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    logging.getLogger(__name__).info("Starting Slack digest bot in %s mode", settings.env)

    init_db()
    app, slack_client = build_bolt_app(settings)

    scheduler = DigestScheduler(slack_client)
    scheduler.bootstrap_from_db()
    scheduler.start()

    if settings.slack_app_token:
        run_socket_mode(app, settings)
    else:
        port = int(os.environ.get("PORT", 3000))
        app.start(port=port)


if __name__ == "__main__":
    main()
