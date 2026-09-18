// Sortierung der Bereichsübersicht — dieselben Regeln wie
// tools/bereiche.py (schluessel/sortiere) und docs/js/themen.js
// (SORT_SCHLUESSEL). Eigenständig hier, weil es kein API-Feld dafür gibt —
// Bereiche kommen aus /api/daten bereits sortiert nach "baustellen"
// (build.py), der Wechsler in der Übersicht sortiert nur um.

import type { AufgabeAntwort, BereichAntwort } from '../api-typen';

export const SORTIERUNGEN = ['baustellen', 'phase', 'name'] as const;
export type Sortierung = (typeof SORTIERUNGEN)[number];

export const SORT_WORT: Record<Sortierung, string> = {
  baustellen: 'Baustellen zuerst',
  phase: 'Bauabschnitt',
  name: 'A–Z',
};

export const STANDARD_SORTIERUNG: Sortierung = 'baustellen';

// Baustellen zuerst: woran gearbeitet wird, vor dem, was noch ansteht.
const STATUS_RANG: Record<string, number> = { 'in-arbeit': 0, geplant: 1, fertig: 2 };
const OHNE_PHASE = 999; // kein `phase:` im Kopf → hinten, aber nicht weg.
const ERLEDIGT = new Set(['erledigt', 'verworfen']);

export interface Fortschritt {
  fertig: number;
  gesamt: number;
}

/** Fortschritt eines Bereichs — nur Blätter (Aufgaben ohne Unterpunkte)
 * zählen, wie tools/tasks.py:fortschritt(). */
export function fortschritt(aufgaben: AufgabeAntwort[], bereich: string): Fortschritt {
  const blaetter = aufgaben.filter((a) => a.bereich === bereich && !a.kinder?.length);
  return {
    fertig: blaetter.filter((a) => ERLEDIGT.has(a.status)).length,
    gesamt: blaetter.length,
  };
}

function offen(f: Fortschritt): number {
  return Math.max(f.gesamt - f.fertig, 0);
}

function vergleiche(a: (string | number)[], b: (string | number)[]): number {
  for (let i = 0; i < a.length; i++) {
    if (a[i] < b[i]) return -1;
    if (a[i] > b[i]) return 1;
  }
  return 0;
}

export function sortiere(
  bereiche: BereichAntwort[],
  aufgaben: AufgabeAntwort[],
  art: Sortierung,
): BereichAntwort[] {
  const schluessel = (b: BereichAntwort): (string | number)[] => {
    const f = fortschritt(aufgaben, b.name);
    const name = b.name.toLowerCase();
    if (art === 'name') return [name];
    if (art === 'phase') {
      return [b.phase ?? OHNE_PHASE, STATUS_RANG[b.status] ?? 1, -offen(f), name];
    }
    return [STATUS_RANG[b.status] ?? 1, -offen(f), name];
  };
  return [...bereiche].sort((a, b) => vergleiche(schluessel(a), schluessel(b)));
}
