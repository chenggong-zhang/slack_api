This document is written for code-generation agents (e.g., Codex) to implement a production-ready Slack app in Python that:
- Tracks selected Slack channels in real time
- Lets users manage tracking preferences via natural language in DM
- Sends a daily DM digest generated via OpenAI’s API
- Stores data in a database (messages, subscriptions, preferences, installations)
- Supports optional external API integrations (calendar / issue trackers) to improve meeting/deadline detection

---

## 1) Product Goals (What to Build)

### Core user story
A user installs the Slack app into their workspace. They choose which channels to track (and how many). The bot listens to live messages in those channels, stores them, and sends a daily digest in a private DM.

### Digest requirements (must include)
1) Brief overview of work-related content across tracked conversations:
   - meetings, deadlines, clients, deliverables, risks, decisions
2) Messages where the user’s name was mentioned (direct mentions)
3) Broadcast mentions (e.g., @here / @channel / @everyone)
4) Questions asked where no answer was detected
5) Suggested actions the user could take, based on the content above

### Natural language control (must support)
User can DM the bot with natural language to:
- add/remove channels to track
- change how many channels to track (cap/limit)
- modify digest content preferences (toggle sections, add custom rules)
- change digest schedule/timezone
- ask “what are you tracking?” and receive a summary of current configuration

---

## 2) Architecture Overview (How It Should Work)

Implement the app as a set of modules with clear boundaries:

### A) Slack ingestion pipeline (live)
- Listen for Slack message events via Slack Bolt for Python.
- Filter for channels the user is subscribed to.
- Store message content + metadata in DB.
- Handle message edits/deletes (update/soft-delete).

### B) Natural language config (DM)
- In a DM channel with the user, interpret their messages via OpenAI tool calling.
- Convert the user’s request into deterministic “configuration change” tool calls.
- Apply changes to DB and confirm back to user in natural language.

### C) Daily digest job
- Scheduled per user (timezone-aware).
- Query DB for the last digest window (e.g., last 24h or since last_sent_at).
- Preprocess content (mentions/broadcasts/question candidates).
- Call OpenAI to produce structured digest output (JSON schema).
- Render digest into a Slack DM message and send.

### D) Optional external API connectors (enrichment)
Design for plug-in connectors that can enrich the digest:
- Google Calendar: meetings, titles, attendees (optional)
- Jira/Linear/GitHub: issues/PRs mentioned, due dates (optional)
- CRM (Salesforce/HubSpot): client context (optional)

These are optional. The MVP must work using Slack messages only.

---

## 3) Recommended Tech Stack (Python)

### Slack
- slack_bolt (Bolt for Python)
- Socket Mode for local development (no public URL required)
- HTTP mode + OAuth for production distribution (recommended if multi-workspace)

### Database
- PostgreSQL (production)
- SQLite allowed for local dev/testing
- SQLAlchemy (or SQLModel) + Alembic migrations

### Scheduling / Background jobs
- MVP: APScheduler (single process)
- Production: Celery + Redis (or RQ) for retries/scale

### OpenAI
- OpenAI Python SDK
- Use tool calling for config management
- Use structured JSON output for daily digest

### Tooling
- ruff (lint)
- black (format)
- mypy (types)
- pytest (tests)

---

## 4) Repository Layout (Target Structure)

Implement this structure (or very close), keeping modules small and testable:

```

slack_digest_bot/
app/
main.py                 # entrypoint: starts Bolt (socket or http)
settings.py             # env + configuration
logging_config.py

```
slack/
  bolt_app.py           # creates Bolt App, middleware, error handlers
  handlers_events.py    # message event ingestion -> DB
  handlers_dm.py        # DM NLP router -> tool calls -> DB updates
  slack_client.py       # Slack WebClient wrapper (retry, rate limits)

storage/
  db.py                 # engine/session
  models.py             # ORM models
  repo.py               # CRUD & queries
  migrations/           # alembic

nl/
  tool_schemas.py       # OpenAI tool schemas for config actions
  router.py             # call OpenAI, execute returned tool calls
  prompts.py            # system prompts (config + digest)

digest/
  scheduler.py          # schedule jobs per user
  preprocess.py         # mention/broadcast/question heuristics
  llm_digest.py         # OpenAI call to produce structured digest
  renderer.py           # digest JSON -> Slack blocks/text
  delivery.py           # send DM via Slack

integrations/
  base.py               # connector interface
  google_calendar.py    # optional
  jira.py               # optional
```

tests/
test_preprocess.py
test_repo.py
test_nl_router.py

.env.example
pyproject.toml (preferred) or requirements.txt
README.md

```

---

## 5) Environment Variables (Must Support)

Create `.env.example` and load via settings.py.

