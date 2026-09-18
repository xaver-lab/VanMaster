// Bestätigungsdialog als Funktion:
//   if (await bestaetigen({ titel: 'Aufgabe löschen?', text: '…', gefaehrlich: true })) …
// Angezeigt von <BestaetigungsHost /> (steckt einmal in App.svelte).

export interface Frage {
  titel: string;
  text?: string;
  ja?: string;
  nein?: string;
  gefaehrlich?: boolean;
}

interface OffeneFrage extends Frage {
  antworten: (ja: boolean) => void;
}

class BestaetigungStore {
  aktuell = $state<OffeneFrage | null>(null);

  fragen(frage: Frage): Promise<boolean> {
    this.aktuell?.antworten(false);
    return new Promise((aufloesen) => {
      this.aktuell = {
        ...frage,
        antworten: (ja) => {
          this.aktuell = null;
          aufloesen(ja);
        },
      };
    });
  }
}

export const bestaetigung = new BestaetigungStore();

export function bestaetigen(frage: Frage): Promise<boolean> {
  return bestaetigung.fragen(frage);
}
