from __future__ import annotations

import datetime as dt
from typing import List

from slack_digest_bot.integrations.base import BaseConnector, EnrichmentItem


class JiraConnector(BaseConnector):
    def __init__(self, token_encrypted: str, site: str):
        self.token_encrypted = token_encrypted
        self.site = site

    def fetch_items(
        self, team_id: str, user_id: str, since: dt.datetime, until: dt.datetime
    ) -> List[EnrichmentItem]:
        # Placeholder for Jira search calls.
        return []
