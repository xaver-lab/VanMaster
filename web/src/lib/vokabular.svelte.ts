// Erlaubte Werte der Auswahlfelder — kommen mit /api/daten aus tools/common.py,
// damit die Oberfläche kein eigenes Vokabular pflegt. Reaktiv über den Store.
import { store } from './daten.svelte';

function liste(name: string): string[] {
  return store.daten?.vokabular?.[name] ?? [];
}

export const vokabular = {
  get teilStatus() { return liste('teil_status'); },
  get teilPrio() { return liste('teil_prio'); },
  get teilKategorien() { return liste('teil_kategorien'); },
  get einzelteilArt() { return liste('einzelteil_art'); },
  get einzelteilStatus() { return liste('einzelteil_status'); },
  get massquelle() { return liste('massquelle'); },
};
