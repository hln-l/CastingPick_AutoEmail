import re

from .models import Media, TicketNotice, WatchAccount


ROUND_PATTERN = re.compile(
    r"(?<!\d)(\d{1,2})\s*차\s*(?:티켓|ticket)\s*(?:오픈|open)",
    re.IGNORECASE,
)
TITLE_PATTERNS = (
    re.compile(r"(?:뮤지컬|연극|공연)\s*[<〈《「『【\[]\s*([^>〉》」』】\]]{1,80})\s*[>〉》」』】\]]"),
    re.compile(r"[<〈《「『【]\s*([^>〉》」』】]{1,80})\s*[>〉》」』】]"),
)


def extract_round(caption: str) -> int | None:
    match = ROUND_PATTERN.search(caption or "")
    return int(match.group(1)) if match else None


def extract_performance(caption: str, hint: str = "") -> str:
    if hint.strip():
        return hint.strip()
    for pattern in TITLE_PATTERNS:
        match = pattern.search(caption or "")
        if match:
            return re.sub(r"\s+", " ", match.group(1)).strip()
    for line in (caption or "").splitlines():
        candidate = re.sub(r"^[#\s📢🎫🎟️✨\[【]+|[#\s\]】]+$", "", line).strip()
        if candidate and not ROUND_PATTERN.search(candidate) and len(candidate) <= 80:
            return candidate
    return "공연명 확인 필요"


def contains_keyword(caption: str, keywords: list[str]) -> bool:
    normalized_caption = re.sub(r"\s+", "", caption or "").casefold()
    return any(
        re.sub(r"\s+", "", keyword).casefold() in normalized_caption
        for keyword in keywords
        if keyword.strip()
    )


def extract_notice(
    media: Media, account: WatchAccount, keywords: list[str] | None = None
) -> TicketNotice | None:
    if keywords is not None and not contains_keyword(media.caption, keywords):
        return None
    ticket_round = extract_round(media.caption)
    if ticket_round is None:
        return None
    return TicketNotice(
        media_id=media.id,
        account=media.username,
        performance=extract_performance(media.caption, account.performance_hint),
        ticket_round=ticket_round,
        permalink=media.permalink,
        posted_at=media.timestamp,
    )
