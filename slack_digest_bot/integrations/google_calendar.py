from __future__ import annotations

import datetime as dt
from typing import List

from slack_digest_bot.integrations.base import BaseConnector, EnrichmentItem


class GoogleCalendarConnector(BaseConnector):
    def __init__(self, token_encrypted: str):
        self.token_encrypted = token_encrypted

    def fetch_items(
        self, team_id: str, user_id: str, since: dt.datetime, until: dt.datetime
    ) -> List[EnrichmentItem]:
        # Placeholder: integrate with Google Calendar API using decrypted token.
        return []
