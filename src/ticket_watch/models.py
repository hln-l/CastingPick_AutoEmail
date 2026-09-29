from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WatchAccount:
    username: str
    performance_hint: str = ""


@dataclass(frozen=True)
class Media:
    id: str
    username: str
    caption: str
    permalink: str
    timestamp: datetime


@dataclass(frozen=True)
class TicketNotice:
    media_id: str
    account: str
    performance: str
    ticket_round: int
    permalink: str
    posted_at: datetime

