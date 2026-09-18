// Tastenkürzel wie im alten Dashboard (docs/js/bedienung.js): Ziffern 1..n
// wechseln die Ansicht, „t" schaltet das Thema um, Strg/Cmd+K und „/" öffnen
// die Befehlspalette (kommt erst in Phase 8, daher hier nur ein Einhängepunkt),
// Escape ruft eine mitgegebene Funktion. Keine Kürzel, während in einem
// Textfeld getippt wird.

import { ANSICHTEN, zu } from './routing.svelte';
import { umschalten } from './thema.svelte';

type Optionen = {
  paletteOeffnen?: () => void;
  escape?: () => void;
};

/** Meldet die Tastenkürzel an, gibt eine Abmeldefunktion zurück. */
export function tastenAnmelden(opts: Optionen = {}): () => void {
  function inFeld(ziel: EventTarget | null): boolean {
    const el = ziel as HTMLElement | null;
    if (!el) return false;
    if (el.isContentEditable) return true;
    return /^(INPUT|SELECT|TEXTAREA)$/.test(el.tagName);
  }

  function handler(e: KeyboardEvent): void {
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      opts.paletteOeffnen?.();
      return;
    }
    if (e.key === 'Escape') {
      opts.escape?.();
      return;
    }
    if (inFeld(e.target)) return;
    if (e.key === '/') {
      e.preventDefault();
      opts.paletteOeffnen?.();
      return;
    }
    if (e.key.toLowerCase() === 't') {
      umschalten();
      return;
    }
    const nummer = Number(e.key);
    if (Number.isInteger(nummer) && nummer >= 1 && nummer <= ANSICHTEN.length) {
      zu(ANSICHTEN[nummer - 1]);
    }
  }

  window.addEventListener('keydown', handler);
  return () => window.removeEventListener('keydown', handler);
}
