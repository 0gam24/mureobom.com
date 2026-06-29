/* 피드 공용 헬퍼 — RSS 2.0 / Atom 1.0 / JSON Feed 1.1 빌더 + 클러스터 메타.
 * 의존성 0 (sitemap.xml.ts·rss.xml.ts와 동일 기조, `@astrojs/rss` 미사용).
 * /feeds/ 허브와 각 피드 라우트가 공유한다.
 */
import { getCollection } from "astro:content";

export const SITE_TITLE = "물어봄 — 공식 자료 기반 금융·생활 답변";
export const SITE_DESC =
  "세금·정부지원금·대출·보험. 사람들이 많이 묻는 질문을 법령과 정부 자료로 직접 확인해 정리합니다.";

/* IA 4 클러스터 — 라벨/이모지 단일 정의(허브·피드 공용). */
export const CLUSTERS = [
  { id: "tax", label: "세금", emoji: "🧾" },
  { id: "support", label: "정부지원금", emoji: "🏛️" },
  { id: "loan", label: "대출·신용", emoji: "🏦" },
  { id: "insurance", label: "보험·연금", emoji: "🛡️" },
] as const;

export const CLUSTER_LABEL: Record<string, string> = Object.fromEntries(
  CLUSTERS.map((c) => [c.id, c.label])
);

export function xmlEscape(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export function rfc822(d: Date | string): string {
  return new Date(d).toUTCString();
}
export function iso(d: Date | string): string {
  return new Date(d).toISOString();
}

export type FeedItem = {
  title: string;
  summary: string;
  url: string;
  cluster: string;
  clusterLabel: string;
  updated: Date;
};

/* 발행 글 → 피드 아이템(최신순). cluster 지정 시 해당 클러스터만. */
export async function loadItems(site: URL, cluster?: string): Promise<FeedItem[]> {
  const siteUrl = site.toString().replace(/\/$/, "");
  const posts = (await getCollection("answers"))
    .filter((p) => !cluster || p.data.cluster === cluster)
    .sort((a, b) => +new Date(b.data.updated) - +new Date(a.data.updated));
  return posts.map((p) => ({
    title: p.data.title,
    summary: p.data.summary,
    url: `${siteUrl}/${p.data.cluster}/${encodeURIComponent(p.slug)}/`,
    cluster: p.data.cluster,
    clusterLabel: CLUSTER_LABEL[p.data.cluster] ?? p.data.cluster,
    updated: new Date(p.data.updated),
  }));
}

type ChannelMeta = { siteUrl: string; feedUrl: string; title: string; description: string };

export function rssBody(items: FeedItem[], o: ChannelMeta): string {
  const itemsXml = items
    .map(
      (it) => `    <item>
      <title>${xmlEscape(it.title)}</title>
      <link>${it.url}</link>
      <guid isPermaLink="true">${it.url}</guid>
      <pubDate>${rfc822(it.updated)}</pubDate>
      <category>${xmlEscape(it.clusterLabel)}</category>
      <description>${xmlEscape(it.summary)}</description>
    </item>`
    )
    .join("\n");
  return (
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n` +
    `  <channel>\n` +
    `    <title>${xmlEscape(o.title)}</title>\n` +
    `    <link>${o.siteUrl}/</link>\n` +
    `    <description>${xmlEscape(o.description)}</description>\n` +
    `    <language>ko</language>\n` +
    `    <atom:link href="${o.feedUrl}" rel="self" type="application/rss+xml" />\n` +
    `    <lastBuildDate>${rfc822(items[0]?.updated ?? new Date())}</lastBuildDate>\n` +
    itemsXml +
    `\n  </channel>\n` +
    `</rss>\n`
  );
}

export function atomBody(
  items: FeedItem[],
  o: { siteUrl: string; feedUrl: string; title: string; subtitle: string }
): string {
  const updated = iso(items[0]?.updated ?? new Date());
  const entries = items
    .map(
      (it) => `  <entry>
    <title>${xmlEscape(it.title)}</title>
    <link href="${it.url}" />
    <id>${it.url}</id>
    <updated>${iso(it.updated)}</updated>
    <category term="${it.cluster}" label="${xmlEscape(it.clusterLabel)}" />
    <summary>${xmlEscape(it.summary)}</summary>
  </entry>`
    )
    .join("\n");
  return (
    `<?xml version="1.0" encoding="UTF-8"?>\n` +
    `<feed xmlns="http://www.w3.org/2005/Atom" xml:lang="ko">\n` +
    `  <title>${xmlEscape(o.title)}</title>\n` +
    `  <subtitle>${xmlEscape(o.subtitle)}</subtitle>\n` +
    `  <link href="${o.feedUrl}" rel="self" />\n` +
    `  <link href="${o.siteUrl}/" />\n` +
    `  <id>${o.feedUrl}</id>\n` +
    `  <updated>${updated}</updated>\n` +
    entries +
    `\n</feed>\n`
  );
}

export function jsonBody(items: FeedItem[], o: ChannelMeta): string {
  return JSON.stringify(
    {
      version: "https://jsonfeed.org/version/1.1",
      title: o.title,
      home_page_url: `${o.siteUrl}/`,
      feed_url: o.feedUrl,
      description: o.description,
      language: "ko",
      items: items.map((it) => ({
        id: it.url,
        url: it.url,
        title: it.title,
        summary: it.summary,
        content_text: it.summary,
        date_modified: iso(it.updated),
        tags: [it.clusterLabel],
      })),
    },
    null,
    2
  );
}
