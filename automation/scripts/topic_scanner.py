#!/usr/bin/env python3
"""
물어봄 토픽 스캐너
- 네이버 데이터랩 검색 트렌드 API + 지식iN 검색 API(kin)로
  클러스터별 후보 토픽을 점수화하여 topic-queue.json 생성.
- 지식iN '원문'은 저장하지 않는다. 제목/링크/게시일 메타와
  집계 신호만 사용한다. (약관·저작권·중복 리스크 차단)

ENV (GitHub Actions Secrets):
  NAVER_CLIENT_ID, NAVER_CLIENT_SECRET

Usage:
  python scripts/topic_scanner.py \
      --seeds config/seed-keywords.yaml \
      --scoring config/scoring.yaml \
      --published briefs/_published_slugs.txt \
      --out topic-queue.json
"""
from __future__ import annotations
import argparse, json, os, re, sys, math, datetime as dt
from urllib import request, parse

import yaml  # pip install pyyaml

# kin description은 HTML 엔티티/태그 섞인 짧은 스니펫.
# 본문은 저장 안 하되, 날짜 추정용 패턴만 추출.
_DATE_RE = re.compile(r"(20\d{2})[.\-/년 ]+(\d{1,2})[.\-/월 ]+(\d{1,2})")

KIN_URL = "https://openapi.naver.com/v1/search/kin"
DATALAB_URL = "https://openapi.naver.com/v1/datalab/search"


def _headers():
    cid = os.environ.get("NAVER_CLIENT_ID")
    csec = os.environ.get("NAVER_CLIENT_SECRET")
    if not cid or not csec:
        sys.exit("ERROR: NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 미설정")
    return {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}


# ---------- 네이버 API ----------

def kin_search(query: str, display: int, sort: str) -> list[dict]:
    qs = parse.urlencode({"query": query, "display": display, "sort": sort})
    req = request.Request(f"{KIN_URL}?{qs}", headers=_headers())
    with request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    return data.get("items", [])


def datalab_trend(keyword: str, lookback_days: int) -> list[float]:
    end = dt.date.today()
    start = end - dt.timedelta(days=lookback_days)
    body = json.dumps({
        "startDate": start.isoformat(),
        "endDate": end.isoformat(),
        "timeUnit": "date",
        "keywordGroups": [{"groupName": keyword, "keywords": [keyword]}],
    }).encode()
    h = _headers() | {"Content-Type": "application/json"}
    req = request.Request(DATALAB_URL, data=body, headers=h, method="POST")
    with request.urlopen(req, timeout=15) as r:
        data = json.load(r)
    results = data.get("results", [])
    if not results:
        return []
    return [p["ratio"] for p in results[0].get("data", [])]


# ---------- 점수 컴포넌트 ----------

def trend_momentum(series: list[float]) -> float:
    """최근 7일 평균 vs 직전 구간 평균 상승률 → 0~1"""
    if len(series) < 8:
        return 0.0
    recent = sum(series[-7:]) / 7
    base = sum(series[:-7]) / max(1, len(series) - 7)
    if base <= 0:
        return 0.0
    return max(0.0, min(1.0, (recent - base) / base))


def question_volume(items: list[dict], window_days: int, sort: str) -> tuple[float, float]:
    """최근 window 내 질문 비중(0~1), 최신 신선도(0~1) 반환.
    sort='date'면 인덱스 기반 폴백을 허용한다."""
    if not items:
        return 0.0, 0.0
    recent, newest_age = 0, 9999
    sort_by_date = (sort == "date")
    for idx, it in enumerate(items):
        age = _estimate_age_days(it, idx, len(items), sort_by_date)
        if age is None:
            continue
        newest_age = min(newest_age, age)
        if age <= window_days:
            recent += 1
    vol = recent / len(items)
    fresh = math.exp(-newest_age / 30.0) if newest_age < 9999 else 0.0
    return vol, fresh


