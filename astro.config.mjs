// @ts-check
import { defineConfig } from 'astro/config';

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
  vite: {
    server: {
      // dev 환경에서 한국어 슬러그 디버깅 시 유리
      fs: { strict: true },
    },
  },
});
