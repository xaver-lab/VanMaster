"use strict";

/* ------------------------------------------------------------- Markdown */

/* Kleiner Renderer — reicht für die Bereichstexte, keine Bibliothek nötig. */
function mdInline(s) {
  return s
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\[\[([^\]|]+)(?:\|[^\]]+)?\]\]/g, "$1")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g,
             '<a href="$2" target="_blank" rel="noopener">$1</a>');
}

function md(text) {
  const aus = [];
  let liste = null;
  let absatz = [];
  const absatzEnde = () => {
    if (absatz.length) { aus.push("<p>" + mdInline(absatz.join(" ")) + "</p>"); absatz = []; }
  };
  const listeEnde = () => { if (liste) { aus.push("</" + liste + ">"); liste = null; } };
  let tabelle = null;
  const tabelleEnde = () => { if (tabelle) { aus.push("</table></div>"); tabelle = null; } };
  // | a | b |  ·  die Trennzeile aus Strichen wird nur erkannt, nicht gezeigt.
  const zellen = (z) => z.slice(1, -1).split("|").map((c) => c.trim());

  for (const roh of (text || "").split("\n")) {
    const z = roh.trim();
    if (!z) { absatzEnde(); listeEnde(); tabelleEnde(); continue; }

    if (z.startsWith("|") && z.endsWith("|")) {
      absatzEnde(); listeEnde();
      if (/^\|[\s|:-]+\|$/.test(z)) {
        if (tabelle === "kopf") tabelle = "rumpf";
        continue;
      }
      const kopfzeile = tabelle === null;
      if (kopfzeile) { aus.push('<div class="tabellenrand"><table>'); tabelle = "kopf"; }
      const tag = kopfzeile ? "th" : "td";
      aus.push("<tr>" + zellen(z).map(
        (c) => "<" + tag + ">" + mdInline(c) + "</" + tag + ">").join("") + "</tr>");
      continue;
    }
    tabelleEnde();

    const ueberschrift = z.match(/^(#{1,6})\s+(.*)$/);
    if (ueberschrift) {
      absatzEnde(); listeEnde();
      const stufe = Math.min(ueberschrift[1].length + 2, 6);
      aus.push("<h" + stufe + ">" + mdInline(ueberschrift[2]) + "</h" + stufe + ">");
      continue;
    }

    const punkt = z.match(/^[-*]\s+(.*)$/);
    const nummer = z.match(/^\d+\.\s+(.*)$/);
    if (punkt || nummer) {
      absatzEnde();
      const art = punkt ? "ul" : "ol";
      if (liste !== art) { listeEnde(); aus.push("<" + art + ">"); liste = art; }
      aus.push("<li>" + mdInline((punkt || nummer)[1]) + "</li>");
      continue;
    }

    // Eingerückte Fortsetzung gehört zum vorigen Listenpunkt.
    if (liste && /^\s/.test(roh)) {
      aus[aus.length - 1] = aus[aus.length - 1]
        .replace(/<\/li>$/, " " + mdInline(z) + "</li>");
      continue;
    }

    listeEnde();
    absatz.push(z);
  }
  absatzEnde(); listeEnde(); tabelleEnde();
  return aus.join("");
}
