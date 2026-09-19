// Toasts: Info, Fehler, Konflikt. Blenden sich von selbst wieder aus
// (Konflikt/Fehler länger, weil dort mehr zu lesen ist).

export type ToastArt = 'info' | 'fehler' | 'konflikt';

export interface ToastAktion {
  label: string;
  tun: () => void | Promise<void>;
}

export interface Toast {
  id: number;
  art: ToastArt;
  text: string;
  /** Ein Knopf im Toast, z. B. „Rückgängig". Ausführen schließt den Toast. */
  aktion?: ToastAktion;
}

const DAUER: Record<ToastArt, number> = {
  info: 3500,
  fehler: 6000,
  konflikt: 7000,
};

// Mit Knopf länger stehen lassen — 3,5 Sekunden reichen nicht, um eine
// versehentliche Änderung zu bemerken und zurückzunehmen.
const DAUER_MIT_AKTION = 9000;

let naechsteId = 1;

class ToastStore {
  liste = $state<Toast[]>([]);

  zeigen(art: ToastArt, text: string, aktion?: ToastAktion): void {
    const id = naechsteId++;
    this.liste.push({ id, art, text, aktion });
    setTimeout(() => this.entfernen(id), aktion ? DAUER_MIT_AKTION : DAUER[art]);
  }

  info(text: string, aktion?: ToastAktion): void {
    this.zeigen('info', text, aktion);
  }

  fehler(text: string): void {
    this.zeigen('fehler', text);
  }

  konflikt(text: string): void {
    this.zeigen('konflikt', text);
  }

  entfernen(id: number): void {
    this.liste = this.liste.filter((t) => t.id !== id);
  }
}

export const toasts = new ToastStore();
