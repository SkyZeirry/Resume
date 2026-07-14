import { defineConfig } from 'astro/config';

const isDevelopment = process.env.NODE_ENV === 'development';

export default defineConfig({
  site: 'https://skyzeirry.github.io',
  base: isDevelopment ? '/' : '/Resume/',
});
