"""Dashboard-Daten erzeugen — docs/data.json ist reine Ausgabe."""
from __future__ import annotations

import json
from datetime import datetime

from . import bauteile, bereiche, media, parts, status, tasks
from .common import (
    ANLEITUNGEN_DIR, DASHBOARD_JSON, DOCS, ENTSCHEIDUNGEN_DIR,
    PART_KATEGORIEN, RECHERCHE_DIR, SORTIERUNGEN, STANDARD_SORTIERUNG, VAULT,
    read_text, split_frontmatter, write_json,
)


def seiten(ordner) -> list[dict]:
    """Markdown-Seiten eines Vault-Ordners samt Kopf und Rohtext."""
    if not ordner.exists():
        return []
    out = []
    for datei in sorted(ordner.glob("*.md")):
        meta, body = split_frontmatter(read_text(datei))
        out.append({
            "titel": datei.stem,
            "status": meta.get("status", ""),
            "bereich": meta.get("bereich", meta.get("system", "")),
            "meta": meta,
            "text": body.strip(),
            "datei": str(datei.relative_to(VAULT.parent)).replace("\\", "/"),
        })
    return out


def daten(sortierung: str = STANDARD_SORTIERUNG) -> dict:
    m = media.web_export()
    alle = tasks.load()
    teile = parts.load()
    fertig, gesamt_n = tasks.fortschritt(alle)

    nach_b = tasks.nach_bereich(alle)
    bereiche_json = []
    for b in bereiche.load():
        bfertig, bgesamt = tasks.fortschritt(nach_b.get(b["name"], []))
        bereiche_json.append({**b, "fertig": bfertig, "gesamt": bgesamt})
    # Bereiche, die nur als Aufgabenkopf vorkommen, gehen nicht verloren.
    bekannt = {b["name"] for b in bereiche_json}
    for name, liste in sorted(nach_b.items()):
        if name in bekannt:
            continue
        bfertig, bgesamt = tasks.fortschritt(liste)
        bereiche_json.append({
            "name": name, "kurz": "", "status": "geplant", "phase": None,
            "beschreibung": "", "stand": "", "auslegung": "", "notizen": "",
            "links": [], "datei": "",
            "fertig": bfertig, "gesamt": bgesamt,
        })
    # Reihenfolge kommt fertig aus data.json — das Dashboard sortiert nur um,
    # wenn der Nutzer den Wechsler anfasst.
    bereiche_json = bereiche.sortiere(bereiche_json, sortierung)

    kategorien = []
    for kat in PART_KATEGORIEN:
        krows = [t for t in teile if t["kategorie"] == kat]
        if krows:
            kategorien.append({
                "name": kat, "teile": len(krows),
                "kosten": round(parts.summe(krows), 2),
                "gewicht": round(parts.gewicht_summe(krows), 2),
                "verbaut": len([t for t in krows if t["status"] == "Verbaut"]),
            })

    teile_json = []
    for t in teile:
        eintrag = dict(t)
        eintrag["menge_n"] = parts.num(t["menge"], 1)
        eintrag["preis_n"] = round(parts.num(t["preis"]), 2)
        eintrag["gesamt"] = round(parts.gesamt(t), 2)
        eintrag["gewicht_n"] = round(parts.gewicht(t), 2)
        teile_json.append(eintrag)

    bauteile_json = []
    for r in bauteile.load():
        eintrag = dict(r)
        eintrag["flaeche_m2"] = round(bauteile.flaeche(r), 3)
        eintrag["laufmeter"] = round(bauteile.laufmeter(r), 2)
        eintrag["mass"] = bauteile.mass_text(r)
        bauteile_json.append(eintrag)

    bestellt = [t for t in teile
                if t["status"] in ("Bestellt", "Geliefert", "Verbaut")]
    return {
        "erzeugt": datetime.now().isoformat(timespec="minutes"),
        "projekt": "VanMaster",
        "sortierung": sortierung if sortierung in SORTIERUNGEN else STANDARD_SORTIERUNG,
        "kennzahlen": {
            "aufgaben_fertig": fertig,
            "aufgaben_gesamt": gesamt_n,
            "teile": len(teile),
            "kosten": round(parts.summe(teile), 2),
            "kosten_bestellt": round(parts.summe(bestellt), 2),
            "gewicht": round(parts.gewicht_summe(teile), 2),
            "offene_entscheidungen": len(status.offene_entscheidungen()),
            "bauteile": len(bauteile_json),
        },
        "bereiche": bereiche_json,
        "kategorien": kategorien,
        "aufgaben": alle,
        "teile": teile_json,
        "bauteile": bauteile_json,
        "entscheidungen": seiten(ENTSCHEIDUNGEN_DIR),
        "anleitungen": seiten(ANLEITUNGEN_DIR),
        "recherche": seiten(RECHERCHE_DIR),
        "medien": m["bilder"],
        "dokumente": m["dokumente"],
        "modelle": m["modelle"],
    }


def build(sortierung: str = STANDARD_SORTIERUNG) -> str:
    return schreiben(daten(sortierung))


def schreiben(d: dict) -> str:
    """Erzeugte Daten ablegen — getrennt von daten(), damit der Server die
    frisch gebauten Daten direkt weiterreichen kann, ohne zweimal zu bauen."""
    write_json(DASHBOARD_JSON, d)
    # Zweite Ausgabe als JS, damit das Dashboard auch per Doppelklick
    # (file://) läuft — dort blockiert der Browser fetch().
    js = ("window.VANMASTER_DATEN = "
          + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n")
    (DOCS / "data.js").write_text(js, encoding="utf-8", newline="\n")
    k = d["kennzahlen"]
    return (f"docs/data.json geschrieben — {len(d['bereiche'])} Bereiche, "
            f"{k['aufgaben_gesamt']} Aufgaben, {k['teile']} Teile, "
            f"{k['bauteile']} Einzelteile, {len(d['medien'])} Bilder, "
            f"{len(d['dokumente'])} Dokumente, {len(d['modelle'])} Modelle")
