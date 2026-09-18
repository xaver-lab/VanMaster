// Routing per Hash: #/<ansicht>/<eins>/<zwei> — angelehnt ans alte Dashboard
// (docs/js/bedienung.js). Die Ansichtsnamen entsprechen 1:1 den Punkten in
// der heutigen Navigation (docs/index.html #hauptnav).

export const ANSICHTEN = [
  'start',
  'themen',
  'aufgaben',
  'teile',
  'zuschnitt',
  'medien',
] as const;

export type Ansicht = (typeof ANSICHTEN)[number];

/** Titel + Unterzeile je Ansicht, für die Kopfleiste. */
export const TITEL: Record<Ansicht, [string, string]> = {
  start: ['Start', 'Woran gerade gearbeitet wird'],
  themen: ['Themen', 'Ein Arbeitsraum je Bereich'],
  aufgaben: ['Aufgaben', 'Alles, was noch zu tun ist'],
  teile: ['Teile', 'Stückliste — was gekauft wird'],
  zuschnitt: ['Zuschnitt', 'Einzelteile mit Maßen'],
  medien: ['Medien', 'Bilder und Unterlagen'],
};

export type Route = { ansicht: Ansicht; eins: string; zwei: string };

function istAnsicht(wert: string): wert is Ansicht {
  return (ANSICHTEN as readonly string[]).includes(wert);
}

function ausHash(): Route {
  const roh = decodeURIComponent(location.hash.replace(/^#\/?/, ''));
  const [a = '', eins = '', zwei = ''] = roh.split('/');
  return { ansicht: istAnsicht(a) ? a : 'start', eins, zwei };
}

let route = $state<Route>(ausHash());

/** Aktuelle Route, reaktiv über Runen. */
export const routing = {
  get route() {
    return route;
  },
};

/** Navigiert zu einem Pfad wie "themen/Möbel/aufgaben" (ohne führendes #/). */
export function zu(pfad: string): void {
  const ziel = pfad
    .replace(/^#?\/?/, '')
    .split('/')
    .filter(Boolean)
    .map(encodeURIComponent)
    .join('/');
  location.hash = '/' + ziel;
}

function aktualisieren(): void {
  route = ausHash();
  window.scrollTo({ top: 0 });
}

// Einmalig anmelden — dieses Modul ist ein Singleton (wie bedienung.js).
window.addEventListener('hashchange', aktualisieren);
