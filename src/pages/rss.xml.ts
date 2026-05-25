/* 동적 RSS 2.0 피드 — 발행된 모든 answers 글을 최신순으로 노출.
 * sitemap.xml.ts와 동일하게 의존성 0의 자체 라우트 (`@astrojs/rss` 미사용).
 * 주 목적: 네이버 Search Advisor RSS 제출로 색인 가속 (한국 시장 SEO).
 */
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";

const CLUSTER_LABEL: Record<string, string> = {
  tax: "세금",
  support: "정부지원금",
  loan: "대출·신용",
  insurance: "보험·연금",
};

/* RFC822 날짜 (RSS 2.0 표준) */
function toRfc822(d: Date | string): string {
  return new Date(d).toUTCString();
}

/* XML 본문 안전 escape */
function xmlEscape(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export const GET: APIRoute = async ({ site }) => {
  if (!site) {
    return new Response(
      "site is not set in astro.config.mjs; RSS unavailable",
      { status: 500 }
    );
  }

  const posts = (await getCollection("answers"))
    .sort((a, b) => +new Date(b.data.updated) - +new Date(a.data.updated));

  const siteUrl = site.toString().replace(/\/$/, "");
  const feedUrl = `${siteUrl}/rss.xml`;
  const lastBuild = toRfc822(new Date());

  const items = posts.map((p) => {
    const url = `${siteUrl}/${p.data.cluster}/${encodeURIComponent(p.slug)}/`;
    const cluster = CLUSTER_LABEL[p.data.cluster] ?? p.data.cluster;
    return `    <item>
      <title>${xmlEscape(p.data.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${toRfc822(p.data.updated)}</pubDate>
      <category>${xmlEscape(cluster)}</category>
      <description>${xmlEscape(p.data.summary)}</description>
    </item>`;
  }).join("\n");

  const body =
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n` +
    `  <channel>\n` +
    `    <title>물어봄 — 공식 자료 기반 금융·생활 답변</title>\n` +
    `    <link>${siteUrl}/</link>\n` +
    `    <description>세금·정부지원금·대출·보험. 사람들이 많이 묻는 질문을 법령과 정부 자료로 직접 확인해 정리합니다.</description>\n` +
    `    <language>ko</language>\n` +
    `    <atom:link href="${feedUrl}" rel="self" type="application/rss+xml" />\n` +
    `    <lastBuildDate>${lastBuild}</lastBuildDate>\n` +
    items +
    `\n  </channel>\n` +
    `</rss>\n`;

  return new Response(body, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
};
