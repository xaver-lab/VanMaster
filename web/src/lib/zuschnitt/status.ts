// Status-Wortschatz der Einzelteile (bauteile.csv) — bewusst getrennt vom
// Aufgaben-Status aus lib/ui/status.ts: andere Werte, anderer Lebenslauf
// (tools/common.py: BAUTEIL_STATUS = Idee, Geplant, Zugeschnitten, Verbaut).
// Ein unbekannter/leerer Wert bekommt den neutralen Ton.

export const BAUTEIL_STATUS_TON: Record<string, 'neutral' | 'info' | 'signal' | 'gut'> = {
  Idee: 'neutral',
  Geplant: 'info',
  Zugeschnitten: 'signal',
  Verbaut: 'gut',
};

export function bauteilStatusTon(status: string): 'neutral' | 'info' | 'signal' | 'gut' {
  return BAUTEIL_STATUS_TON[status] ?? 'neutral';
}
