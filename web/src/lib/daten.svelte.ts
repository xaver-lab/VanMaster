// Datenschicht im Browser (UMBAU.md Phase 5). Lädt /api/daten (Servermodus)
// oder data.json neben index.html (statischer Build, Lesemodus), hört über
// live.ts auf SSE und stellt die Schreibfunktionen des Servers bereit.
// Importiert nichts aus dem Rahmen — Rückmeldungen gehen nur über
// `beobachten` (Toasts sind Sache des Rahmens).
import { apiGet, apiPost, apiPatch, apiPut, apiDelete, ApiFehler } from './api';
import type {
  DatenAntwort as Daten,
  SchreibErfolg,
} from './api-typen';

export type Modus = 'server' | 'statisch';
export type Konflikt = { datei: string; meldung: string; stand: unknown };
export type Meldung = { art: 'info' | 'erfolg' | 'fehler'; text: string };

// Bekannte Ablage laut CLAUDE.md — Schlüssel in `versionen`, falls sich der
// genaue Pfad je ändern sollte, greift die Suche in `_version` als Rückfall
// über den Dateinamen.
const TEIL_DATEI = 'data/parts.csv';
const EINZELTEIL_DATEI = 'data/bauteile.csv';

let _wert = $state<Daten | null>(null);
let _laedt = $state(true);
let _fehler = $state<string | null>(null);
let _schreibt = $state(false);
let _konflikt = $state<Konflikt | null>(null);
let _modus = $state<Modus>('server');

const _beobachter = new Set<(m: Meldung) => void>();

/** Für live.ts: Meldungen (SSE-Hinweise) über denselben Kanal ausgeben wie
 * die Schreibfunktionen hier. Kein Teil der festen Schnittstelle, aber vom
 * selben Modul exportiert, damit live.ts nicht selbst einen zweiten Kanal
 * aufmacht. */
export function meldungSenden(m: Meldung): void {
  for (const f of _beobachter) f(m);
}

export function beobachten(f: (m: Meldung) => void): () => void {
  _beobachter.add(f);
  return () => _beobachter.delete(f);
}

export const daten = {
  get wert() {
    return _wert;
  },
  get laedt() {
    return _laedt;
  },
  get fehler() {
    return _fehler;
  },
  get schreibt() {
    return _schreibt;
  },
  get konflikt() {
    return _konflikt;
  },
  get modus() {
    return _modus;
  },
  get lesemodus() {
    return _modus === 'statisch';
  },
};

/** (Neu) laden — erst /api/daten, bei Fehlschlag data.json neben
 * index.html (statischer Build auf GitHub Pages, Lesemodus). */
export async function laden(): Promise<void> {
  _laedt = true;
  _fehler = null;
  try {
    _wert = await apiGet<Daten>('/api/daten');
    _modus = 'server';
  } catch {
    try {
      const basis = import.meta.env.BASE_URL ?? './';
      const antwort = await fetch(`${basis}data.json`);
      if (!antwort.ok) {
        throw new Error(`data.json: Fehler ${antwort.status}`);
      }
      _wert = (await antwort.json()) as Daten;
      _modus = 'statisch';
    } catch (e2) {
      _wert = null;
      _fehler = e2 instanceof Error ? e2.message : 'Laden fehlgeschlagen.';
    }
  } finally {
    _laedt = false;
  }
}

export function konfliktSchliessen(): void {
  _konflikt = null;
}

// --------------------------------------------------------------- Hilfen

function _version(datei: string): string {
  const v = _wert?.versionen[datei];
  if (v === undefined) {
    throw new ApiFehler(409, `Kein Stand für '${datei}' bekannt — bitte neu laden.`);
  }
  return v;
}

function _teilDatei(): string {
  if (_wert && TEIL_DATEI in _wert.versionen) return TEIL_DATEI;
  const treffer = Object.keys(_wert?.versionen ?? {}).find((d) => d.endsWith('parts.csv'));
  return treffer ?? TEIL_DATEI;
}

function _einzelteilDatei(): string {
  if (_wert && EINZELTEIL_DATEI in _wert.versionen) return EINZELTEIL_DATEI;
  const treffer = Object.keys(_wert?.versionen ?? {}).find((d) => d.endsWith('bauteile.csv'));
  return treffer ?? EINZELTEIL_DATEI;
}

function _bereichStand(name: string) {
  const b = _wert?.bereiche.find((x) => x.name === name);
  if (!b) {
    throw new ApiFehler(409, `Bereich '${name}' unbekannt — bitte neu laden.`);
  }
  return b;
}

function _aufgabeStand(id: string) {
  const a = _wert?.aufgaben.find((x) => x.id === id);
  if (!a || !a.datei) {
    throw new ApiFehler(409, `Aufgabe '${id}' unbekannt — bitte neu laden.`);
  }
  return a;
}

