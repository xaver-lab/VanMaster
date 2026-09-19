// Hash-Routing wie im alten Dashboard: #/ansicht/param1/param2 —
// Parameter sind erlaubt und werden einzeln weitergereicht.

export const ANSICHTEN = ['start', 'bereiche', 'aufgaben', 'teile', 'zuschnitt', 'medien', 'bilanz'] as const;
// Erreichbar per Adresse, aber nicht in der Navigation und ohne Zifferntaste.
export const NEBENANSICHTEN = ['muster'] as const;
export type Ansicht = (typeof ANSICHTEN)[number] | (typeof NEBENANSICHTEN)[number];

export interface Route {
  ansicht: Ansicht;
  parameter: string[];
}

function istAnsicht(wert: string): wert is Ansicht {
  return ([...ANSICHTEN, ...NEBENANSICHTEN] as readonly string[]).includes(wert);
}

function ausHash(): Route {
  // Erst zerlegen, dann je Stück dekodieren — `gehe()` kodiert jedes Stück
  // einzeln. Würde der ganze Hash vorab dekodiert, zerfiele ein Dateiname
  // mit `/` oder `%` in zwei Parameter.
  const roh = location.hash.replace(/^#\/?/, '');
  const teile = roh.split('/').filter(Boolean).map((stueck) => {
    try {
      return decodeURIComponent(stueck);
    } catch {
      return stueck;
    }
  });
  let [erste, ...rest] = teile;
  if (erste === 'themen') erste = 'bereiche'; // alte Adressen aus dem Dashboard
  const ansicht = erste && istAnsicht(erste) ? erste : 'start';
  return { ansicht, parameter: rest };
}

class RouterStore {
  route = $state<Route>(ausHash());

  constructor() {
    window.addEventListener('hashchange', () => {
      this.route = ausHash();
    });
  }

  gehe(ansicht: Ansicht, ...parameter: string[]): void {
    const stueck = [ansicht, ...parameter].map(encodeURIComponent);
    location.hash = '/' + stueck.join('/');
  }
}

export const router = new RouterStore();

export const TITEL: Record<Ansicht, string> = {
  start: 'Start',
  bereiche: 'Bereiche',
  aufgaben: 'Aufgaben',
  teile: 'Teile',
  zuschnitt: 'Zuschnitt',
  medien: 'Medien',
  bilanz: 'Bilanz',
  muster: 'Muster',
};
