// Kleine Helfer für die Teileansicht: Zahlen aus den CSV-Strings lesen,
// Euro formatieren, Status/Priorität-Vokabular (PART_STATUS/PART_PRIO aus
// tools/common.py — eigenes Vokabular, nicht das Status-Enum aus lib/ui,
// das für Aufgaben gilt).

export const TEIL_STATUS: string[] = ['Idee', 'Recherche', 'Entschieden', 'Bestellt', 'Geliefert', 'Verbaut'];

export const TEIL_PRIO: string[] = ['Kritisch', 'Hoch', 'Mittel', 'Nice-to-have'];

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

export function gesamtpreis(t: { preis: string; menge: string }): number {
  const menge = zahl(t.menge) || 1;
  return zahl(t.preis) * menge;
}
