// Einträge der Befehlspalette: Befehle, Ansichten und alle Inhalte aus den Daten.

import type { DatenAntwort } from '../api-typen';
import { ANSICHTEN, router, TITEL } from '../router.svelte';
import { theme } from '../theme.svelte';
import { STATUS_TEXT, istStatus } from '../ui/status';
import { preisText } from '../teile/format';
import { massText } from '../zuschnitt/mass';
import { istBild } from '../medien/url';

export type Art =
  | 'Befehl'
  | 'Ansicht'
  | 'Bereich'
  | 'Aufgabe'
  | 'Teil'
  | 'Einzelteil'
  | 'Entscheidung'
  | 'Anleitung'
  | 'Recherche'
  | 'Medium';

// Reihenfolge der Gruppen in der Trefferliste
export const ARTEN: Art[] = [
  'Befehl',
  'Ansicht',
  'Bereich',
  'Aufgabe',
  'Teil',
  'Einzelteil',
  'Entscheidung',
  'Anleitung',
  'Recherche',
  'Medium',
];

export const ART_MEHRZAHL: Record<Art, string> = {
  Befehl: 'Befehle',
  Ansicht: 'Ansichten',
  Bereich: 'Bereiche',
  Aufgabe: 'Aufgaben',
  Teil: 'Teile',
  Einzelteil: 'Einzelteile',
  Entscheidung: 'Entscheidungen',
  Anleitung: 'Anleitungen',
  Recherche: 'Recherche',
  Medium: 'Medien',
};

export interface Eintrag {
  schluessel: string;
  art: Art;
  titel: string;
  neben?: string;
  // zusätzlicher Suchtext, der nicht angezeigt wird
  kontext?: string;
  ausfuehren: () => void;
}

function statusText(s: string): string {
  return istStatus(s) ? STATUS_TEXT[s] : s;
}

function verbinden(...teile: (string | undefined | null)[]): string {
  return teile.filter(Boolean).join(' · ');
}

export function befehle(): Eintrag[] {
  const liste: Eintrag[] = [
    {
      schluessel: 'befehl-thema',
      art: 'Befehl',
      titel: theme.aktuell === 'hell' ? 'Dunkles Thema einschalten' : 'Helles Thema einschalten',
      neben: 'T',
      kontext: 'hell dunkel thema farbe modus',
      ausfuehren: () => theme.umschalten(),
    },
  ];
  ANSICHTEN.forEach((a, i) => {
    liste.push({
      schluessel: `ansicht-${a}`,
      art: 'Ansicht',
      titel: TITEL[a],
      neben: String(i + 1),
      kontext: 'gehe zu ansicht',
      ausfuehren: () => router.gehe(a),
    });
  });
  return liste;
}

export function inhalte(d: DatenAntwort): Eintrag[] {
  const liste: Eintrag[] = [];

  for (const b of d.bereiche) {
    const eigene = d.aufgaben.filter((a) => a.bereich === b.name);
    const fertig = eigene.filter((a) => a.status === 'erledigt').length;
    liste.push({
      schluessel: `bereich-${b.name}`,
      art: 'Bereich',
      titel: b.name,
      neben: eigene.length ? `${fertig}/${eigene.length}` : undefined,
      kontext: b.kurz,
      ausfuehren: () => router.gehe('bereiche', b.name),
    });
  }

  for (const a of d.aufgaben) {
    liste.push({
      schluessel: `aufgabe-${a.id}`,
      art: 'Aufgabe',
      titel: a.titel,
      neben: verbinden(a.bereich, statusText(a.status)),
      kontext: verbinden(a.id, a.gruppe),
      ausfuehren: () => router.gehe('aufgaben', a.id),
    });
  }

  for (const t of d.teile) {
    liste.push({
      schluessel: `teil-${t.id}`,
      art: 'Teil',
      titel: t.titel,
      neben: verbinden(t.kategorie, preisText(t)),
      kontext: verbinden(t.id, t.haendler, t.status, t.beschreibung),
      ausfuehren: () => router.gehe('teile', t.id),
    });
  }

  for (const e of d.einzelteile) {
    liste.push({
      schluessel: `einzelteil-${e.id}`,
      art: 'Einzelteil',
      titel: e.titel,
      neben: verbinden(e.bereich, massText(e)),
      kontext: verbinden(e.id, e.material, e.art),
      ausfuehren: () => router.gehe('zuschnitt', e.id),
    });
  }

  const seiten: [Art, keyof DatenAntwort, string][] = [
    ['Entscheidung', 'entscheidungen', 'entscheidungen'],
    ['Anleitung', 'anleitungen', 'anleitungen'],
    ['Recherche', 'recherche', 'recherche'],
  ];
  for (const [art, feld, reiter] of seiten) {
    for (const s of (d[feld] as DatenAntwort['entscheidungen']) ?? []) {
      liste.push({
        schluessel: `${reiter}-${s.datei}`,
        art,
        titel: s.titel,
        neben: verbinden(s.bereich, art === 'Entscheidung' ? s.status : undefined),
        ausfuehren: () => (s.bereich ? router.gehe('bereiche', s.bereich, reiter) : router.gehe('bereiche')),
      });
    }
  }

  for (const m of d.medien) {
    liste.push({
      schluessel: `medium-${m.datei}`,
      art: 'Medium',
      titel: m.name,
      neben: m.bereich,
      kontext: m.dateiname,
      // Bilder springen direkt in die Lupe (#/medien/<id>), alles andere
      // (Unterlage, Modell ohne Web-Kopie) nur in die gefilterte Galerie.
      ausfuehren: () => (istBild(m) ? router.gehe('medien', m.datei) : router.gehe('medien')),
    });
  }

  return liste;
}
