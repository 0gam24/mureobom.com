#!/usr/bin/env node
/**
 * 글별 대표 이미지(hero) WebP 생성 — public/img/{slug}.webp (1200×900, 4:3)
 *
 * 왜 WebP 4:3인가
 *  - Google Article 구조화 데이터·검색 썸네일 권장: 가로 1200px 이상, 16:9·4:3·1:1 비율.
 *    인포그래픽 viewBox 비율이 1.04~1.9 사이라 4:3 캔버스에 레터박스가 가장 손실이 적다.
 *  - 네이버 og:image 요건: 150×150 초과·5,000B 이상·가로:세로 3:1 이내·문서별 고유 이미지.
 *  - Google 이미지 가이드: 로고·텍스트 카드 대신 "페이지를 대표하는" 이미지 → 본문
 *    인포그래픽(public/diagrams/{slug}.svg)을 래스터화해 대표 이미지로 쓴다.
 *
 * 동작
 *  1. src/content/answers/*.md 스캔 (--slug 지정 시 해당 글만)
 *  2. 본문이 참조하는 첫 /diagrams/*.svg 를 resvg-js로 래스터화해 sharp로 1200×900
 *     크림 캔버스에 합성 (인포그래픽이 없는 초기 글은 제목·핵심 불릿 카드 SVG를 생성해
 *     렌더 — 폴백)
 *  3. public/img/{slug}.webp 저장 (quality 82)
 *  4. frontmatter에 `hero: "/img/{slug}.webp"` 삽입 (이미 있으면 유지)
 *
 * 폰트: scripts/fonts/*.ttf(OFL)를 resvg에 직접 로드, 시스템 폰트 미사용 —
 *      OS 폰트에 의존하지 않아 로컬 Windows·클라우드 Linux 출력이 동일하다.
 *
 * 실행
 *   node scripts/gen_post_hero.mjs --slug {slug}      # 신규 1편 (publish-daily가 호출)
 *   node scripts/gen_post_hero.mjs --all              # 전체 (webp가 없는 글만)
 *   node scripts/gen_post_hero.mjs --all --force      # 전체 강제 재생성
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import sharp from 'sharp';
import { Resvg } from '@resvg/resvg-js';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

/* 폰트 — resvg에 동봉 TTF를 명시적으로 넘기고 시스템 폰트는 끈다.
 * (sharp/librsvg의 fontconfig는 Windows에서 지정 디렉토리를 무시하고 OS 폰트로
 *  대체하는 것이 실측됐고, Linux 컨테이너엔 한글 폰트가 없어 tofu가 난다.
 *  resvg-js는 fontFiles만으로 family·weight를 정확히 매칭한다 — 2026-09-02 검증.) */
const FONT_DIR = path.join(ROOT, 'scripts', 'fonts');
const FONT_FILES = fs.readdirSync(FONT_DIR).filter((f) => f.endsWith('.ttf')).map((f) => path.join(FONT_DIR, f));
if (!FONT_FILES.length) { console.error('scripts/fonts/*.ttf 없음'); process.exit(2); }
const FONT_OPTS = {
  fontFiles: FONT_FILES,
  loadSystemFonts: false,
  defaultFontFamily: 'IBM Plex Sans KR',
  sansSerifFamily: 'IBM Plex Sans KR',
  serifFamily: 'Gowun Batang',
};

const W = 1200, H = 900;
const PAPER = '#FBF7F0', INK = '#1A2B2A', SOFT = '#4A5856',
      FAINT = '#8A938F', TEAL = '#0E7C72', LINE = '#E3DCCF';
const ANSWERS = path.join(ROOT, 'src', 'content', 'answers');
const PUBLIC  = path.join(ROOT, 'public');
const OUT     = path.join(PUBLIC, 'img');
const CLUSTER_LABEL = { tax: '세금', support: '정부지원금', loan: '대출·신용', insurance: '보험·연금' };

/* ── CLI ── */
const argv = process.argv.slice(2);
const slugs = [];
let force = false, all = false;
for (let i = 0; i < argv.length; i++) {
  if (argv[i] === '--slug') slugs.push(argv[++i]);
  else if (argv[i] === '--force') force = true;
  else if (argv[i] === '--all') all = true;
}
if (!slugs.length && !all) {
  console.error('usage: node scripts/gen_post_hero.mjs --slug {slug} | --all [--force]');
  process.exit(2);
}

