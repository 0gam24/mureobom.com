import { defineCollection, z } from "astro:content";

/* 작성 에이전트가 생성하는 발행 글의 프론트매터.
 * brief.yaml의 승인 필드를 그대로 이어받아 일관성 유지.
 * 길이 제약은 Google SEO 권장값 + AdSense 최소 분량(본문은 글 자체에서 검증). */
const answers = defineCollection({
  type: "content",
  schema: z.object({
    /* Google 권장 <title> 50~60자. 제목 + " — 물어봄" 까지 합쳐도 60자 이내 권장. */
    title: z.string().min(10).max(60),
    cluster: z.enum(["tax", "support", "loan", "insurance"]),
    targetQuery: z.string(),
    searchIntent: z.enum(["정보형", "절차형", "거래형"]),
    /* Google 권장 description 50~160자 (SERP 절단 회피 + 정보성).
     * 짧은 답 케이스 허용 위해 min은 30자로 완화. */
    summary: z.string().min(30).max(160),
    updated: z.coerce.date(),
    /* 최초 발행일(선택). JSON-LD datePublished에 사용 — 미지정 시 updated로 폴백.
     * 기존 글 소급 불필요: updated만 있으면 종전 동작 유지. */
    published: z.coerce.date().optional(),
    sources: z.array(z.object({                 // 공식 1차 출처(0건이면 빌드 차단)
      label: z.string(),
      url: z.string().url().optional(),
    })).min(1),
    internalLinks: z.array(z.string()).default([]),
    faq: z.array(z.object({                     // FAQPage JSON-LD 자동 생성용
      q: z.string(),
      a: z.string(),
    })).default([]),
    disclaimer: z.boolean().default(true),      // 일반정보 고지 노출
    /* OG/Twitter Card 이미지(선택). 절대경로 권장(`/og/{slug}.png` 또는 외부 URL).
     * 미지정 시 [slug].astro가 `/og-default.png` 사용. */
    image: z.string().optional(),
  }),
});

export const collections = { answers };
