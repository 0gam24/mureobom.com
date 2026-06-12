# GSC 자동 수집 셋업 가이드

`automation/scripts/gsc_reader.py` + `.github/workflows/gsc-weekly.yml` 가
주 1회(매주 월요일 00:00 KST) Google Search Console 데이터를 자동으로 가져와
`automation/ooda/gsc-snapshot-latest.json` / `gsc-summary-latest.md` 를 갱신·커밋한다.

운영자가 한 번만 셋업하면 그 뒤로는 무인.

---

## 1단계 — Google Cloud Project + 서비스 계정 (5분)

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

## 2단계 — GSC에 서비스 계정 권한 부여 (1분)

1. [search.google.com/search-console](https://search.google.com/search-console) → `mureobom.com` 속성 선택
2. 좌측 하단 **설정 → 사용자 및 권한** → **사용자 추가**
3. 이메일에 위에서 복사한 서비스 계정 이메일 붙여넣기
4. 권한: **전체** (또는 최소 "제한적" — 읽기 전용으로 충분)
5. 추가

---

## 3단계 — GitHub Secrets 등록 (2분)

GitHub `mureobom.com` 리포 → **Settings → Secrets and variables → Actions** → **New repository secret**

| 이름 | 값 |
|---|---|
| `GSC_CREDS_JSON` | 1단계에서 다운로드한 JSON 파일의 **전체 내용**을 그대로 붙여넣기 |
| `GSC_SITE_URL` | `sc-domain:mureobom.com` (도메인 속성) 또는 `https://mureobom.com/` (URL 속성) |

> 본인 GSC 속성 유형을 모른다면 GSC 좌상단 속성 선택 드롭다운에서 확인.
> "도메인" 라벨이 붙어 있으면 `sc-domain:mureobom.com`,
> URL 형태로 표시되면 `https://mureobom.com/`.

---

## 4단계 — 첫 실행 (수동, 1분)

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
| `User does not have sufficient permission for site` | 2단계 GSC 권한 부여 누락 또는 이메일 오타 |
| `GSC_CREDS_JSON 환경변수도 없고 gsc-creds.json 파일도 없습니다` | Secret 미등록 또는 로컬 키 파일 없음 |
| `Quota exceeded` | GSC API 일 한도 초과 — 다음 날 재시도 (보통 안 걸림) |
| 빈 결과 | 속성 식별자(`GSC_SITE_URL`)가 도메인/URL 속성 매칭 안 됨 — 형식 확인 |

---

## 활용 — Macro OODA Observe 자동화

`gsc-summary-latest.md`가 매주 갱신되므로 `observations/{YYYY-WW}.md` §2(트래픽 - Google
Search Console) 셀에 이 파일 내용을 그대로 복붙하면 됨.

특히 "트랙 2 재공유 후보" 표는 [policy-calendar-2026H2.md](../automation/ooda/policy-calendar-2026H2.md)
의 재공유 우선순위 결정에 직접 입력됨.
