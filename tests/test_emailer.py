import base64
import io
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError

from ticket_watch.emailer import send_report


class EmailerTests(unittest.TestCase):
    def test_resend_payload_preserves_csv_and_recipient(self):
        with TemporaryDirectory() as directory:
            attachment = Path(directory) / "report.csv"
            original = "공연명,차수\n엘리자벳,3\n".encode("utf-8-sig")
            attachment.write_bytes(original)
            with patch("ticket_watch.emailer.urlopen", return_value=io.BytesIO(b'{"id":"email-1"}')) as mocked:
                result = send_report(api_key="test-key", sender="onboarding@resend.dev",
                                     recipient="castingpick@naver.com", subject="공지", body="결과", attachment=attachment)
            request = mocked.call_args.args[0]
            payload = json.loads(request.data)
            self.assertEqual(result, "email-1")
            self.assertEqual(payload["to"], ["castingpick@naver.com"])
            self.assertEqual(base64.b64decode(payload["attachments"][0]["content"]), original)
            self.assertEqual(request.get_header("Authorization"), "Bearer test-key")

    def test_error_does_not_expose_secret_or_response(self):
        with TemporaryDirectory() as directory:
            attachment = Path(directory) / "report.csv"
            attachment.write_bytes(b"csv")
            error = HTTPError("https://api.resend.com/emails", 403, "error", {}, io.BytesIO(b"private details"))
            with patch("ticket_watch.emailer.urlopen", side_effect=error):
                with self.assertRaises(RuntimeError) as caught:
                    send_report(api_key="secret-key", sender="from@example.com", recipient="to@example.com",
                                subject="test", body="test", attachment=attachment)
            self.assertIn("403", str(caught.exception))
            self.assertNotIn("secret-key", str(caught.exception))
            self.assertNotIn("private details", str(caught.exception))