/** Reicht den Fehler einer Schreibanfrage an den Rahmen weiter: 409 setzt
 * `konflikt` (Rumpf trägt den aktuellen Stand schon mit) und lädt den
 * Gesamtbestand einmal nach, 403/422/404 werden als deutsche Meldung
 * ausgegeben. */
async function _fehlerMelden(e: unknown, datei: string): Promise<void> {
  if (e instanceof ApiFehler) {
    if (e.status === 409) {
      _konflikt = { datei, meldung: e.meldung, stand: e.stand };
      await laden();
      return;
    }
    if (e.status === 403) {
      meldungSenden({ art: 'fehler', text: `Nicht erlaubt: ${e.meldung}` });
      return;
    }
    if (e.status === 422) {
      meldungSenden({ art: 'fehler', text: `Ungültige Eingabe: ${e.meldung}` });
      return;
    }
    if (e.status === 404) {
      meldungSenden({ art: 'fehler', text: `Nicht gefunden: ${e.meldung}` });
      return;
    }
  }
  meldungSenden({
    art: 'fehler',
    text: e instanceof Error ? e.message : 'Unbekannter Fehler beim Schreiben.',
  });
}

/** Sperre während einer laufenden Schreibanfrage: eine zweite Anfrage wird
 * abgewiesen statt eingereiht. Einreihen würde gegen einen Hash schreiben,
 * den der Nutzer zwischenzeitlich nicht mehr sieht — das Ergebnis wäre ein
 * überraschender Konflikt später statt jetzt. Abweisen ist vorhersehbarer:
 * die Oberfläche kann Aktionen einfach sperren, solange `schreibt` true ist. */
async function _schreiben(bezug: string, aktion: () => Promise<void>): Promise<void> {
  if (_schreibt) {
    meldungSenden({ art: 'fehler', text: 'Eine andere Änderung läuft noch — bitte kurz warten.' });
    return;
  }
  _schreibt = true;
  try {
    await aktion();
  } catch (e) {
    await _fehlerMelden(e, bezug);
  } finally {
    _schreibt = false;
  }
}

function _lesemodusPruefen(): void {
  if (_modus === 'statisch') {
    throw new Error('Lesemodus: Schreiben ist hier nicht möglich.');
  }
}

// ------------------------------------------------------------- Aufgaben

export async function aufgabeAnlegen(
  bereich: string,
  titel: string,
  optionen: {
    status?: string;
    beschreibung?: string;
    prio?: string;
    gruppe?: string | null;
    eltern_id?: string | null;
  } = {},
): Promise<void> {
  _lesemodusPruefen();
  // Bereichs-/Hash-Suche läuft bewusst innerhalb von `_schreiben`, damit ein
  // nicht (mehr) gefundener Bereich denselben Weg über `beobachten` nimmt
  // wie ein Serverfehler, statt die Zusage "wirft nur im Lesemodus" zu
  // brechen.
  await _schreiben(bereich, async () => {
    const b = _bereichStand(bereich);
    const version = _version(b.datei);
    await apiPost<SchreibErfolg>('/api/aufgaben', { bereich, titel, version, ...optionen });
    // Neue Aufgabe (Verschachtelung, Reihenfolge) lässt sich lokal nicht
    // sauber nachbilden — einmal neu laden.
    await laden();
  });
}

async function _aufgabePatch(
  id: string,
  feld: 'status' | 'titel' | 'beschreibung' | 'prio',
  wert: string,
): Promise<void> {
  _lesemodusPruefen();
  await _schreiben(id, async () => {
    const a = _aufgabeStand(id);
    const version = _version(a.datei!);
    const erfolg = await apiPatch<SchreibErfolg>(`/api/aufgaben/${id}`, {
      version,
      [feld]: wert,
    });
    const aktuelle = _wert!.aufgaben.find((x) => x.id === id);
    if (aktuelle) aktuelle[feld] = wert;
    _wert!.versionen[erfolg.datei] = erfolg.version;
  });
}

export function aufgabeStatus(id: string, status: string): Promise<void> {
  return _aufgabePatch(id, 'status', status);
}

export function aufgabeTitel(id: string, titel: string): Promise<void> {
  return _aufgabePatch(id, 'titel', titel);
}

export function aufgabeBeschreibung(id: string, beschreibung: string): Promise<void> {
  return _aufgabePatch(id, 'beschreibung', beschreibung);
}

export function aufgabePrio(id: string, prio: string): Promise<void> {
  return _aufgabePatch(id, 'prio', prio);
}

