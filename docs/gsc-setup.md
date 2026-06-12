# GSC 자동 수집 셋업 가이드

`automation/scripts/gsc_reader.py` + `.github/workflows/gsc-weekly.yml` 가
주 1회(매주 월요일 00:00 KST) Google Search Console 데이터를 자동으로 가져와
`automation/ooda/gsc-snapshot-latest.json` / `gsc-summary-latest.md` 를 갱신·커밋한다.

운영자가 한 번만 셋업하면 그 뒤로는 무인.

---

## 인증 방식 선택

| 방식 | 설치 시간 | 권한 부여 | 권장 상황 |
|---|---|---|---|
| **A. OAuth (ADC)** ⭐ | 3분 | 본인 Google 계정으로 OAuth 동의만 | "사용자 추가 실패: 이메일 찾을 수 없음" 등 서비스 계정 권한 부여가 막힐 때 |
| B. 서비스 계정 | 8분 | GSC 속성에 서비스 계정 이메일 추가 | 다중 계정·팀 운영, 또는 본인 계정과 분리하고 싶을 때 |

→ **권장은 A**. mureobom 단일 운영자 + 본인 GSC 권한이면 OAuth가 가장 빠름.

---

## A. OAuth(ADC) 방식 — Cloud Shell 한 번 실행 (3분)

별도 OAuth 클라이언트 ID를 만들 필요 없이 `gcloud` 자체 OAuth 앱으로
ADC(Application Default Credentials) 파일을 발급받아 GitHub Secret에 넣는다.

### A-1. Cloud Shell 열기

