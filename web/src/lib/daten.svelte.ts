// Datenschicht im Browser (UMBAU.md Phase 5).
//
// Modus wird beim Start erkannt: `/api/daten` erreichbar → "server"
// (Schreibzugriff, SSE); sonst `./data.json` → "statisch" (nur lesen).
//
// Sperre: Solange eine Schreibanfrage läuft, ist `beschaeftigt` gesetzt und
// weitere Schreibaufrufe werden sofort abgewiesen (nicht in eine Reihe
// gestellt) — einfacher, und im Web bearbeitet man ohnehin ein Feld nach
// dem anderen; eine Warteschlange wäre hier nur Komplexität ohne Nutzen.

import type {
  AbschnittAnfrage,
  AufgabeAnlegenAnfrage,
  AufgabePatchAnfrage,
  DatenAntwort,
  EinzelteilAnlegenAnfrage,
  EinzelteilPatchAnfrage,
  KonfliktAntwort,
  KopfAnfrage,
  SchreibErfolg,
  TeilAnlegenAnfrage,
  TeilPatchAnfrage,
} from './api-typen';
import { toasts } from './toasts.svelte';

export type Modus = 'server' | 'statisch';
export type Verbindung = 'verbindet' | 'verbunden' | 'getrennt' | 'aus';

interface SseEreignis {
  dateien: { datei: string; version: string }[];
  quelle: 'web' | 'extern';
}

const DATEI_TEILE = 'data/parts.csv';
const DATEI_BAUTEILE = 'data/bauteile.csv';

function bereichsdatei(bereich: string): string {
  return `vault/Bereiche/${bereich}.md`;
}

function istKonflikt(wert: unknown): wert is KonfliktAntwort {
  return (
    !!wert &&
    typeof wert === 'object' &&
    'fehler' in wert &&
    'version_aktuell' in wert
  );
}

class DatenStore {
  daten = $state<DatenAntwort | null>(null);
  modus = $state<Modus | null>(null);
  ladeFehler = $state<string | null>(null);
  laedt = $state(true);
  beschaeftigt = $state(false);
  verbindung = $state<Verbindung>('aus');

  darfSchreiben = $derived(this.modus === 'server');

  #es: EventSource | null = null;
  #wiederverbindenMs = 1000;
  #wiederverbindenTimer: ReturnType<typeof setTimeout> | null = null;

  async init(): Promise<void> {
    this.laedt = true;
    this.ladeFehler = null;
    const serverDaten = await this.#versuchServer();
    if (serverDaten) {
      this.modus = 'server';
      this.daten = serverDaten;
      this.laedt = false;
      this.#sseVerbinden();
      return;
    }
    const statischeDaten = await this.#versuchStatisch();
    if (statischeDaten) {
      this.modus = 'statisch';
      this.daten = statischeDaten;
      this.laedt = false;
      this.verbindung = 'aus';
      return;
    }
    this.laedt = false;
    this.ladeFehler =
      'Keine Daten gefunden — weder /api/daten noch data.json erreichbar.';
  }

