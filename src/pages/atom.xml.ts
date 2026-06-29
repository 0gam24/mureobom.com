/* 동적 Atom 1.0 피드 — 발행된 모든 answers 글 최신순. 빌더는 src/lib/feeds.ts 공용. */
import type { APIRoute } from "astro";
import { loadItems, atomBody, SITE_TITLE, SITE_DESC } from "../lib/feeds";

export const GET: APIRoute = async ({ site }) => {
  if (!site) {
    return new Response("site is not set in astro.config.mjs; Atom unavailable", { status: 500 });
  }
  const siteUrl = site.toString().replace(/\/$/, "");
  const items = await loadItems(site);
  const body = atomBody(items, {
    siteUrl,
    feedUrl: `${siteUrl}/atom.xml`,
    title: SITE_TITLE,
    subtitle: SITE_DESC,
  });
  return new Response(body, {
    headers: { "Content-Type": "application/atom+xml; charset=utf-8" },
  });
};