def _estimate_age_days(
    item: dict, idx: int, total: int, sort_by_date: bool
) -> int | None:
    """게시일 → 추정 일수. 우선순위:
    1) item.postdate (YYYYMMDD) — kin API 응답이 제공할 때.
    2) title/description 안의 'YYYY.MM.DD' 패턴.
    3) sort=date 호출이면 위치 기반 프록시(상위일수록 최근).
       1주차 PoC에서 (1)(2)가 채워지는지 실측 후 (3)을 줄이거나 제거.
    원문 문장 자체는 저장하지 않는다 — 추출된 날짜 정수만 사용."""
    today = dt.date.today()

    pd = item.get("postdate")
    if isinstance(pd, str) and len(pd) == 8 and pd.isdigit():
        try:
            d = dt.date(int(pd[:4]), int(pd[4:6]), int(pd[6:8]))
            return max(0, (today - d).days)
        except ValueError:
            pass

    for field in ("title", "description"):
        text = item.get(field) or ""
        m = _DATE_RE.search(text)
        if m:
            try:
                d = dt.date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                return max(0, (today - d).days)
            except ValueError:
                continue

    if sort_by_date and total > 0:
        # 위치 프록시: 0번 항목을 오늘로, 마지막 항목을 30일 전쯤으로 선형 매핑.
        # 실제 분포와 다를 수 있어 (1)(2)가 잡히는 즉시 자동으로 밀려난다.
        return int(round(30 * idx / max(1, total - 1)))

    return None


def cluster_fit(candidate: str, seeds: list[str], aliases: list[str]) -> float:
    text = candidate
    if any(s in text or text in s for s in seeds):
        return 1.0
    if any(a in text for a in aliases):
        return 0.6
    return 0.3


def slugify(text: str) -> str:
    return "-".join(text.split())[:60]


def _norm(text: str) -> str:
    """슬러그 의미비교용 정규화 — 하이픈/공백 제거."""
    return text.replace("-", "").replace(" ", "")


def is_covered(slug: str, cluster: str, covered: dict[str, set[str]]) -> bool:
    """후보가 같은 클러스터에서 이미 발행됐거나 의미상 포함되는가.
    발행 슬러그는 시드보다 구체적이라(예: '마이너스통장-한도-금리') 시드형
    후보('마이너스통장')는 그 부분 문자열이다. 정확 매칭만 하던 구버전
    dup_penalty가 이런 후보를 전부 놓쳐 큐가 기발행 주제로만 가득 차던
    문제를 막는다. 같은 클러스터 안에서만 비교한다."""
    cand = _norm(slug)
    if not cand:
        return False
    for pub in covered.get(cluster, ()):
        p = _norm(pub)
        if cand in p or p in cand:
            return True
    return False


# ---------- 파생 질의 마이닝 (Phase 4 진입점) ----------
# kin 질문 '제목'에서 시드와 함께 자주 등장하는 명사형 토큰을 뽑아
# '시드 + 토큰' 롱테일 후보를 만든다. 제목 원문은 버리고 토큰 빈도(집계)만
# 남긴다 — CLAUDE.md 절대 원칙 1(지식iN은 신호로만). 산출물은 짧은 키워드
# 구(句)이지 질문 문장이 아니다.
_TOKEN_RE = re.compile(r"[가-힣]{2,}")
_DERIVE_STOP = {
    "방법", "신청", "얼마", "경우", "관련", "문의", "질문", "궁금", "어떻게",
    "있나요", "하나요", "인가요", "받나요", "되나요", "가능", "지금", "오늘",
    "그리고", "그런데", "혹시", "정도", "이번", "최근", "요즘", "에서", "한테",
}


def derive_queries(items: list[dict], seed: str, max_derived: int) -> list[str]:
    """시드 kin 결과 제목에서 ≥2회 등장한 명사형 토큰을 빈도순으로 뽑아
    '{seed} {token}' 롱테일 후보를 반환. 제목 문장은 보관하지 않는다."""
    seed_tokens = set(_TOKEN_RE.findall(seed))
    freq: dict[str, int] = {}
    for it in items:
        title = it.get("title") or ""        # 태그/엔티티 섞인 짧은 스니펫
        toks = {t for t in _TOKEN_RE.findall(title)
                if t not in _DERIVE_STOP and t not in seed_tokens}
        for t in toks:                        # 제목당 1회만 카운트
            freq[t] = freq.get(t, 0) + 1
    ranked = sorted((t for t, c in freq.items() if c >= 2),
                    key=lambda t: freq[t], reverse=True)
    return [f"{seed} {t}" for t in ranked[:max_derived]]