export async function aufgabeLoeschen(id: string): Promise<void> {
  _lesemodusPruefen();
  await _schreiben(id, async () => {
    const a = _aufgabeStand(id);
    const version = _version(a.datei!);
    await apiDelete<SchreibErfolg>(`/api/aufgaben/${id}`, { version });
    // Löschen nimmt laut Kern auch Unterpunkte mit — welche, ist von hier
    // aus nicht sicher zu wissen. Einmal neu laden.
    await laden();
  });
}

// ------------------------------------------------------------- Bereiche

export async function abschnittSetzen(bereich: string, abschnitt: string, text: string): Promise<void> {
  _lesemodusPruefen();
  await _schreiben(bereich, async () => {
    const b = _bereichStand(bereich);
    const version = _version(b.datei);
    const erfolg = await apiPut<SchreibErfolg>(
      `/api/bereiche/${encodeURIComponent(bereich)}/abschnitte/${encodeURIComponent(abschnitt)}`,
      { text, version },
    );
    const aktueller = _wert!.bereiche.find((x) => x.name === bereich);
    if (aktueller?.abschnitte?.[abschnitt]) {
      aktueller.abschnitte[abschnitt].text = text;
    }
    _wert!.versionen[erfolg.datei] = erfolg.version;
  });
}

export async function kopfSetzen(bereich: string, feld: string, wert: unknown): Promise<void> {
  _lesemodusPruefen();
  await _schreiben(bereich, async () => {
    const b = _bereichStand(bereich);
    const version = _version(b.datei);
    const erfolg = await apiPatch<SchreibErfolg>(
      `/api/bereiche/${encodeURIComponent(bereich)}/kopf`,
      { feld, wert, version },
    );
    const aktueller = _wert!.bereiche.find((x) => x.name === bereich);
    if (aktueller && feld in aktueller) {
      (aktueller as unknown as Record<string, unknown>)[feld] = wert;
    }
    _wert!.versionen[erfolg.datei] = erfolg.version;
  });
}

// --------------------------------------------------------------- Teile

export async function teilFeld(id: string, feld: string, wert: string): Promise<void> {
  _lesemodusPruefen();
  const datei = _teilDatei();
  await _schreiben(datei, async () => {
    const version = _version(datei);
    const erfolg = await apiPatch<SchreibErfolg>(`/api/teile/${encodeURIComponent(id)}`, {
      feld,
      wert,
      version,
    });
    const aktuelles = _wert!.teile.find((x) => x.id === id);
    if (aktuelles) (aktuelles as unknown as Record<string, unknown>)[feld] = wert;
    _wert!.versionen[erfolg.datei] = erfolg.version;
  });
}

export async function teilAnlegen(felder: Record<string, unknown>): Promise<void> {
  _lesemodusPruefen();
  const datei = _teilDatei();
  await _schreiben(datei, async () => {
    const version = _version(datei);
    await apiPost<SchreibErfolg>('/api/teile', { felder, version });
    await laden();
  });
}

export async function teilLoeschen(id: string): Promise<void> {
  _lesemodusPruefen();
  const datei = _teilDatei();
  await _schreiben(datei, async () => {
    const version = _version(datei);
    await apiDelete<SchreibErfolg>(`/api/teile/${encodeURIComponent(id)}`, { version });
    _wert!.teile = _wert!.teile.filter((x) => x.id !== id);
  });
}

// ----------------------------------------------------------- Einzelteile

export async function einzelteilFeld(id: string, feld: string, wert: string): Promise<void> {
  _lesemodusPruefen();
  const datei = _einzelteilDatei();
  await _schreiben(datei, async () => {
    const version = _version(datei);
    const erfolg = await apiPatch<SchreibErfolg>(`/api/einzelteile/${encodeURIComponent(id)}`, {
      feld,
      wert,
      version,
    });
    const aktuelles = _wert!.einzelteile.find((x) => x.id === id);
    if (aktuelles) (aktuelles as unknown as Record<string, unknown>)[feld] = wert;
    _wert!.versionen[erfolg.datei] = erfolg.version;
  });
}

export async function einzelteilAnlegen(felder: Record<string, unknown>): Promise<void> {
  _lesemodusPruefen();
  const datei = _einzelteilDatei();
  await _schreiben(datei, async () => {
    const version = _version(datei);
    await apiPost<SchreibErfolg>('/api/einzelteile', { felder, version });
    await laden();
  });
}

export async function einzelteilLoeschen(id: string): Promise<void> {
  _lesemodusPruefen();
  const datei = _einzelteilDatei();
  await _schreiben(datei, async () => {
    const version = _version(datei);
    await apiDelete<SchreibErfolg>(`/api/einzelteile/${encodeURIComponent(id)}`, { version });
    _wert!.einzelteile = _wert!.einzelteile.filter((x) => x.id !== id);
  });
}
