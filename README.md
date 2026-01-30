# Slack Digest Bot

Slack app that tracks selected channels, stores messages, and sends a daily digest via DM with natural-language configuration.

## Quick start
- Install dependencies: `pip install -e .[dev]`
- Copy `.env.example` to `.env` and fill Slack + OpenAI credentials.
- Initialize DB (SQLite by default): `python -m slack_digest_bot.app.main` will auto-create tables on first run.
- Run in Socket Mode (recommended for local): ensure `SLACK_APP_TOKEN` is set, then `python -m slack_digest_bot.app.main`.
- For HTTP mode set `SLACK_SIGNING_SECRET` and `PORT`; the app will listen on that port.

## Project layout
- `slack_digest_bot/app`: settings, logging, entrypoint.
- `slack_digest_bot/slack`: Bolt app wiring, event + DM handlers, Slack client wrapper.
- `slack_digest_bot/storage`: SQLAlchemy models, session helpers, repository.
- `slack_digest_bot/nl`: OpenAI prompts, tool schemas, router for DM config.
- `slack_digest_bot/digest`: preprocessing heuristics, OpenAI digest call, rendering, delivery, scheduler.
- `slack_digest_bot/integrations`: pluggable external connectors (stubs).
- `tests`: minimal unit tests for preprocessing, repo, and NL router.

## Notes
- Scheduling uses APScheduler in-process; production workers should run the scheduler separately.
- Tokens should be encrypted at rest; `APP_ENCRYPTION_KEY` is provided for this but encryption wiring is left for implementation detail.
- Alembic migrations folder is present but not yet configured; generate migrations once models stabilize.
