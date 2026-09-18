// Toasts: Info, Fehler, Konflikt. Blenden sich von selbst wieder aus
// (Konflikt/Fehler länger, weil dort mehr zu lesen ist).

export type ToastArt = 'info' | 'fehler' | 'konflikt';

export interface Toast {
  id: number;
  art: ToastArt;
  text: string;
}

const DAUER: Record<ToastArt, number> = {
  info: 3500,
  fehler: 6000,
  konflikt: 7000,
};

let naechsteId = 1;

class ToastStore {
  liste = $state<Toast[]>([]);

  zeigen(art: ToastArt, text: string): void {
    const id = naechsteId++;
    this.liste.push({ id, art, text });
    setTimeout(() => this.entfernen(id), DAUER[art]);
  }

  info(text: string): void {
    this.zeigen('info', text);
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