### Slack
- `SLACK_BOT_TOKEN` = xoxb-...
- `SLACK_APP_TOKEN` = xapp-... (Socket Mode)
- `SLACK_SIGNING_SECRET` (HTTP mode validation)
- `SLACK_CLIENT_ID`, `SLACK_CLIENT_SECRET` (OAuth mode)
- `SLACK_SCOPES` (space/comma-separated; keep in config)

### OpenAI
- `OPENAI_API_KEY`
- `OPENAI_MODEL_DIGEST` (e.g., a strong text model)
- `OPENAI_MODEL_NL` (tool-calling capable)

### Database / Security
- `DATABASE_URL` (postgresql+psycopg://... or sqlite:///...)
- `APP_ENCRYPTION_KEY` (used to encrypt Slack tokens at rest)
- `MESSAGE_RETENTION_DAYS` (default e.g. 30)

### Scheduling
- `DEFAULT_DIGEST_HOUR_LOCAL` (e.g., 9)
- `DEFAULT_DIGEST_MINUTE_LOCAL` (e.g., 0)

---

## 6) Slack App Capabilities (What to Implement)

### Events to handle (MVP)
- message events in channels and private channels
- message edits and deletes

Minimum logic:
- Store text, channel_id, user_id, timestamp, thread_ts (if present)
- Ignore bot/self messages to prevent loops
- Only store messages for channels currently tracked by at least one user

### DM interactions (MVP)
Support DM conversation with user:
- “track #channel-a and #channel-b”
- “stop tracking #channel-x”
- “only include mentions and unanswered questions”
- “send digest at 8:30am”
- “what are you tracking?”

DM handler must:
- Call OpenAI with tool schemas
- Execute tools deterministically (no “freeform” DB updates)
- Reply with confirmation + current config summary

### Commands (Optional fallback)
Add slash commands if helpful for debugging:
- `/digest status`
- `/digest track #channel`
- `/digest untrack #channel`

NL DM is still the primary interface.

---

## 7) Database Models (Minimum Required)

Implement these tables (names can differ; fields must exist conceptually):

### A) installations (for multi-workspace)
- id (pk)
- team_id (indexed)
- enterprise_id (nullable)
- bot_token_encrypted
- installed_at
- updated_at

### B) users
- id (pk)
- team_id (indexed)
- user_id (indexed)          # Slack user id
- timezone                   # IANA tz if available
- digest_time_local          # "HH:MM"
- last_digest_sent_at        # timestamp
- created_at, updated_at

### C) channel_subscriptions
- id (pk)
- team_id (indexed)
- user_id (fk -> users)
- channel_id (indexed)
- enabled (bool)
- priority_weight (int default 0)
- created_at, updated_at

### D) tracking_prefs
- id (pk)
- team_id
- user_id (fk)
- include_overview (bool)
- include_mentions_me (bool)
- include_broadcasts (bool)
- include_unanswered_questions (bool)
- include_suggested_actions (bool)
- max_channels (int)
- custom_rules_json (json)   # keywords, clients, exclusions, etc.
- created_at, updated_at

### E) messages
- id (pk)
- team_id (indexed)
- channel_id (indexed)
- slack_ts (indexed unique with channel/team)
- user_id (nullable)
- text (text)
- thread_ts (nullable, indexed)
- subtype (nullable)
- is_deleted (bool default false)
- raw_json (json, optional)
- created_at

Indexes:
- (team_id, channel_id, slack_ts)
- (team_id, user_id, created_at)
- (team_id, thread_ts)

Retention:
- Implement a cleanup job that deletes messages older than `MESSAGE_RETENTION_DAYS`.

---

## 8) Message Preprocessing Rules (Non-LLM First)

Before calling OpenAI, extract these deterministically to reduce cost and improve reliability:

### A) Mentions of the user
- Detect `<@USERID>` tokens or Slack formatted mention entities
- Keep list of messages that mention that user

### B) Broadcast mentions
- Detect Slack broadcast tokens: `<!here>`, `<!channel>`, `<!everyone>`
- Keep list of broadcast messages

### C) Question candidates
- Heuristics: `?` / `？`, starts with “who/what/when/where/why/how”, “can someone”, etc.
- Mark as question_candidate = true

### D) “Unanswered” heuristic (MVP)
- If message is in a thread (`thread_ts`) and there are replies after it, consider it potentially answered.
- If not in thread:
  - Look at next N messages in same channel within a time window; if obvious response exists, mark answered.
- For “answered” detection, allow an optional second-pass mini model, but keep deterministic fallback.

Store derived flags either:
- inline (extra columns), or
- computed at digest time (acceptable for MVP).

---

## 9) OpenAI Integration Requirements

### A) Natural language configuration (tool calling)
Implement tool schemas like:

- `add_channels(channels: list[str])`
- `remove_channels(channels: list[str])`
- `set_max_channels(max_channels: int)`
- `set_digest_time(time_local: str)`
- `set_preferences(preferences: object)`
- `list_configuration()`
- `add_custom_rule(rule: object)`
- `remove_custom_rule(rule_id: str)`

Rules:
- The model must ONLY modify state via tool calls.
- After tool execution, respond with a short confirmation.

### B) Daily digest generation (structured output)
Call OpenAI with a strict JSON schema. Output must include:

- `overview`: string
- `mentions_me`: array of {channel, ts, author, text, permalink?}
- `broadcasts`: array of {channel, ts, author, text}
- `unanswered_questions`: array of {channel, ts, author, question_text, context_snippet}
- `suggested_actions`: array of {priority, action, rationale, related_items}

Rules:
- No hallucinated facts. Only use provided message data.
- If a section is empty, output empty array or empty string.
- Keep output concise and skimmable.

Token/cost control:
- Summarize per channel first if message volume is high.
- Cap messages per channel (configurable).

---

## 10) Slack Delivery Requirements

### A) DM delivery
- Send daily digest via DM to each user.
- Ensure the app can open or reuse a DM channel and post messages reliably.
- Use Slack blocks for readability (optional, but recommended).

### B) User channel selection
User can choose which channels and how many:
- Persist `max_channels` in tracking_prefs
- Enforce limit when adding channels:
  - If over limit, either reject with explanation or auto-disable oldest/lowest priority channels.

Validation of channels:
- Resolve `#name` to `channel_id` using Slack API lookups where needed.
- Handle ambiguous names gracefully (ask user via DM clarification).

---

## 11) Optional External Integrations (Design for Plug-ins)

Create an interface:

`BaseConnector.fetch_items(team_id, user_id, since_dt, until_dt) -> list[EnrichmentItem]`

Examples:
- CalendarConnector: returns meetings (title, start/end, attendees)
- JiraConnector: returns issues updated/mentioned
- GitHubConnector: PRs/issues

Enrichment flow:
- Daily job fetches enrichment items and merges into digest context.
- Do not block digest if connector fails; log and continue.

Security:
- Store connector tokens separately per user/workspace.
- Encrypt at rest using `APP_ENCRYPTION_KEY`.

---

## 12) Reliability & Security Requirements

### Rate limiting and retries
- Slack API calls must handle rate limits (HTTP 429) with backoff.
- OpenAI calls must handle transient failures with retries.

### Token storage
- Slack bot tokens and external connector tokens must be encrypted at rest.
- Do not log tokens.
- Minimize stored Slack message data (store only necessary fields).

### Privacy controls (MVP)
- Allow a user to DM: “delete my data” (implements data deletion).
- Implement retention policy cleanup.

---

## 13) Testing Requirements (Minimum)

Write unit tests for:
- preprocess mention/broadcast/question detection
- unanswered question heuristic
- NL router: tool schema validation + correct repo updates
- repo queries for “last 24h messages for user’s tracked channels”

Add an integration test (optional) that:
- mocks Slack events -> DB insert -> digest build -> “send” called

---

## 14) Development Modes

### Local Dev (Socket Mode)
- Start Bolt Socket Mode using SLACK_BOT_TOKEN + SLACK_APP_TOKEN
- Use SQLite by default
- Run scheduler in-process

### Production (HTTP + OAuth)
- HTTP adapter + OAuth install flow
- Postgres + worker queue
- Scheduler in worker/beat

---

## 15) Implementation Milestones (Order Matters)

1) Boot Slack Bolt app (Socket Mode) + logging + settings
2) DB setup + migrations + models
3) Message event ingestion -> DB (with filters/subtypes)
4) DM interface skeleton (simple commands)
5) OpenAI tool calling for NL configuration (DM)
6) Daily scheduler + digest pipeline (preprocess -> OpenAI -> render -> DM)
7) Multi-workspace OAuth + installation store
8) Optional connectors (calendar/issues)
9) Hardening: retries, retention, data deletion, tests

---

## 16) Definition of Done

The implementation is “done” when:
- A user can install the app, select channels to track via DM, and see tracked status.
- Messages from tracked channels are stored in DB.
- A scheduled daily digest is delivered via DM, containing all required sections.
- Preferences can be changed via natural language and persist correctly.
- The system runs reliably with retries and basic retention.

---

## 17) Non-Goals (Explicitly Out of Scope for MVP)

- Full Slack App Home UI / modals (nice-to-have, not required)
- Perfect “unanswered question” detection (use heuristic + optional model pass)
- Full analytics/dashboard
- Bulk exporting entire workspace history

---

## 18) Agent Coding Standards

- Keep functions small and testable; isolate I/O at module edges.
- Use typed interfaces (mypy-friendly).
- Prefer deterministic preprocessing; use LLM only where it adds clear value.
- Keep OpenAI prompts in dedicated files; avoid prompt strings scattered around.
- Ensure all state changes are executed via tool calls in NL flow.
- Avoid tight coupling between Slack handlers and DB layers (use repo/services).