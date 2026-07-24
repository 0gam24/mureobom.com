/* 동적 sitemap.xml — 홈 + 4 카테고리 랜딩 + 정적 페이지 + 모든 answers 글.
 * Astro.site(astro.config.mjs의 site 옵션)이 절대 URL 베이스.
 * `npm install @astrojs/sitemap` 통합 플러그인을 쓰는 대신 의존성 0의 자체 라우트로 운영.
 *
 * Google sitemaps/build-sitemap.md 준수 사항:
 *  - <priority>/<changefreq>는 Google이 무시하므로 생성하지 않는다.
 *  - <lastmod>는 "마지막 중요 업데이트"만 — 홈·카테고리는 포함 글의 최신 updated,
 *    변경 추적이 없는 정적 페이지(about·privacy·feeds)는 lastmod 자체를 생략.
 *    (매 빌드 today를 찍는 lastmod 인플레이션은 Google의 lastmod 신뢰를 깎는다.)
 *  - <loc>은 percent-encoding된 절대 URL(new URL이 처리) + XML 엔티티 escape.
 *  - 이미지 sitemap 확장: 각 글의 본문 인포그래픽(/diagrams/*.svg)을 <image:image>로
 *    노출해 Google 이미지 검색 색인을 돕는다 (sitemaps/image-sitemaps.md).
 */
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

const CLUSTERS = ["tax", "support", "loan", "insurance"] as const;

function toW3CDate(d: Date | string): string {
  return new Date(d).toISOString().slice(0, 10); // YYYY-MM-DD
}

function xmlEscape(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/* 본문 마크다운에서 다이어그램 참조 추출 — ![alt](/diagrams/{slug}.svg) */
function extractDiagrams(body: string): string[] {
  const out: string[] = [];
  const re = /\]\((\/diagrams\/[^)\s]+\.svg)\)/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(body)) !== null) {
    if (!out.includes(m[1])) out.push(m[1]);
  }
  return out;
}

export const GET: APIRoute = async ({ site }) => {
  if (!site) {
    return new Response(
      "site is not set in astro.config.mjs; sitemap unavailable",
      { status: 500 }
    );
  }

  const posts = await getCollection("answers");

  /* 클러스터별·전체 최신 updated — 랜딩/홈 lastmod의 정직한 근거 */
  const latestOf = (cluster?: string): string | undefined => {
    const pool = cluster ? posts.filter((p) => p.data.cluster === cluster) : posts;
    if (!pool.length) return undefined;
    const max = pool.reduce((acc, p) =>
      +new Date(p.data.updated) > +new Date(acc.data.updated) ? p : acc
    );
    return toW3CDate(max.data.updated);
  };

  type Entry = { loc: string; lastmod?: string; images?: string[] };
  const entries: Entry[] = [
    { loc: new URL("/", site).toString(), lastmod: latestOf() },
    ...CLUSTERS.map((c) => ({
      loc: new URL(`/${c}/`, site).toString(),
      lastmod: latestOf(c),
    })),
    /* 정적 고지 페이지 — AdSense 정책·신뢰 신호용. 변경 추적이 없어 lastmod 생략 */
    { loc: new URL("/about/",   site).toString() },
    { loc: new URL("/privacy/", site).toString() },
    { loc: new URL("/feeds/",   site).toString() },
    ...posts.map((p) => ({
      loc: new URL(`/${p.data.cluster}/${p.slug}/`, site).toString(),
      lastmod: toW3CDate(p.data.updated),
      images: extractDiagrams(p.body ?? "").map((path) =>
        new URL(encodeURI(path), site).toString()
      ),
    })),
  ];

  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"` +
    ` xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n` +
    entries
      .map((e) => {
        const lastmod = e.lastmod ? `<lastmod>${e.lastmod}</lastmod>` : "";
        const images = (e.images ?? [])
          .map((img) => `<image:image><image:loc>${xmlEscape(img)}</image:loc></image:image>`)
          .join("");
        return `  <url><loc>${xmlEscape(e.loc)}</loc>${lastmod}${images}</url>`;
      })
      .join("\n") +
    `\n</urlset>\n`;

  return new Response(body, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
};
