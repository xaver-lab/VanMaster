// Suche der Befehlspalette: jedes Wort der Eingabe muss vorkommen (Titel,
// Nebentext oder Kontext). Titeltreffer zählen mehr, Wortanfänge mehr als
// Treffer mitten im Wort. Findet ein Wort nichts, darf es als lose
// Buchstabenfolge im Titel stehen („lcht“ → „Leuchte“), das zählt wenig —
// aber nur, wenn es ohne diesen Notbehelf gar keine Treffer gäbe (siehe
// `suchen`), sonst verdrängt „kabel“ als Folge in „Kinvaro“ echte
// Worttreffer anderer Gruppen aus ihrer Gruppe.

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

// Wert eines echten Worttreffers (Wortanfang, Wortmitte, Nebentext) — 0, wenn
// das Wort so nirgends vorkommt.
function wortWert(wort: string, titel: string, rest: string): number {
  const pos = titel.indexOf(wort);
  if (pos === 0) return 100;
  if (pos > 0) return /[\s\-/(.,]/.test(titel[pos - 1]) ? 70 : 50;
  if (rest.includes(wort)) return 25;
  return 0;
}

// Wert des Notbehelfs: lose Buchstabenfolge im Titel, zählt wenig.
function loseWert(wort: string, titel: string): number {
  return wort.length >= 3 && folge(wort, titel) ? 8 : 0;
}

interface Bewertung {
  e: Eintrag;
  wert: number;
}

// Bewertet alle Einträge gegen die Suchwörter. `loseErlaubt` steuert, ob ein
// Wort, das nirgends echt vorkommt, ersatzweise als lose Buchstabenfolge
// zählen darf — ein Eintrag braucht dafür mindestens ein Wort, das nur so
// passt, sonst wäre er auch ohne den Notbehelf schon echt getroffen.
function bewerten(alle: Eintrag[], woerter: string[], loseErlaubt: boolean): Bewertung[] {
  const bewertet: Bewertung[] = [];
  for (const e of alle) {
    const titel = normal(e.titel);
    const rest = normal(`${e.neben ?? ''} ${e.kontext ?? ''}`);
    let wert = 0;
    let passt = true;
    for (const w of woerter) {
      let w1 = wortWert(w, titel, rest);
      if (!w1) {
        w1 = loseErlaubt ? loseWert(w, titel) : 0;
        if (!w1) {
          passt = false;
          break;
        }
      }
      wert += w1;
    }
    if (!passt) continue;
    // ganzer Titel getroffen: ganz nach oben
    if (titel === woerter.join(' ')) wert += 200;
    bewertet.push({ e, wert: wert - titel.length / 100 });
  }
  bewertet.sort((a, b) => b.wert - a.wert);
  return bewertet;
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
    // Schwelle: „genug echte Worttreffer“ heißt hier mindestens einer. Lose
    // Buchstabenfolgen kommen erst dazu, wenn die Suche sonst ganz leer
    // bliebe — dann lieber ein schwacher Treffer als keiner.
    let bewertet = bewerten(alle, woerter, false);
    if (!bewertet.length) bewertet = bewerten(alle, woerter, true);
    treffer = bewertet.slice(0, HOECHSTZAHL).map((b) => b.e);
  }
  // Gruppen in der Reihenfolge ihres besten Treffers
  const reihe = woerter.length ? [...new Set(treffer.map((e) => e.art))] : ARTEN;
  return reihe
    .map((art) => ({ art, eintraege: treffer.filter((e) => e.art === art) }))
    .filter((g) => g.eintraege.length);
}
