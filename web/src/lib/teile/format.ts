// Kleine Helfer für die Teileansicht: Zahlen aus den CSV-Strings lesen,
// Euro formatieren, Ton je Teile-Status. Die Wertelisten selbst kommen aus
// lib/vokabular.svelte.ts (eigenes Vokabular, nicht das Aufgaben-Enum).

export const TEIL_STATUS_TON: Record<string, 'neutral' | 'signal' | 'info' | 'gut'> = {
  Idee: 'neutral',
  Recherche: 'neutral',
  Entschieden: 'signal',
  Bestellt: 'signal',
  Geliefert: 'info',
  Verbaut: 'gut',
};

export function zahl(wert: string | undefined | null): number {
  const n = parseFloat(String(wert ?? '').replace(',', '.'));
  return Number.isFinite(n) ? n : 0;
}

export const euro = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

/** Gesamtpreis als Euro-Text; ohne Preis ein Strich statt „0 €“. */
export function preisText(t: { preis: string; menge: string }): string {
  return zahl(t.preis) ? euro.format(gesamtpreis(t)) : '—';
}

export function gesamtpreis(t: { preis: string; menge: string }): number {
  const menge = zahl(t.menge) || 1;
  return zahl(t.preis) * menge;
}
