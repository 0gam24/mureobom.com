/* 동적 RSS 2.0 피드 — 네이버 서치어드바이저 RSS 제출용 (한국 시장 SEO).
 *
 * 네이버 RSS 검증 요건(H/05-02 RSS 및 사이트맵 제출) 준수:
 *  - 각 item의 본문은 "일부가 아닌 전체 공개" → 마크다운 본문을 HTML로 렌더해
 *    <description> CDATA로 포함 (summary만 넣으면 검증 미충족).
 *  - 피드 10MB 미만 → 최신 50건으로 제한. 네이버 공식 입장이 "RSS는 최신 글 창구,
 *    전체 URL은 사이트맵으로"이므로 전체 포함 불필요.
 *  - 모든 URL은 소유확인 도메인과 동일한 절대 URL.
 * 마크다운 렌더는 Astro 내장 @astrojs/markdown-remark 사용 (추가 의존성 0).
 */
import type { APIRoute } from "astro";
import { getCollection } from "astro:content";
import { createMarkdownProcessor } from "@astrojs/markdown-remark";

const CLUSTER_LABEL: Record<string, string> = {
  tax: "세금",
  support: "정부지원금",
  loan: "대출·신용",
  insurance: "보험·연금",
};

const MAX_ITEMS = 50;

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

/* CDATA 안전화 — 본문에 "]]>"가 있으면 CDATA 분할로 이스케이프 */
function cdata(s: string): string {
  return `<![CDATA[${s.replace(/\]\]>/g, "]]]]><![CDATA[>")}]]>`;
}

/* 렌더 HTML의 상대 URL(이미지·내부 링크)을 절대 URL로 — 피드 리더·네이버 수집기 호환 */
function absolutize(html: string, siteUrl: string): string {
  return html
    .replace(/(src|href)="\/(?!\/)/g, `$1="${siteUrl}/`);
}

export const GET: APIRoute = async ({ site }) => {
  if (!site) {
    return new Response(
      "site is not set in astro.config.mjs; RSS unavailable",
      { status: 500 }
    );
  }

  const posts = (await getCollection("answers"))
    .sort((a, b) => +new Date(b.data.updated) - +new Date(a.data.updated))
    .slice(0, MAX_ITEMS);

  const siteUrl = site.toString().replace(/\/$/, "");
  const feedUrl = `${siteUrl}/rss.xml`;

  const processor = await createMarkdownProcessor({ gfm: true });

  const items = await Promise.all(posts.map(async (p) => {
    const url = `${siteUrl}/${p.data.cluster}/${encodeURIComponent(p.slug)}/`;
    const cluster = CLUSTER_LABEL[p.data.cluster] ?? p.data.cluster;
    const rendered = await processor.render(p.body ?? "");
    const bodyHtml = absolutize(String(rendered.code), siteUrl);
    /* 요약 한 문장 + 본문 전문 — 전체 공개 요건 충족 */
    const full = `<p>${xmlEscape(p.data.summary)}</p>\n${bodyHtml}`;
    return `    <item>
      <title>${xmlEscape(p.data.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${toRfc822(p.data.updated)}</pubDate>
      <category>${xmlEscape(cluster)}</category>
      <description>${cdata(full)}</description>
    </item>`;
  }));

  const lastBuild = toRfc822(posts[0]?.data.updated ?? new Date());

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
    items.join("\n") +
    `\n  </channel>\n` +
    `</rss>\n`;

  return new Response(body, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
};