# ---------- 메인 ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", required=True)
    ap.add_argument("--scoring", required=True)
    ap.add_argument("--published", default=None)
    ap.add_argument("--out", default="topic-queue.json")
    a = ap.parse_args()

    seeds_cfg = yaml.safe_load(open(a.seeds, encoding="utf-8"))
    sc = yaml.safe_load(open(a.scoring, encoding="utf-8"))
    w = sc["weights"]
    s = sc["scanner"]
    published = set()
    if a.published and os.path.exists(a.published):
        published = {l.strip() for l in open(a.published, encoding="utf-8") if l.strip()}
    # 발행 슬러그를 클러스터별로 분해 — 의미 중복 차단용. _published_slugs.txt는
    # '{cluster}/{slug}' 형식이고 발행 슬러그가 시드보다 구체적이다.
    covered: dict[str, set[str]] = {}
    for line in published:
        if "/" in line:
            cl, sl = line.split("/", 1)
            covered.setdefault(cl, set()).add(sl)

    boosts = sc.get("cluster_fit_boost", {})
    max_derived = s.get("max_derived_per_seed", 3)

    queue = []
    for cname, c in seeds_cfg["clusters"].items():
        boost = boosts.get(cname, 1.0)
        scored = []
        seen_slugs: set[str] = set()
        for kw in c["seed"]:
            try:
                series = datalab_trend(kw, s["datalab_lookback_days"])
                items = kin_search(kw, s["kin_display"], s["kin_sort"])
            except Exception as e:
                print(f"[warn] {kw}: {e}", file=sys.stderr)
                continue

            # 시드 + kin 제목에서 마이닝한 롱테일 파생 질의를 함께 후보로.
            # 파생 질의는 자체 kin_search로 실측 신호를 얻는다(트렌드는 미측정).
            candidates = [(kw, series, items)]
            for dq in derive_queries(items, kw, max_derived):
                try:
                    dq_items = kin_search(dq, s["kin_display"], s["kin_sort"])
                except Exception as e:
                    print(f"[warn] {dq}: {e}", file=sys.stderr)
                    continue
                candidates.append((dq, None, dq_items))

            for cand_kw, cand_series, cand_items in candidates:
                slug = slugify(cand_kw)
                if slug in seen_slugs or is_covered(slug, cname, covered):
                    continue  # 큐 내 중복 + 기발행/의미중복 제외
                seen_slugs.add(slug)

                is_seed = cand_series is not None
                tm = trend_momentum(cand_series) if is_seed else 0.0
                vol, fresh = question_volume(
                    cand_items, s["recent_window_days"], s["kin_sort"])
                base_fit = cluster_fit(cand_kw, c["seed"], c.get("aliases", []))
                if not is_seed:
                    base_fit = max(base_fit, 0.6)  # 시드 kin 파생 → 적합 하한
                fit = base_fit * boost             # loan·tax RPM 우선 가중

                score = 100 * (
                    w["trend_momentum"] * tm
                    + w["question_volume"] * vol
                    + w["cluster_fit"] * fit
                    + w["freshness"] * fresh
                )

                scored.append({
                    "cluster": cname,
                    "path": c["path"],
                    "keyword": cand_kw,
                    "slug": slug,
                    "derived": not is_seed,
                    "score": round(score, 2),
                    "signals": {"trend_momentum": round(tm, 3),
                                "question_volume": round(vol, 3),
                                "cluster_fit": round(fit, 3),
                                "freshness": round(fresh, 3)},
                })

        scored.sort(key=lambda x: x["score"], reverse=True)
        queue.extend(scored[: s["top_n_per_cluster"]])

    out = {"generated_at": dt.datetime.utcnow().isoformat() + "Z",
           "count": len(queue), "items": queue}
    json.dump(out, open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(f"wrote {a.out}: {len(queue)} topics")


if __name__ == "__main__":
    main()
