import unittest
import csv
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from ticket_watch.extract import contains_keyword, extract_notice, extract_performance, extract_round
from ticket_watch.models import Media, WatchAccount
from ticket_watch.models import TicketNotice
from ticket_watch.report import write_report


class ExtractTests(unittest.TestCase):
    def test_round_variants(self):
        self.assertEqual(extract_round("1차 티켓 오픈 안내"), 1)
        self.assertEqual(extract_round("10차티켓오픈 D-DAY"), 10)
        self.assertEqual(extract_round("2차 Ticket Open"), 2)
        self.assertIsNone(extract_round("캐스팅 스케줄 공개"))

    def test_performance_title(self):
        self.assertEqual(extract_performance("뮤지컬 <엘리자벳>\n3차 티켓 오픈"), "엘리자벳")
        self.assertEqual(extract_performance("아무 캡션", "렌트"), "렌트")

    def test_notice(self):
        media = Media("m1", "official", "[뮤지컬 데스노트]\n4차 티켓 오픈", "https://example.com/p/1", datetime.now(timezone.utc))
        notice = extract_notice(media, WatchAccount("official"))
        self.assertIsNotNone(notice)
        self.assertEqual(notice.ticket_round, 4)
        self.assertEqual(notice.performance, "뮤지컬 데스노트")

    def test_editable_keywords_ignore_spacing_and_case(self):
        self.assertTrue(contains_keyword("3차 티켓오픈 안내", ["티켓 오픈"]))
        self.assertTrue(contains_keyword("2차 TICKET OPEN", ["ticket open"]))
        self.assertFalse(contains_keyword("캐스팅 공개", ["티켓 오픈"]))

    def test_empty_report_explicitly_says_no_news(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.csv"
            write_report(path, [], [])
            with path.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.reader(file))
            self.assertEqual(rows[1][0], "신규 소식 없음")

    def test_report_is_chronological(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "report.csv"
            newer = TicketNotice("2", "b", "B", 2, "https://example.com/2", datetime(2026, 9, 29, 2, tzinfo=timezone.utc))
            older = TicketNotice("1", "a", "A", 1, "https://example.com/1", datetime(2026, 9, 29, 1, tzinfo=timezone.utc))
            write_report(path, [newer, older], [])
            with path.open(encoding="utf-8-sig", newline="") as file:
                rows = list(csv.reader(file))
            self.assertEqual([rows[1][1], rows[2][1]], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
