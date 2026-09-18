// Suche der Befehlspalette: jedes Wort der Eingabe muss vorkommen (Titel,
// Nebentext oder Kontext). Titeltreffer zählen mehr, Wortanfänge mehr als
// Treffer mitten im Wort. Findet ein Wort nichts, darf es als lose
// Buchstabenfolge im Titel stehen („lcht“ → „Leuchte“), das zählt wenig.

import { ARTEN, type Eintrag } from './quellen';

export const HOECHSTZAHL = 50;

export function normal(text: string): string {
  return text
    .toLowerCase()
    .replace(/ß/g, 'ss')
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '');
}

function folge(nadel: string, heu: string): boolean {
  let i = 0;
  for (const z of heu) if (z === nadel[i]) i++;
  return i === nadel.length;
}

function wortWert(wort: string, titel: string, rest: string): number {
  const pos = titel.indexOf(wort);
  if (pos === 0) return 100;
  if (pos > 0) return /[\s\-/(.,]/.test(titel[pos - 1]) ? 70 : 50;
  if (rest.includes(wort)) return 25;
  if (wort.length >= 3 && folge(wort, titel)) return 8;
  return 0;
}

export interface Gruppe {
  art: Eintrag['art'];
  eintraege: Eintrag[];
}

export function suchen(alle: Eintrag[], eingabe: string): Gruppe[] {
  const woerter = normal(eingabe).split(/\s+/).filter(Boolean);
  let treffer: Eintrag[];
  if (!woerter.length) {
    treffer = alle.filter((e) => e.art === 'Befehl' || e.art === 'Ansicht');
  } else {
    const bewertet: { e: Eintrag; wert: number }[] = [];
    for (const e of alle) {
      const titel = normal(e.titel);
      const rest = normal(`${e.neben ?? ''} ${e.kontext ?? ''}`);
      let wert = 0;
      for (const w of woerter) {
        const w1 = wortWert(w, titel, rest);
        if (!w1) {
          wert = 0;
          break;
        }
        wert += w1;
      }
      // ganzer Titel getroffen: ganz nach oben
      if (wert && titel === woerter.join(' ')) wert += 200;
      if (wert) bewertet.push({ e, wert: wert - titel.length / 100 });
    }
    bewertet.sort((a, b) => b.wert - a.wert);
    treffer = bewertet.slice(0, HOECHSTZAHL).map((b) => b.e);
  }
  // Gruppen in der Reihenfolge ihres besten Treffers
  const reihe = woerter.length ? [...new Set(treffer.map((e) => e.art))] : ARTEN;
  return reihe
    .map((art) => ({ art, eintraege: treffer.filter((e) => e.art === art) }))
    .filter((g) => g.eintraege.length);
}
