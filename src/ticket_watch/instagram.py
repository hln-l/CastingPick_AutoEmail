import json
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .models import Media, WatchAccount


class InstagramClient:
    def __init__(self, ig_user_id: str, access_token: str, api_version: str = "v24.0"):
        self.ig_user_id = ig_user_id
        self.access_token = access_token
        self.api_version = api_version

    def recent_media(self, account: WatchAccount, limit: int = 25) -> list[Media]:
        username = account.username.lstrip("@").strip()
        fields = (
            f"business_discovery.username({username})"
            f"{{username,media.limit({limit}){{id,caption,permalink,timestamp}}}}"
        )
        query = urlencode({"fields": fields, "access_token": self.access_token})
        url = f"https://graph.facebook.com/{self.api_version}/{self.ig_user_id}?{query}"
        request = Request(url, headers={"Accept": "application/json"})
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except Exception as exc:
            raise RuntimeError(f"@{username} 조회 실패: {exc}") from exc
        discovery = payload.get("business_discovery") or {}
        media_rows = (discovery.get("media") or {}).get("data") or []
        result = []
        for row in media_rows:
            if not all(row.get(key) for key in ("id", "permalink", "timestamp")):
                continue
            result.append(
                Media(
                    id=str(row["id"]),
                    username=discovery.get("username", username),
                    caption=row.get("caption", ""),
                    permalink=row["permalink"],
                    timestamp=datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")),
                )
            )
        return result

