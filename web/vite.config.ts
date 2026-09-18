import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [svelte()],
  // GitHub Pages liefert die App auch unter einem Unterpfad statisch aus.
  base: './',
  server: {
    proxy: {
      // camper serve läuft unter 127.0.0.1:8765, inkl. SSE (/api/live) —
      // Proxy darf die Antwort nicht puffern, sonst kommen die Ereignisse
      // nicht laufend an.
      '/medien': { target: 'http://127.0.0.1:8765', changeOrigin: true },
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
        ws: true,
        configure(proxy) {
          proxy.on('proxyRes', (proxyRes) => {
            delete proxyRes.headers['content-encoding'];
          });
        },
      },
    },
  },
});
