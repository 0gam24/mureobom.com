/* 동적 카테고리별 RSS 2.0 — /{cluster}/rss.xml. 해당 클러스터 글만 최신순.
 * getStaticPaths로 4 클러스터 정적 생성. 빌더는 src/lib/feeds.ts 공용. */
import type { APIRoute } from "astro";
import { loadItems, rssBody, CLUSTERS, CLUSTER_LABEL } from "../../lib/feeds";

export function getStaticPaths() {
  return CLUSTERS.map((c) => ({ params: { cluster: c.id } }));
}

export const GET: APIRoute = async ({ params, site }) => {
  if (!site) {
    return new Response("site is not set in astro.config.mjs; RSS unavailable", { status: 500 });
  }
  const cluster = params.cluster as string;
  const label = CLUSTER_LABEL[cluster] ?? cluster;
  const siteUrl = site.toString().replace(/\/$/, "");
  const items = await loadItems(site, cluster);
  const body = rssBody(items, {
    siteUrl,
    feedUrl: `${siteUrl}/${cluster}/rss.xml`,
    title: `물어봄 ${label} — 공식 자료 기반 답변`,
    description: `${label} 분야의 새 질문답변을 최신순으로 제공합니다.`,
  });
  return new Response(body, {
    headers: { "Content-Type": "application/rss+xml; charset=utf-8" },
  });
};