/* ── frontmatter (간이) ── */
const FM_RE = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/;
function parseFm(text) {
  const m = FM_RE.exec(text);
  if (!m) return { fm: null, data: {}, body: text };
  const fm = m[1];
  const data = {};
  const scalar = (k) => {
    const r = new RegExp(`^${k}:\\s*(.+?)\\s*$`, 'm').exec(fm);
    return r ? r[1].replace(/^["']|["']$/g, '') : undefined;
  };
  data.title = scalar('title') ?? '';
  data.cluster = scalar('cluster') ?? '';
  data.summary = scalar('summary') ?? '';
  const kp = /^keyPoints:\s*\n((?:\s+-\s.*\n?)+)/m.exec(fm);
  data.keyPoints = kp
    ? kp[1].split('\n').map((l) => l.replace(/^\s+-\s*/, '').replace(/^["']|["']$/g, '').trim()).filter(Boolean)
    : [];
  /* CRLF 파일("---\r\n")도 안전하게 — 여는 구분자 길이를 실측한다 */
  const openLen = /^---\r?\n/.exec(text)[0].length;
  const eol = text.includes('\r\n') ? '\r\n' : '\n';
  return { fm, data, body: text.slice(m[0].length), fmStart: openLen, fmEnd: openLen + fm.length, eol };
}

function esc(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
/* 한글 폭 근사(글자당 1em, 영문·숫자 ~0.55em)로 줄바꿈 */
function wrap(text, fontPx, maxW, maxLines) {
  const w = (ch) => (/[ㄱ-힝]/.test(ch) ? 1 : /[A-Z0-9%]/.test(ch) ? 0.66 : 0.5) * fontPx;
  const lines = []; let cur = '', curW = 0;
  for (const ch of text) {
    const cw = w(ch);
    if (curW + cw > maxW && cur) { lines.push(cur); cur = ch; curW = cw; }
    else { cur += ch; curW += cw; }
  }
  if (cur) lines.push(cur);
  if (lines.length > maxLines) {
    lines.length = maxLines;
    lines[maxLines - 1] = lines[maxLines - 1].slice(0, -1) + '…';
  }
  return lines;
}

/* 인포그래픽 없는 글의 폴백 카드 — 제목 + 핵심 불릿(또는 요약). 브랜드 팔레트만 사용 */
function fallbackSvg({ title, cluster, summary, keyPoints }) {
  const titleLines = wrap(title, 60, 1000, 3);
  /* keyPoints가 있으면 최대 3개(각 2줄), 없으면 summary 한 덩어리(최대 4줄) */
  const bullets = keyPoints.length
    ? keyPoints.slice(0, 3).map((b) => wrap(b, 30, 940, 2))
    : [wrap(summary, 30, 940, 4)];
  let y = 200;
  const tSvg = titleLines
    .map((l, i) => `<text x="100" y="${y + i * 78}" font-family="'Gowun Batang', serif" font-size="60" font-weight="700" fill="${INK}">${esc(l)}</text>`)
    .join('');
  y += titleLines.length * 78 + 30;
  let bSvg = '';
  for (const lines of bullets) {
    bSvg += `<circle cx="112" cy="${y - 10}" r="6" fill="${TEAL}"/>`;
    lines.forEach((l, i) => {
      bSvg += `<text x="136" y="${y + i * 42}" font-family="'IBM Plex Sans KR', sans-serif" font-size="30" fill="${SOFT}">${esc(l)}</text>`;
    });
    y += lines.length * 42 + 22;
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}">
  <rect width="${W}" height="${H}" fill="${PAPER}"/>
  <rect width="16" height="${H}" fill="${TEAL}"/>
  <text x="100" y="120" font-family="'IBM Plex Sans KR', sans-serif" font-size="30" font-weight="700" fill="${TEAL}">${esc(CLUSTER_LABEL[cluster] ?? cluster)}</text>
  ${tSvg}${bSvg}
  <line x1="100" y1="${H - 110}" x2="${W - 100}" y2="${H - 110}" stroke="${LINE}" stroke-width="2"/>
  <text x="100" y="${H - 58}" font-family="'IBM Plex Sans KR', sans-serif" font-size="28" font-weight="700" fill="${TEAL}">mureobom.com</text>
  <text x="${W - 100}" y="${H - 58}" text-anchor="end" font-family="'IBM Plex Sans KR', sans-serif" font-size="22" fill="${FAINT}">공식 1차 출처로 확인한 답</text>
</svg>`;
}

/* SVG → (resvg) PNG, 1200×900 안에 맞춤 → (sharp) 크림 캔버스 중앙 합성 → WebP */
function rasterize(svgText) {
  const probe = new Resvg(svgText, { font: FONT_OPTS });
  const { width: sw, height: sh } = probe;                  // viewBox 기준 원본 크기
  const fit = (sw / sh) >= (W / H)
    ? { mode: 'width', value: W }
    : { mode: 'height', value: H };
  return new Resvg(svgText, { fitTo: fit, font: FONT_OPTS, background: PAPER }).render().asPng();
}

async function renderToCanvas(svgText) {
  const inner = rasterize(svgText);
  return sharp({ create: { width: W, height: H, channels: 3, background: PAPER } })
    .composite([{ input: inner, gravity: 'centre' }])
    .webp({ quality: 82, effort: 5 })
    .toBuffer();
}

function firstDiagram(body) {
  const re = /\]\((\/diagrams\/[^)\s]+\.svg)\)|src="(\/diagrams\/[^"\s]+\.svg)"/g;
  let m;
  while ((m = re.exec(body)) !== null) {
    const rel = decodeURI(m[1] ?? m[2]);
    const abs = path.join(PUBLIC, rel);
    if (fs.existsSync(abs)) return abs;
  }
  return null;
}

function ensureHeroField(mdPath, text, parsed, slug) {
  if (/^hero:/m.test(parsed.fm)) return false;
  const line = `hero: "/img/${slug}.webp"`;
  const eol = parsed.eol;
  let fm = parsed.fm;
  /* `[^\r\n]*`로 캡처해 CR을 그룹에 포함시키지 않는다 (CRLF 파일 안전) */
  if (/^image:[^\r\n]*/m.test(fm)) fm = fm.replace(/^(image:[^\r\n]*)/m, `$1${eol}${line}`);
  else if (/^disclaimer:[^\r\n]*/m.test(fm)) fm = fm.replace(/^(disclaimer:[^\r\n]*)/m, `$1${eol}${line}`);
  else fm = fm.replace(/\s*$/, '') + `${eol}${line}`;
  fs.writeFileSync(mdPath, text.slice(0, parsed.fmStart) + fm + text.slice(parsed.fmEnd), 'utf8');
  return true;
}

/* ── main ── */
fs.mkdirSync(OUT, { recursive: true });
const files = all
  ? fs.readdirSync(ANSWERS).filter((f) => f.endsWith('.md')).sort()
  : slugs.map((s) => `${s}.md`);

let made = 0, skipped = 0, fallback = 0, failed = 0;
for (const f of files) {
  const mdPath = path.join(ANSWERS, f);
  const slug = f.slice(0, -3);
  if (!fs.existsSync(mdPath)) { console.error(`  x 없음: ${mdPath}`); failed++; continue; }
  const text = fs.readFileSync(mdPath, 'utf8');
  const parsed = parseFm(text);
  if (!parsed.fm) { console.error(`  x frontmatter 없음: ${f}`); failed++; continue; }
  const out = path.join(OUT, `${slug}.webp`);
  if (fs.existsSync(out) && !force) {
    ensureHeroField(mdPath, text, parsed, slug);
    skipped++;
    continue;
  }
  try {
    const dia = firstDiagram(parsed.body);
    let svg;
    if (dia) svg = fs.readFileSync(dia, 'utf8');
    else { svg = fallbackSvg(parsed.data); fallback++; }
    const webp = await renderToCanvas(svg);
    if (webp.length < 5000) throw new Error(`too small (${webp.length}B) — 네이버 og:image 5,000B 하한`);
    fs.writeFileSync(out, webp);
    const added = ensureHeroField(mdPath, text, parsed, slug);
    made++;
    console.log(`  ok ${slug}.webp ${(webp.length / 1024).toFixed(0)}KB${dia ? '' : ' (fallback card)'}${added ? ' +hero:' : ''}`);
  } catch (e) {
    failed++;
    console.error(`  x ${slug}: ${e.message}`);
  }
}
console.log(`\n  hero: ${made} generated (${fallback} fallback cards), ${skipped} existing, ${failed} failed -> public/img/`);
if (failed) process.exit(1);
