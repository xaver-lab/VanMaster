// Befehlspalette (Strg+K) — Zustand. Die Taste selbst hört Schiene.svelte ab,
// die Anzeige steckt in palette/Palette.svelte (in App.svelte eingehängt).

class PaletteStore {
  offen = $state(false);
}

export const palette = new PaletteStore();

export function paletteOeffnen(): void {
  palette.offen = true;
}

export function paletteSchliessen(): void {
  palette.offen = false;
}
