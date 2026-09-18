// Hell/Dunkel — Standard ist die Systemeinstellung, Wahl des Nutzers wird
// gemerkt (gleicher localStorage-Schlüssel wie im alten Dashboard, damit
// eine schon getroffene Wahl übernommen wird).

export type Thema = 'hell' | 'dunkel';

const SCHLUESSEL = 'vm.thema';

function merken(wert: Thema): void {
  try {
    localStorage.setItem(SCHLUESSEL, wert);
  } catch {
    /* egal — dann eben nicht gemerkt */
  }
}

function gemerkt(): Thema | null {
  try {
    const wert = localStorage.getItem(SCHLUESSEL);
    return wert === 'hell' || wert === 'dunkel' ? wert : null;
  } catch {
    return null;
  }
}

function systemThema(): Thema {
  try {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dunkel' : 'hell';
  } catch {
    return 'hell';
  }
}

class ThemeStore {
  aktuell = $state<Thema>(gemerkt() ?? systemThema());

  constructor() {
    this.anwenden();
  }

  private anwenden(): void {
    document.documentElement.dataset.thema = this.aktuell;
  }

  setzen(thema: Thema): void {
    this.aktuell = thema;
    this.anwenden();
    merken(thema);
  }

  umschalten(): void {
    this.setzen(this.aktuell === 'hell' ? 'dunkel' : 'hell');
  }
}

export const theme = new ThemeStore();
