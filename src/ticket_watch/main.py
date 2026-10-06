import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .emailer import send_report
from .extract import extract_notice
from .instagram import InstagramClient
from .models import WatchAccount
from .report import SEOUL, write_report


def required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"필수 환경 변수 {name}이 없습니다.")
    return value


def load_config(path: Path) -> tuple[list[WatchAccount], list[str], str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    accounts = []
    for row in payload.get("accounts", []):
        username = str(row.get("username", "")).lstrip("@").strip()
        if not username:
            raise ValueError("watch list의 username은 비워둘 수 없습니다.")
        accounts.append(WatchAccount(username, str(row.get("performance_hint", ""))))
    keywords = [str(item).strip() for item in payload.get("keywords", []) if str(item).strip()]
    if not keywords:
        raise ValueError("keywords에는 한 개 이상의 검색어가 필요합니다.")
    email_to = str((payload.get("notification") or {}).get("email_to", "")).strip()
    return accounts, keywords, email_to


def run(config: Path, state_path: Path, report_path: Path, now: datetime) -> tuple[int, list[str], str]:
    accounts, keywords, config_email = load_config(config)
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {}
    seen = set(map(str, state.get("seen_media_ids", [])))
    client = InstagramClient(
        required_env("INSTAGRAM_IG_USER_ID"),
        required_env("INSTAGRAM_ACCESS_TOKEN"),
        os.environ.get("INSTAGRAM_GRAPH_VERSION", "v24.0"),
    )
    cutoff = now - timedelta(hours=24)
    notices, warnings, newly_seen = [], [], set()
    for account in accounts:
        try:
            media_rows = client.recent_media(account)
        except RuntimeError as exc:
            warnings.append(str(exc))
            continue
        for media in media_rows:
            if media.timestamp < cutoff or media.timestamp > now or media.id in seen:
                continue
            notice = extract_notice(media, account, keywords)
            if notice:
                notices.append(notice)
                newly_seen.add(media.id)
    write_report(report_path, notices, warnings)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"seen_media_ids": sorted(seen | newly_seen)[-5000:]}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return len(notices), warnings, config_email


def wait_until_local_time(value: str, now: datetime | None = None) -> int:
    try:
        hour, minute = map(int, value.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError as exc:
        raise ValueError("--send-at은 HH:MM 형식이어야 합니다.") from exc
    current = (now or datetime.now(timezone.utc)).astimezone(SEOUL)
    target = current.replace(hour=hour, minute=minute, second=0, microsecond=0)
    seconds = max(0, int((target - current).total_seconds()))
    if seconds:
        print(f"이메일 발송 시각까지 {seconds}초 대기합니다.")
        time.sleep(seconds)
    return seconds


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/accounts.json"))
    parser.add_argument("--state", type=Path, default=Path("state/seen.json"))
    parser.add_argument("--report", type=Path)
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--send-at", help="수집 후 이메일을 보낼 한국 시각(HH:MM)")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    report = args.report or Path("reports") / f"ticket-open-{now.astimezone(SEOUL):%Y-%m-%d}.csv"
    count, warnings, config_email = run(args.config, args.state, report, now)
    if not args.no_email:
        if args.send_at:
            wait_until_local_time(args.send_at)
        recipient = os.environ.get("EMAIL_TO", "").strip() or config_email
        if not recipient:
            raise RuntimeError("config의 notification.email_to 또는 EMAIL_TO를 설정해주세요.")
        send_report(
            api_key=required_env("RESEND_API_KEY"),
            sender=os.environ.get("RESEND_FROM", "").strip() or "CastingPick <onboarding@resend.dev>",
            recipient=recipient,
            subject=f"[캐스팅 공지] {now.astimezone(SEOUL):%Y-%m-%d} 신규 {count}건",
            body=(f"최근 24시간 신규 티켓 오픈 공지는 {count}건입니다.\n"
                  f"수집 경고는 {len(warnings)}건입니다. 상세 내용은 첨부 CSV를 확인해주세요."),
            attachment=report,
        )
    print(f"report={report} notices={count} warnings={len(warnings)}")


if __name__ == "__main__":
    main()
