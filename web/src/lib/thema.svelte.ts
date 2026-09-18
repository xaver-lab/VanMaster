// Hell/Dunkel: Systemvorgabe als Voreinstellung, Wahl gemerkt in localStorage,
// `data-thema` am <html> — wie bisher in docs/js/grund.js (dort: `thema`).

export type Thema = 'hell' | 'dunkel';

const SCHLUESSEL = 'thema';

function systemThema(): Thema {
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dunkel' : 'hell';
  } catch {
    return 'dunkel';
  }
}

function gemerkt(): Thema | null {
  try {
    const w = localStorage.getItem(SCHLUESSEL);
    return w === 'hell' || w === 'dunkel' ? w : null;
  } catch {
    return null;
  }
}

let thema = $state<Thema>(gemerkt() ?? systemThema());

export const themaZustand = {
  get wert() {
    return thema;
  },
};

function anwenden(): void {
  document.documentElement.dataset.thema = thema;
}

/** Beim Start einmal aufrufen (main.ts): setzt data-thema am <html>. */
export function themaStarten(): void {
  anwenden();
}

/** Schaltet zwischen hell und dunkel um, merkt die Wahl. */
export function umschalten(): void {
  thema = thema === 'hell' ? 'dunkel' : 'hell';
  try {
    localStorage.setItem(SCHLUESSEL, thema);
  } catch {
    // Privater Modus o. Ä. — Wahl gilt dann nur für diese Sitzung.
  }
  anwenden();
}
