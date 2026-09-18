import { svelte } from '@sveltejs/vite-plugin-svelte';
import { defineConfig } from 'vite';

// base: './' — relative Pfade in index.html, damit dieselbe dist/ sowohl
// unter '/' (tools/server/start.py liefert web/dist an der Wurzel aus) als
// auch später unter einem Unterpfad auf GitHub Pages (Projektseite,
// https://<user>.github.io/<repo>/) läuft, ohne den Build für die beiden
// Ziele unterschiedlich konfigurieren zu müssen.
export default defineConfig({
  plugins: [svelte()],
  base: './',
  build: {
    outDir: 'dist',
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8765',
        changeOrigin: true,
      },
    },
  },
});
