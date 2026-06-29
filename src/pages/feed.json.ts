/* 동적 JSON Feed 1.1 — 발행된 모든 answers 글 최신순. 빌더는 src/lib/feeds.ts 공용. */
import type { APIRoute } from "astro";
import { loadItems, jsonBody, SITE_TITLE, SITE_DESC } from "../lib/feeds";

export const GET: APIRoute = async ({ site }) => {
  if (!site) {
    return new Response("site is not set in astro.config.mjs; JSON Feed unavailable", { status: 500 });
  }
  const siteUrl = site.toString().replace(/\/$/, "");
  const items = await loadItems(site);
  const body = jsonBody(items, {
    siteUrl,
    feedUrl: `${siteUrl}/feed.json`,
    title: SITE_TITLE,
    description: SITE_DESC,
  });
  return new Response(body, {
    headers: { "Content-Type": "application/feed+json; charset=utf-8" },
  });
};