  async #versuchServer(): Promise<DatenAntwort | null> {
    try {
      const antwort = await fetch('/api/daten');
      if (!antwort.ok) return null;
      return (await antwort.json()) as DatenAntwort;
    } catch {
      return null;
    }
  }

  async #versuchStatisch(): Promise<DatenAntwort | null> {
    try {
      const antwort = await fetch('./data.json');
      if (!antwort.ok) return null;
      return (await antwort.json()) as DatenAntwort;
    } catch {
      return null;
    }
  }

  async #neuLaden(): Promise<void> {
    const frisch = await this.#versuchServer();
    if (frisch) this.daten = frisch;
  }

  #sseVerbinden(): void {
    if (this.#es) this.#es.close();
    this.verbindung = 'verbindet';
    const es = new EventSource('/api/live');
    this.#es = es;

    es.addEventListener('open', () => {
      this.verbindung = 'verbunden';
      this.#wiederverbindenMs = 1000;
    });

    es.addEventListener('aenderung', (ev) => {
      const nachricht = ev as MessageEvent<string>;
      let daten: SseEreignis;
      try {
        daten = JSON.parse(nachricht.data) as SseEreignis;
      } catch {
        return;
      }
      void this.#neuLaden();
      if (daten.quelle === 'extern') {
        const namen = daten.dateien.map((d) => d.datei).join(', ');
        toasts.info(`Datei wurde außerhalb geändert: ${namen}`);
      }
    });

    es.addEventListener('error', () => {
      this.verbindung = 'getrennt';
      es.close();
      if (this.#wiederverbindenTimer) clearTimeout(this.#wiederverbindenTimer);
      this.#wiederverbindenTimer = setTimeout(() => {
        if (this.modus === 'server') this.#sseVerbinden();
      }, this.#wiederverbindenMs);
      this.#wiederverbindenMs = Math.min(this.#wiederverbindenMs * 2, 30000);
    });
  }

  #version(datei: string): string {
    return this.daten?.versionen[datei] ?? '';
  }

  // -------------------------------------------------------- Schreibkern

  async #anfrage(
    methode: string,
    pfad: string,
    datei: string,
    koerper?: unknown,
  ): Promise<SchreibErfolg | null> {
    if (!this.darfSchreiben) {
      toasts.fehler('Nur Lesemodus — keine Änderung möglich.');
      return null;
    }
    if (this.beschaeftigt) {
      toasts.fehler('Bitte warten, es läuft noch eine Anfrage.');
      return null;
    }
    this.beschaeftigt = true;
    try {
      const antwort = await fetch(pfad, {
        method: methode,
        headers: koerper ? { 'Content-Type': 'application/json' } : undefined,
        body: koerper ? JSON.stringify(koerper) : undefined,
      });
      const inhalt = await antwort.json().catch(() => null);

      if (antwort.status === 409 && istKonflikt(inhalt)) {
        this.#versionUebernehmen(inhalt.datei, inhalt.version_aktuell);
        if (inhalt.stand !== undefined && inhalt.stand !== null) {
          void this.#neuLaden();
        }
        toasts.konflikt(
          `Konflikt: „${inhalt.datei}“ wurde inzwischen anderswo geändert. Stand übernommen.`,
        );
        return null;
      }
      if (!antwort.ok) {
        const text =
          (inhalt && typeof inhalt === 'object' && 'fehler' in inhalt
            ? String((inhalt as { fehler: unknown }).fehler)
            : null) ?? `Fehler ${antwort.status}`;
        toasts.fehler(text);
        return null;
      }

      const erfolg = inhalt as SchreibErfolg;
      this.#versionUebernehmen(erfolg.datei, erfolg.version);
      return erfolg;
    } catch {
      toasts.fehler('Anfrage fehlgeschlagen — keine Verbindung zum Server.');
      return null;
    } finally {
      this.beschaeftigt = false;
    }
  }

  #versionUebernehmen(datei: string, version: string): void {
    if (!this.daten) return;
    this.daten.versionen[datei] = version;
  }

  // ------------------------------------------------------------ Aufgaben

  async aufgabeAnlegen(
    felder: Omit<AufgabeAnlegenAnfrage, 'version'>,
  ): Promise<string | null> {
    const version = this.#version(bereichsdatei(felder.bereich));
    const erfolg = await this.#anfrage('POST', '/api/aufgaben', bereichsdatei(felder.bereich), {
      ...felder,
      version,
    });
    if (erfolg) await this.#neuLaden();
    return erfolg?.id ?? null;
  }

  async aufgabePatch(
    aufgabeId: string,
    datei: string,
    felder: Omit<AufgabePatchAnfrage, 'version'>,
  ): Promise<boolean> {
    const version = this.#version(datei);
    const erfolg = await this.#anfrage(
      'PATCH',
      `/api/aufgaben/${encodeURIComponent(aufgabeId)}`,
      datei,
      { ...felder, version },
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }

  async aufgabeLoeschen(aufgabeId: string, datei: string): Promise<boolean> {
    const version = this.#version(datei);
    const erfolg = await this.#anfrage(
      'DELETE',
      `/api/aufgaben/${encodeURIComponent(aufgabeId)}?version=${encodeURIComponent(version)}`,
      datei,
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }

  // ------------------------------------------------------------ Bereiche

  async abschnittSetzen(bereich: string, abschnitt: string, text: string): Promise<boolean> {
    const datei = bereichsdatei(bereich);
    const version = this.#version(datei);
    const anfrage: AbschnittAnfrage = { text, version };
    const erfolg = await this.#anfrage(
      'PUT',
      `/api/bereiche/${encodeURIComponent(bereich)}/abschnitte/${encodeURIComponent(abschnitt)}`,
      datei,
      anfrage,
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }

  async kopfSetzen(bereich: string, feld: string, wert: unknown): Promise<boolean> {
    const datei = bereichsdatei(bereich);
    const version = this.#version(datei);
    const anfrage: KopfAnfrage = { feld, wert, version };
    const erfolg = await this.#anfrage(
      'PATCH',
      `/api/bereiche/${encodeURIComponent(bereich)}/kopf`,
      datei,
      anfrage,
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }

  // --------------------------------------------------------------- Teile

  async teilAnlegen(felder: Record<string, unknown>): Promise<string | null> {
    const version = this.#version(DATEI_TEILE);
    const anfrage: TeilAnlegenAnfrage = { felder, version };
    const erfolg = await this.#anfrage('POST', '/api/teile', DATEI_TEILE, anfrage);
    if (erfolg) await this.#neuLaden();
    return erfolg?.id ?? null;
  }

  async teilPatch(teilId: string, feld: string, wert: string): Promise<boolean> {
    const version = this.#version(DATEI_TEILE);
    const anfrage: TeilPatchAnfrage = { feld, wert, version };
    const erfolg = await this.#anfrage(
      'PATCH',
      `/api/teile/${encodeURIComponent(teilId)}`,
      DATEI_TEILE,
      anfrage,
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }

  async teilLoeschen(teilId: string): Promise<boolean> {
    const version = this.#version(DATEI_TEILE);
    const erfolg = await this.#anfrage(
      'DELETE',
      `/api/teile/${encodeURIComponent(teilId)}?version=${encodeURIComponent(version)}`,
      DATEI_TEILE,
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }

  // --------------------------------------------------------- Einzelteile

  async einzelteilAnlegen(felder: Record<string, unknown>): Promise<string | null> {
    const version = this.#version(DATEI_BAUTEILE);
    const anfrage: EinzelteilAnlegenAnfrage = { felder, version };
    const erfolg = await this.#anfrage('POST', '/api/einzelteile', DATEI_BAUTEILE, anfrage);
    if (erfolg) await this.#neuLaden();
    return erfolg?.id ?? null;
  }

  async einzelteilPatch(einzelteilId: string, feld: string, wert: string): Promise<boolean> {
    const version = this.#version(DATEI_BAUTEILE);
    const anfrage: EinzelteilPatchAnfrage = { feld, wert, version };
    const erfolg = await this.#anfrage(
      'PATCH',
      `/api/einzelteile/${encodeURIComponent(einzelteilId)}`,
      DATEI_BAUTEILE,
      anfrage,
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }

  async einzelteilLoeschen(einzelteilId: string): Promise<boolean> {
    const version = this.#version(DATEI_BAUTEILE);
    const erfolg = await this.#anfrage(
      'DELETE',
      `/api/einzelteile/${encodeURIComponent(einzelteilId)}?version=${encodeURIComponent(version)}`,
      DATEI_BAUTEILE,
    );
    if (erfolg) await this.#neuLaden();
    return !!erfolg;
  }
}

export const store = new DatenStore();
