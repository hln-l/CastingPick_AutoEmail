import base64
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def send_report(
    *, api_key: str, sender: str, recipient: str, subject: str,
    body: str, attachment: Path,
) -> str:
    payload = {
        "from": sender,
        "to": [recipient],
        "subject": subject,
        "text": body,
        "attachments": [{
            "filename": attachment.name,
            "content": base64.b64encode(attachment.read_bytes()).decode("ascii"),
        }],
    }
    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "CastingPick-AutoEmail/0.1",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
    except HTTPError as exc:
        # Do not echo response bodies or credentials into Actions logs.
        raise RuntimeError(
            f"Resend 발송 실패(HTTP {exc.code}). Resend Logs에서 API 키, 발신 도메인 및 수신자 제한을 확인하세요."
        ) from None
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Resend 연결 실패. 네트워크 상태를 확인한 후 다시 실행하세요.") from None
    if not result.get("id"):
        raise RuntimeError("Resend가 발송 ID를 반환하지 않았습니다.")
    return str(result["id"])
