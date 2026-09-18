// Zahlen deutsch formatieren (Komma, Tausenderpunkt) mit fester Nachkommazahl.

export function dezimal(n: number, stellen = 1): string {
  return n.toLocaleString('de-DE', { minimumFractionDigits: stellen, maximumFractionDigits: stellen });
}
