from __future__ import annotations

import datetime as dt
from typing import List, Protocol


class EnrichmentItem(dict):
    """Simple container for enrichment records."""


class BaseConnector(Protocol):
    def fetch_items(
        self, team_id: str, user_id: str, since: dt.datetime, until: dt.datetime
    ) -> List[EnrichmentItem]:
        ...