[console.cloud.google.com](https://console.cloud.google.com) 우상단 **`>_` 아이콘(Cloud Shell 활성화)** 클릭.

### A-2. 다음 명령 실행 (Cloud Shell 안)

```bash
gcloud auth application-default login \
  --scopes="https://www.googleapis.com/auth/webmasters.readonly,openid"
```

- 브라우저에 동의 화면이 뜨면 **본인 Google 계정** (GSC 소유 계정)으로 로그인 → **허용**.
- 완료되면 Cloud Shell에 ADC 파일 경로가 출력됨:
  `Credentials saved to file: [/tmp/tmp.xxxx/application_default_credentials.json]` 또는
  `~/.config/gcloud/application_default_credentials.json`

### A-3. ADC 파일 내용 출력 (복사용)

```bash
cat ~/.config/gcloud/application_default_credentials.json
```

이 JSON 전체(`{ "client_id": "...", "client_secret": "...", "refresh_token": "...", "type": "authorized_user" }`)를 복사.

> **⚠ 채팅창·공개 PR에 절대 붙여넣지 말 것.** GitHub Secrets에만 넣는다.

### A-4. GitHub Secrets 등록

GitHub 리포 → **Settings → Secrets and variables → Actions** → **New repository secret**

| 이름 | 값 |
|---|---|
| `GSC_OAUTH_JSON` | A-3에서 복사한 ADC JSON 전체 |
| `GSC_SITE_URL` | `sc-domain:mureobom.com` (도메인 속성) 또는 `https://mureobom.com/` (URL 속성) |
| `GSC_QUOTA_PROJECT` | A-1 Cloud Shell 좌측 상단의 GCP 프로젝트 ID (예: `mureobom`). User OAuth는 quota project가 필수. 또한 해당 프로젝트에서 **Search Console API가 활성화**돼 있어야 함 — Cloud Shell에서 한 줄: `gcloud services enable searchconsole.googleapis.com` |

### A-5. 첫 실행

Actions 탭 → **GSC Weekly Snapshot** → **Run workflow** → 성공하면 `chore(ooda): refresh GSC snapshot ...` 커밋이 자동 생성됨.

> refresh_token은 본인이 [myaccount.google.com/permissions](https://myaccount.google.com/permissions)
> 에서 "Google Cloud SDK" 접근 권한을 해제하기 전까지 만료되지 않음 (장기 무인 운영 OK).

---

## B. 서비스 계정 방식 (대안)

### B-1단계 — Google Cloud Project + 서비스 계정 (5분)

1. [console.cloud.google.com](https://console.cloud.google.com) 접속
2. 상단 프로젝트 선택 → **새 프로젝트** (이름 예: `mureobom-gsc`)
3. 좌측 메뉴 → **API 및 서비스 → 라이브러리** → "Search Console API" 검색 → **사용 설정**
4. **API 및 서비스 → 사용자 인증 정보** → 상단 **사용자 인증 정보 만들기** → **서비스 계정**
   - 이름: `gsc-reader`
   - 역할은 비워둠 (이 프로젝트에서 권한 부여 안 함)
   - 만들기 완료
5. 생성된 서비스 계정 클릭 → **키** 탭 → **키 추가 → 새 키 만들기** → **JSON** → 다운로드
   - 다운로드된 JSON 파일을 안전한 곳에 보관 (절대 커밋 금지)
6. 서비스 계정의 **이메일 주소** 복사 (예: `gsc-reader@mureobom-gsc.iam.gserviceaccount.com`)

---

## B-2단계 — GSC에 서비스 계정 권한 부여 (1분)

1. [search.google.com/search-console](https://search.google.com/search-console) → `mureobom.com` 속성 선택
2. 좌측 하단 **설정 → 사용자 및 권한** → **사용자 추가**
3. 이메일에 위에서 복사한 서비스 계정 이메일 붙여넣기
4. 권한: **전체** (또는 최소 "제한적" — 읽기 전용으로 충분)
5. 추가

---

## B-3단계 — GitHub Secrets 등록 (2분)

GitHub `mureobom.com` 리포 → **Settings → Secrets and variables → Actions** → **New repository secret**

| 이름 | 값 |
|---|---|
| `GSC_CREDS_JSON` | 1단계에서 다운로드한 JSON 파일의 **전체 내용**을 그대로 붙여넣기 |
| `GSC_SITE_URL` | `sc-domain:mureobom.com` (도메인 속성) 또는 `https://mureobom.com/` (URL 속성) |

> 본인 GSC 속성 유형을 모른다면 GSC 좌상단 속성 선택 드롭다운에서 확인.
> "도메인" 라벨이 붙어 있으면 `sc-domain:mureobom.com`,
> URL 형태로 표시되면 `https://mureobom.com/`.

---

## B-4단계 — 첫 실행 (수동, 1분)

1. GitHub 리포 → **Actions** 탭 → 좌측 **GSC Weekly Snapshot** 워크플로
2. 우상단 **Run workflow** → 기본값 그대로 → **Run workflow**
3. 1~2분 후 완료. 성공하면 `chore(ooda): refresh GSC snapshot ...` 커밋이 자동 생성됨

확인:
- `automation/ooda/gsc-snapshot-latest.json` — 전체 응답
- `automation/ooda/gsc-summary-latest.md` — observations에 붙여넣기용 표

---

## 로컬 실행 (선택)

서비스 계정 JSON 키 파일을 레포 루트에 `gsc-creds.json`으로 저장 (gitignore 자동 처리).

```powershell
pip install -r automation/scripts/requirements.txt
$env:GSC_SITE_URL="sc-domain:mureobom.com"
python automation/scripts/gsc_reader.py
```

---

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `User does not have sufficient permission for site` | OAuth: 잘못된 Google 계정으로 동의함 / 서비스 계정: B-2단계 권한 부여 누락 |
| `사용자 추가 실패: 이메일 찾을 수 없음` (GSC UI) | 서비스 계정 이메일을 GSC가 거부 → **A 방식(OAuth)으로 전환** |
| `GSC_OAUTH_JSON 환경변수도 없고 ...` | Secret 미등록. A-4 또는 B-3 다시 확인 |
| `Token has been expired or revoked` | OAuth refresh_token 만료 — A-2 재실행 후 새 ADC로 Secret 갱신 |
| `accessNotConfigured` / `quota project ... not set` | OAuth 인증 + `GSC_QUOTA_PROJECT` Secret 누락 또는 그 프로젝트에서 Search Console API 미활성화 — Cloud Shell `gcloud services enable searchconsole.googleapis.com --project=<프로젝트ID>` |
| `Quota exceeded` | GSC API 일 한도 초과 — 다음 날 재시도 (보통 안 걸림) |
| 빈 결과 | 속성 식별자(`GSC_SITE_URL`)가 도메인/URL 속성 매칭 안 됨 — 형식 확인 |

---

## 활용 — Macro OODA Observe 자동화

`gsc-summary-latest.md`가 매주 갱신되므로 `observations/{YYYY-WW}.md` §2(트래픽 - Google
Search Console) 셀에 이 파일 내용을 그대로 복붙하면 됨.

특히 "트랙 2 재공유 후보" 표는 [policy-calendar-2026H2.md](../automation/ooda/policy-calendar-2026H2.md)
의 재공유 우선순위 결정에 직접 입력됨.
