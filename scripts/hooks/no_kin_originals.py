#!/usr/bin/env python3
"""PreToolUse 훅 — 지식iN 원문 격리 강제(절대 원칙 1).
에이전트 프롬프트만으로 의존하면 슬립이 가능하므로 config 레벨에서 차단.

발동 조건:
- 도구: Write 또는 Edit
- 대상 파일이 '본문 산출물' 경로일 때만 검사:
    automation/briefs/{cluster}/*.brief.yaml
        (단 example.brief.yaml, _schema.md, _published_slugs.txt 제외)
    src/content/answers/**         ← 작성 에이전트 출력
    public/llms.txt                ← GEO 산출
- 위 경로에 들어가는 새 내용(content / new_string)에서 아래가 발견되면 차단:
    1) 'kin.naver.com' URL
    2) 명시적 '지식iN' / '지식인' / '네이버 지식' 텍스트
    3) 노출 우려 패턴: 'm.kin.naver.com', 'blog.naver.com', 'cafe.naver.com'

CLAUDE.md, .claude/agents/**, compliance/**, scripts/**, 기획서.md 등 메타 파일은
'지식iN'을 자유롭게 언급할 수 있어야 하므로 검사 대상에서 제외한다.

종료 코드:
  0 — 통과
  2 — 차단 (Claude Code가 stderr 메시지를 모델에 다시 주입)
"""
from __future__ import annotations
import json, re, sys

FORBIDDEN_URLS = re.compile(
    r"https?://[^\s)]*?(?:kin\.naver\.com|blog\.naver\.com|cafe\.naver\.com|m\.kin\.naver\.com)",
    re.IGNORECASE,
)
FORBIDDEN_TOKENS = ("지식iN", "지식인", "네이버 지식")

# 시크릿 패턴 — 본문 산출물에 절대 노출되면 안 되는 키 형식
SECRET_PATTERNS = [
    re.compile(r"ca-pub-\d{15,17}"),                       # Google AdSense publisher
    re.compile(r"gho_[A-Za-z0-9]{30,}"),                   # GitHub Personal Access Token
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),                   # GitHub PAT (classic)
    re.compile(r"ghs_[A-Za-z0-9]{30,}"),                   # GitHub Apps secret
    re.compile(r"AKIA[A-Z0-9]{16,}"),                      # AWS Access Key
    re.compile(r"sk-[A-Za-z0-9]{30,}"),                    # OpenAI / Anthropic style
    re.compile(r"AIza[A-Za-z0-9_\-]{30,}"),                # Google API Key
    re.compile(r"NAVER_CLIENT_SECRET\s*[:=]"),             # env-style 노출
    re.compile(r"NAVER_CLIENT_ID\s*[:=]\s*['\"]?[A-Za-z0-9]{10,}"),
    re.compile(r"client_secret\s*[:=]\s*['\"]?[A-Za-z0-9]{10,}", re.IGNORECASE),
]


def _norm(path: str) -> str:
    return path.replace("\\", "/").lower()


_META_BRIEF_BASENAMES = {
    "example.brief.yaml",
    "_schema.md",
    "_published_slugs.txt",
}


def is_protected(path: str) -> bool:
    """본문 산출물 경로면 True. 메타 파일은 False(자유롭게 언급 허용)."""
    p = _norm(path)
    parts = p.split("/")
    basename = parts[-1] if parts else ""
    parent = parts[-2] if len(parts) >= 2 else ""

    # automation/briefs/ 직속 메타 파일은 검사 제외
    if parent == "briefs" and basename in _META_BRIEF_BASENAMES:
        return False

    # automation/briefs/{cluster}/*.brief.yaml — 검수/승인 대상 brief
    if "automation/briefs/" in p and basename.endswith(".brief.yaml"):
        return True
    # src/content/answers/** — 작성 에이전트가 만드는 발행 본문
    if "src/content/answers/" in p:
        return True
    # public/llms.txt — GEO 산출
    if basename == "llms.txt" and parent == "public":
        return True
    return False


def violations(text: str) -> list[str]:
    found: list[str] = []
    if FORBIDDEN_URLS.search(text):
        m = FORBIDDEN_URLS.search(text)
        found.append(f"forbidden URL: {m.group(0)}")
    for tok in FORBIDDEN_TOKENS:
        if tok in text:
            found.append(f"forbidden token: {tok!r}")
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        if m:
            # 실값 stderr 노출 회피 — 패턴 종류만 보고
            found.append(f"secret pattern: {pat.pattern[:40]}...")
    return found


def main() -> None:
    try:
        # 바이트 기반 읽기 — Windows cp949 콘솔에서 '지식iN' 한글이 깨져
        # 차단이 무력화되는 것을 방지 (stdin 텍스트 모드 인코딩 의존 제거).
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8", "replace"))
    except json.JSONDecodeError:
        sys.exit(0)  # 훅 입력이 깨졌으면 통과(다른 안전망에 위임)

    tool = payload.get("tool_name", "")
    if tool not in ("Write", "Edit"):
        sys.exit(0)

    ti = payload.get("tool_input", {}) or {}
    path = ti.get("file_path", "") or ""
    if not is_protected(path):
        sys.exit(0)

    # Write는 content, Edit는 new_string에서 검사
    content = ti.get("content")
    if content is None:
        content = ti.get("new_string", "")
    content = content or ""

    issues = violations(content)
    if not issues:
        sys.exit(0)

    msg = (
        f"BLOCKED by no_kin_originals hook — {path}\n"
        + "\n".join(f"  - {v}" for v in issues)
        + "\n절대 원칙 1 위반: 지식iN 원문/URL은 본문 산출물에 저장 금지. "
          "(CLAUDE.md 참조)"
    )
    print(msg, file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
