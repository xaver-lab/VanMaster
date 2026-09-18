// Toast-Liste mit Runen. Hört per `beobachten()` auf die Datenschicht, damit
// deren Meldungen (Erfolg/Fehler beim Schreiben, Konflikt) automatisch
// erscheinen — wie das alte `toast()` in docs/js/grund.js.

import { beobachten } from './daten.svelte';

export type ToastArt = 'info' | 'erfolg' | 'fehler';
export type Toast = { id: number; text: string; art: ToastArt };

let liste = $state<Toast[]>([]);
let zaehler = 0;

export const toasts = {
  get liste() {
    return liste;
  },
};

/** Zeigt einen Toast; blendet ihn nach einigen Sekunden von selbst aus. */
export function zeigen(text: string, art: ToastArt = 'info'): void {
  const id = ++zaehler;
  liste = [...liste, { id, text, art }];
  const dauer = art === 'fehler' ? 6000 : 3500;
  setTimeout(() => entfernen(id), dauer);
}

/** Blendet einen Toast vorzeitig aus (z. B. per Schließen-Knopf). */
export function entfernen(id: number): void {
  liste = liste.filter((t) => t.id !== id);
}

// Meldungen der Datenschicht automatisch als Toast weiterreichen.
beobachten((m) => zeigen(m.text, m.art));
