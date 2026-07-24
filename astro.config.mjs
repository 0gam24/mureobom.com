// @ts-check
import { defineConfig } from 'astro/config';
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

/**
 * rehype 플러그인 — 본문 마크다운 이미지(인포그래픽 SVG)에 성능 속성 주입.
 *  - loading="lazy" decoding="async": 본문 중반의 다이어그램은 뷰포트 밖 → 지연 로드
 *    (Google javascript/lazy-loading.md — 브라우저 내장 lazy는 색인 안전).
 *  - width/height: public/diagrams/*.svg의 viewBox 실측값 — CLS 방지(C1 §5-1).
 *  빌드 타임 1회 파일 읽기, 미존재 파일은 조용히 스킵(빌드 안 깨짐).
 */
function rehypeImagePerf() {
  /** @type {Map<string, {width:number,height:number}|null>} */
  const dims = new Map();
  /** @param {string} src */
  function svgSize(src) {
    if (dims.has(src)) return dims.get(src);
    /** @type {{width:number,height:number}|null} */
    let size = null;
    try {
      const file = join(process.cwd(), 'public', decodeURI(src));
      const txt = readFileSync(file, 'utf-8');
      const vb = txt.match(
        /viewBox\s*=\s*["']\s*[\d.+-]+[\s,]+[\d.+-]+[\s,]+([\d.]+)[\s,]+([\d.]+)/i
      );
      if (vb) size = { width: Math.round(+vb[1]), height: Math.round(+vb[2]) };
      else {
        const w = txt.match(/<svg[^>]*\swidth=["']?([\d.]+)/i);
        const h = txt.match(/<svg[^>]*\sheight=["']?([\d.]+)/i);
        if (w && h) size = { width: Math.round(+w[1]), height: Math.round(+h[1]) };
      }
    } catch { /* 파일 없음 — 속성 주입만 생략 */ }
    dims.set(src, size);
    return size;
  }
  /** @param {any} node @param {(n:any)=>void} fn */
  function visit(node, fn) {
    fn(node);
    for (const c of node.children ?? []) visit(c, fn);
  }
  return /** @param {any} tree */ (tree) => {
    visit(tree, (node) => {
      if (node.type === 'element' && node.tagName === 'img') {
        const props = node.properties ?? (node.properties = {});
        if (props.loading == null) props.loading = 'lazy';
        if (props.decoding == null) props.decoding = 'async';
        const src = String(props.src ?? '');
        if (src.startsWith('/diagrams/') && props.width == null) {
          const size = svgSize(src);
          if (size) { props.width = size.width; props.height = size.height; }
        }
      }
    });
  };
}

/**
 * 물어봄 Astro 설정.
 * site: sitemap.xml.ts 및 Base.astro canonical/OG 절대 URL 생성에 필수.
 *       도메인 변경 시 본 값 + WORKFLOW.md §6.5의 검색엔진 등록 정보 동시 갱신.
 */
export default defineConfig({
  site: 'https://mureobom.com',
  output: 'static',
  trailingSlash: 'always',     // /tax/{slug}/ — sitemap.xml.ts와 일치
  build: {
    format: 'directory',        // /about/index.html 식, trailing slash 호환
  },
  markdown: {
    rehypePlugins: [rehypeImagePerf],
  },
  vite: {
    server: {
      // dev 환경에서 한국어 슬러그 디버깅 시 유리
      fs: { strict: true },
    },
  },
});
