import { defineConfig } from 'astro/config';

export default defineConfig({
  site: 'https://x-cache-1.github.io',
  base: '/x-cache-1',
  trailingSlash: 'always',
  i18n: {
    locales: ['en', 'zh'],
    defaultLocale: 'zh',
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
