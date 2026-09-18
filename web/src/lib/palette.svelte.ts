// Befehlspalette (Strg+K) — kommt in Phase 8, bis dahin nur ein Hinweis.
import { toasts } from './toasts.svelte';

export function paletteOeffnen(): void {
  toasts.info('Befehlspalette folgt später (Strg+K).');
}
