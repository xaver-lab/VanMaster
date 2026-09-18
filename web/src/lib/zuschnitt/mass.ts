// Maß- und Mengen-Hilfen für Einzelteile (Felder sind Strings — Komma oder
// Punkt, wie im Formular getippt). Rein fürs Anzeigen/Summieren im Web;
// die Wahrheit über gültige Zahlen liegt im Kern (tools/bauteile.py).

import type { EinzelteilAntwort } from '../api-typen';

export function zahl(wert: string | undefined | null, standard = 0): number {
  if (!wert) return standard;
  const n = Number(String(wert).replace(',', '.').trim());
  return Number.isFinite(n) ? n : standard;
}

export function massText(e: EinzelteilAntwort): string {
  const teile = [e.laenge_mm, e.breite_mm, e.dicke_mm].filter((t) => zahl(t) > 0);
  return teile.length ? teile.join(' × ') + ' mm' : '—';
}

const LAUFMETER_ARTEN = new Set(['Leiste', 'Kantholz', 'Rohr', 'Kabel']);

export function flaeche(e: EinzelteilAntwort): number {
  if (LAUFMETER_ARTEN.has(e.art)) return 0;
  const l = zahl(e.laenge_mm);
  const b = zahl(e.breite_mm);
  if (!l || !b) return 0;
  return (l * b * zahl(e.anzahl, 1)) / 1_000_000;
}

export function laufmeter(e: EinzelteilAntwort): number {
  if (!LAUFMETER_ARTEN.has(e.art)) return 0;
  return (zahl(e.laenge_mm) * zahl(e.anzahl, 1)) / 1000;
}
