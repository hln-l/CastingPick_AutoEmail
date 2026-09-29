# 인스타그램 티켓 오픈 Watcher

등록한 뮤지컬 공식 Instagram 프로페셔널 계정의 최근 게시물을 매일 확인해, 최근 24시간 안에 올라온 `N차 티켓 오픈` 공지를 CSV 한 파일로 모아 이메일로 보냅니다. 같은 Instagram media ID는 `state/seen.json`에 기록하여 다시 보내지 않습니다. 새 공지가 없는 날에도 `신규 소식 없음` 한 행이 든 CSV를 발송합니다.

## 중요한 제약

Instagram 로그인 화면을 자동 조작하거나 HTML을 스크래핑하지 않습니다. Meta Graph API의 Business Discovery를 사용하므로 조회자 본인에게 Facebook Page와 연결된 Instagram 프로페셔널 계정이 필요하며, watch list 대상도 공개 비즈니스/크리에이터 계정이어야 합니다. 개인 계정은 이 방식으로 조회할 수 없습니다.

## 1. Watch list·키워드·수신 이메일 설정

`config/accounts.json` 하나에서 검색 키워드, 수신 이메일, 감시 계정을 언제든 수정할 수 있습니다. 계정명에는 `@`를 쓰지 않습니다.

```json
{
  "keywords": ["티켓 오픈", "ticket open"],
  "notification": {
    "email_to": "me@example.com"
  },
  "accounts": [
    {"username": "official_account", "performance_hint": "엘리자벳"},
    {"username": "another_official", "performance_hint": ""}
  ]
}
```

키워드 비교에서는 공백과 영문 대소문자를 무시합니다. 키워드가 포함되면서 `N차 티켓 오픈` 형식에서 차수도 확인되는 게시물만 수집합니다. 수신 주소를 저장소 파일에 남기고 싶지 않으면 `email_to`를 비워두고 GitHub Secret `EMAIL_TO`를 사용하세요. Secret 값이 설정 파일보다 우선합니다.

한 계정이 한 작품만 홍보한다면 `performance_hint`를 넣는 것이 가장 정확합니다. 비워두면 캡션의 `뮤지컬 <작품명>` 같은 표기를 우선 찾고, 없으면 첫 번째 일반 문장을 사용합니다.

## 2. Meta API 준비

Meta 개발자 앱에서 Instagram API with Facebook Login을 설정하고, Facebook Page에 연결된 본인의 Instagram 프로페셔널 계정 ID와 장기 액세스 토큰을 준비합니다. 토큰에는 Business Discovery에 필요한 권한이 있어야 합니다. API 버전은 저장소 변수로 바꿀 수 있습니다.

## 3. GitHub Actions 설정

GitHub 저장소의 Settings → Secrets and variables → Actions에 다음 Repository secrets를 등록합니다.

| 이름 | 값 |
|---|---|
| `INSTAGRAM_IG_USER_ID` | 조회에 사용할 본인 Instagram 프로페셔널 계정 ID |
| `INSTAGRAM_ACCESS_TOKEN` | Meta 장기 액세스 토큰 |
| `SMTP_HOST` | 예: Gmail은 `smtp.gmail.com` |
| `SMTP_PORT` | SSL SMTP는 보통 `465` |
| `SMTP_USERNAME` | SMTP 로그인 이메일 |
| `SMTP_PASSWORD` | Gmail 사용 시 일반 비밀번호가 아닌 앱 비밀번호 |
| `EMAIL_FROM` | 발신 주소 |
| `EMAIL_TO` | 선택 사항. 설정하면 `config/accounts.json`의 수신 주소보다 우선함 |

Repository variable `INSTAGRAM_GRAPH_VERSION`에는 사용할 Graph API 버전(예: `v24.0`)을 넣을 수 있습니다. workflow는 매일 한국 시간 16:10에 수집을 시작하고, 수집이 일찍 끝나면 16:15까지 기다렸다가 이메일을 보냅니다. GitHub Actions 자체가 늦게 시작되면 16:15 이후 수집 완료 즉시 발송됩니다. Actions 화면의 **Run workflow**로 즉시 시험할 수도 있습니다.

중복 방지 상태를 저장하기 위해 workflow에 `contents: write` 권한이 필요합니다. 저장소 설정에서 Actions의 workflow 권한이 read/write로 허용되어 있어야 합니다.

## 로컬 테스트

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

실제 API와 이메일까지 시험하려면 위 환경 변수를 설정한 뒤 실행합니다.

```sh
PYTHONPATH=src python3 -m ticket_watch.main
```

이메일 없이 수집 결과만 시험하려면 `--no-email`을 붙입니다. 실제 조회에도 Instagram 환경 변수는 필요합니다.
