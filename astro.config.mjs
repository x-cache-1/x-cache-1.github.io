import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://x-cache.local',
  i18n: {
    locales: ['en', 'zh'],
    defaultLocale: 'en',
    routing: {
      prefixDefaultLocale: true,
      redirectToDefaultLocale: false,
    },
  },
  build: {
    assets: '_assets',
  },
  vite: {
    server: {
      fs: {
        allow: ['..'],
      },
    },
  },
});
