// Adressen der Mediendateien. Ausgeliefert werden die Web-Kopien aus
// docs/medien/ (tools/media.py: web_export) — Ordnernamen dort als slug,
// Bilder verkleinert. Der Server liefert sie unter /medien/ aus; im statischen
// Modus liegt medien/ neben data.json.
import type { MediumAntwort } from '../api-typen';
import { store } from '../daten.svelte';

const UMLAUTE: Record<string, string> = { ä: 'ae', ö: 'oe', ü: 'ue', ß: 'ss' };

// Gleiche Regel wie tools/common.py: slug
export function slug(text: string): string {
  let s = text.trim().toLowerCase();
  for (const [k, v] of Object.entries(UMLAUTE)) s = s.split(k).join(v);
  s = s.normalize('NFKD').replace(/[̀-ͯ]/g, '');
  return s.replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}

const PRAEFIX = 'vault/Medien/';

/** URL der Web-Kopie, oder null, wenn es keine gibt (z. B. 3D-Modelle). */
export function medienUrl(m: MediumAntwort): string | null {
  if (!m.datei.startsWith(PRAEFIX)) return null;
  const teile = m.datei.slice(PRAEFIX.length).split('/');
  const name = teile.pop() ?? m.dateiname;
  const pfad = [...teile.map(slug), name].map(encodeURIComponent).join('/');
  const basis = store.modus === 'server' ? '/medien/' : './medien/';
  return basis + pfad;
}

export function istBild(m: MediumAntwort): boolean {
  return m.art === 'bild';
}

export function endung(m: MediumAntwort): string {
  const i = m.dateiname.lastIndexOf('.');
  return i > 0 ? m.dateiname.slice(i + 1).toUpperCase() : '';
}
