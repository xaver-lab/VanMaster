// Kleiner Markdown-Renderer — Port von docs/js/markdown.js (reicht für die
// Bereichs-/Aufgabentexte, keine Bibliothek nötig). Neu gegenüber dem alten
// Dashboard: [[Ziel]]/[[Ziel|Text]] wird über `aufloesen` zu einem echten
// Link aufgelöst statt nur die Klammern zu entfernen; ohne Treffer bleibt
// der Querverweis als toter Verweis sichtbar.

export interface Aufloesung {
  href: string;
}

export type Aufloeser = (ziel: string) => Aufloesung | null;

function attr(s: string): string {
  return s.replace(/"/g, '&quot;');
}

function mdInline(s: string, aufloesen?: Aufloeser): string {
  let aus = s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

  aus = aus.replace(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g, (_m, ziel: string, text?: string) => {
    const zielKlar = ziel.trim();
    const anzeige = (text ?? ziel).trim();
    const ergebnis = aufloesen ? aufloesen(zielKlar) : null;
    if (ergebnis) {
      return `<a href="${attr(ergebnis.href)}" class="wiki-link" data-ziel="${attr(zielKlar)}">${anzeige}</a>`;
    }
    return `<span class="wiki-link tot" title="${attr('Ziel nicht gefunden: ' + zielKlar)}">${anzeige}</span>`;
  });

  // Nur http(s) und Ziele ohne Schema; alles andere (javascript: …) bleibt Text.
  aus = aus.replace(/\[([^\]]+)\]\(([^)\s]+)\)/g, (m, text: string, ziel: string) =>
    /^https?:\/\//i.test(ziel) || !/^[a-z][a-z0-9+.-]*:/i.test(ziel)
      ? `<a href="${attr(ziel)}" target="_blank" rel="noopener">${text}</a>`
      : m,
  );
  return aus;
}

export function md(text: string, aufloesen?: Aufloeser): string {
  const aus: string[] = [];
  let liste: 'ul' | 'ol' | null = null;
  let absatz: string[] = [];
  const absatzEnde = (): void => {
    if (absatz.length) {
      aus.push('<p>' + mdInline(absatz.join(' '), aufloesen) + '</p>');
      absatz = [];
    }
  };
  const listeEnde = (): void => {
    if (liste) {
      aus.push('</' + liste + '>');
      liste = null;
    }
  };
  let tabelle: 'kopf' | 'rumpf' | null = null;
  const tabelleEnde = (): void => {
    if (tabelle) {
      aus.push('</table></div>');
      tabelle = null;
    }
  };
  const zellen = (z: string): string[] => z.slice(1, -1).split('|').map((c) => c.trim());

  for (const roh of (text || '').split('\n')) {
    const z = roh.trim();
    if (!z) {
      absatzEnde();
      listeEnde();
      tabelleEnde();
      continue;
    }

    if (z.startsWith('|') && z.endsWith('|')) {
      absatzEnde();
      listeEnde();
      if (/^\|[\s|:-]+\|$/.test(z)) {
        if (tabelle === 'kopf') tabelle = 'rumpf';
        continue;
      }
      const kopfzeile = tabelle === null;
      if (kopfzeile) {
        aus.push('<div class="tabellenrand"><table>');
        tabelle = 'kopf';
      }
      const tag = kopfzeile ? 'th' : 'td';
      aus.push(
        '<tr>' +
          zellen(z)
            .map((c) => '<' + tag + '>' + mdInline(c, aufloesen) + '</' + tag + '>')
            .join('') +
          '</tr>',
      );
      continue;
    }
    tabelleEnde();

    const ueberschrift = z.match(/^(#{1,6})\s+(.*)$/);
    if (ueberschrift) {
      absatzEnde();
      listeEnde();
      const stufe = Math.min(ueberschrift[1].length + 2, 6);
      aus.push('<h' + stufe + '>' + mdInline(ueberschrift[2], aufloesen) + '</h' + stufe + '>');
      continue;
    }

    const punkt = z.match(/^[-*]\s+(.*)$/);
    const nummer = z.match(/^\d+\.\s+(.*)$/);
    if (punkt || nummer) {
      absatzEnde();
      const art: 'ul' | 'ol' = punkt ? 'ul' : 'ol';
      if (liste !== art) {
        listeEnde();
        aus.push('<' + art + '>');
        liste = art;
      }
      aus.push('<li>' + mdInline((punkt || nummer)![1], aufloesen) + '</li>');
      continue;
    }

    // Eingerückte Fortsetzung gehört zum vorigen Listenpunkt.
    if (liste && /^\s/.test(roh)) {
      aus[aus.length - 1] = aus[aus.length - 1].replace(
        /<\/li>$/,
        ' ' + mdInline(z, aufloesen) + '</li>',
      );
      continue;
    }

    listeEnde();
    absatz.push(z);
  }
  absatzEnde();
  listeEnde();
  tabelleEnde();
  return aus.join('');
}
