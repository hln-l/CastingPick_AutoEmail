import csv
from pathlib import Path
from zoneinfo import ZoneInfo

from .models import TicketNotice


SEOUL = ZoneInfo("Asia/Seoul")


def write_report(path: Path, notices: list[TicketNotice], warnings: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["상태", "공연명", "티켓 오픈", "인스타그램 계정", "게시 시간(KST)", "게시물 링크", "비고"])
        if notices:
            for notice in sorted(notices, key=lambda item: item.posted_at):
                writer.writerow([
                    "신규",
                    notice.performance,
                    f"{notice.ticket_round}차 티켓 오픈",
                    f"@{notice.account}",
                    notice.posted_at.astimezone(SEOUL).strftime("%Y-%m-%d %H:%M:%S"),
                    notice.permalink,
                    "",
                ])
        else:
            writer.writerow(["신규 소식 없음", "", "", "", "", "", ""])
        for warning in warnings:
            writer.writerow(["수집 경고", "", "", "", "", "", warning])

