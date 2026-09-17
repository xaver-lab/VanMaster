"""Dashboard-Daten erzeugen — docs/data.json ist reine Ausgabe."""
from __future__ import annotations

import json
from datetime import datetime

from . import media, parts, status, tasks
from .common import (
    ANLEITUNGEN_DIR, DASHBOARD_JSON, DOCS, ENTSCHEIDUNGEN_DIR,
    PART_KATEGORIEN, RECHERCHE_DIR, SYSTEME_DIR, VAULT,
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


def daten() -> dict:
    m = media.web_export()
    alle = tasks.load()
    teile = parts.load()
    fertig, gesamt_n = tasks.fortschritt(alle)

    bereiche = []
    for name, liste in sorted(tasks.nach_bereich(alle).items()):
        bfertig, bgesamt = tasks.fortschritt(liste)
        bereiche.append({"name": name, "fertig": bfertig, "gesamt": bgesamt})

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

    bestellt = [t for t in teile
                if t["status"] in ("Bestellt", "Geliefert", "Verbaut")]
    return {
        "erzeugt": datetime.now().isoformat(timespec="minutes"),
        "projekt": "VanMaster",
        "kennzahlen": {
            "aufgaben_fertig": fertig,
            "aufgaben_gesamt": gesamt_n,
            "teile": len(teile),
            "kosten": round(parts.summe(teile), 2),
            "kosten_bestellt": round(parts.summe(bestellt), 2),
            "gewicht": round(parts.gewicht_summe(teile), 2),
            "offene_entscheidungen": len(status.offene_entscheidungen()),
        },
        "bereiche": bereiche,
        "kategorien": kategorien,
        "aufgaben": alle,
        "teile": teile_json,
        "entscheidungen": seiten(ENTSCHEIDUNGEN_DIR),
        "anleitungen": seiten(ANLEITUNGEN_DIR),
        "systeme": seiten(SYSTEME_DIR),
        "recherche": seiten(RECHERCHE_DIR),
        "medien": m["bilder"],
        "dokumente": m["dokumente"],
    }


def build() -> str:
    d = daten()
    write_json(DASHBOARD_JSON, d)
    # Zweite Ausgabe als JS, damit das Dashboard auch per Doppelklick
    # (file://) läuft — dort blockiert der Browser fetch().
    js = ("window.VANMASTER_DATEN = "
          + json.dumps(d, ensure_ascii=False, separators=(",", ":")) + ";\n")
    (DOCS / "data.js").write_text(js, encoding="utf-8", newline="\n")
    k = d["kennzahlen"]
    return (f"docs/data.json geschrieben — {k['aufgaben_gesamt']} Aufgaben, "
            f"{k['teile']} Teile, {len(d['medien'])} Bilder, "
            f"{len(d['dokumente'])} Dokumente")
