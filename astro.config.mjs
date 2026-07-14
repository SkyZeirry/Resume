import { defineConfig } from 'astro/config';

const isGitHubPages = process.env.GITHUB_ACTIONS === 'true';

export default defineConfig({
  site: 'https://skyzeirry.github.io',
  base: isGitHubPages ? '/Resume/' : '/',
});
