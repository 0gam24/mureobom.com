/* 동적 sitemap.xml — 홈 + 4 카테고리 랜딩 + 모든 answers 글
 * Astro.site(astro.config.mjs의 site 옵션)이 절대 URL 베이스.
 * `npm install @astrojs/sitemap` 통합 플러그인을 쓰는 대신 의존성 0의 자체 라우트로 운영. */
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

const CLUSTERS = ["tax", "support", "loan", "insurance"] as const;

function toW3CDate(d: Date | string): string {
  return new Date(d).toISOString().slice(0, 10); // YYYY-MM-DD
}

export const GET: APIRoute = async ({ site }) => {
  if (!site) {
    return new Response(
      "site is not set in astro.config.mjs; sitemap unavailable",
      { status: 500 }
    );
  }

  const posts = await getCollection("answers");
  const today = toW3CDate(new Date());

  type Entry = { loc: string; lastmod: string; changefreq: string; priority: string };
  const entries: Entry[] = [
    { loc: new URL("/", site).toString(), lastmod: today, changefreq: "daily",   priority: "1.0" },
    ...CLUSTERS.map((c) => ({
      loc: new URL(`/${c}/`, site).toString(),
      lastmod: today,
      changefreq: "daily",
      priority: "0.8",
    })),
    /* 정적 고지 페이지 — AdSense 정책·신뢰 신호용 (소개·개인정보처리방침) */
    { loc: new URL("/about/",   site).toString(), lastmod: today, changefreq: "yearly", priority: "0.3" },
    { loc: new URL("/privacy/", site).toString(), lastmod: today, changefreq: "yearly", priority: "0.3" },
    ...posts.map((p) => ({
      loc: new URL(`/${p.data.cluster}/${p.slug}/`, site).toString(),
      lastmod: toW3CDate(p.data.updated),
      changefreq: "monthly",
      priority: "0.7",
    })),
  ];

  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
    entries
      .map(
        (e) =>
          `  <url><loc>${e.loc}</loc><lastmod>${e.lastmod}</lastmod>` +
          `<changefreq>${e.changefreq}</changefreq><priority>${e.priority}</priority></url>`
      )
      .join("\n") +
    `\n</urlset>\n`;

  return new Response(body, {
    headers: { "Content-Type": "application/xml; charset=utf-8" },
  });
};
