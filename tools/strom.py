"""Strombilanz: Tagesverbrauch der Verbraucher gegen die Batteriekapazität.

Die Verbraucher sind keine eigene Ablage, sondern die Teile aus
``data/parts.csv``, die `watt` und `stunden_pro_tag` gesetzt haben —
Kühlschrank, Pumpe, Licht und Lüfter *sind* Teile der Stückliste. Das ist
derselbe Gedanke wie bei `gewicht_kg` (§13): eine physikalische Eigenschaft
am Teil, nicht eine zweite Liste derselben Dinge. Eine dritte CSV wäre eine
Ablage, die mit der Stückliste auseinanderläuft, sobald ein Verbraucher
umentschieden wird.

Die Anlagendaten (Bordspannung, Batteriekapazität, nutzbarer Anteil) stehen
im Kopf von ``vault/Camper.md``, wie Budget (§11) und Fahrzeuggewicht (§13).
Gelesen wird nur, nie geschrieben.

Gerechnet wird bewusst schlicht und nachvollziehbar:

    Wh/Tag  = Menge × Watt × Stunden pro Tag
    Ah/Tag  = Wh/Tag ÷ Bordspannung
    Reichweite = nutzbare Kapazität ÷ Ah/Tag

Wandlungs- und Leitungsverluste stecken nicht drin. Wer sie berücksichtigen
will, trägt sie über `wirkungsgrad` im Kopf ein — der Vorgabewert 1.0 rechnet
ohne. Nur lesend.
"""
from __future__ import annotations

from . import parts
from .common import CAMPER_MD, bar, read_text, split_frontmatter, table

# Ab hier wird gewarnt: weniger als ein Tag Reserve ist keine Auslegung.
SCHWELLE_TAGE = 1.0

VORGABE_SPANNUNG = 12.0
# Nutzbarer Anteil der Nennkapazität. LiFePO4 verträgt 80–90 %, Blei eher
# 50 %. Ohne Angabe wird der vorsichtige LiFePO4-Wert genommen.
VORGABE_NUTZBAR = 0.8
VORGABE_WIRKUNGSGRAD = 1.0


def _num(value) -> float | None:
    if value in (None, "", []):
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except ValueError:
        return None


def anlage() -> dict:
    """`bordspannung_v`, `batterie_ah`, `batterie_nutzbar`, `wirkungsgrad`
    aus dem Kopf von vault/Camper.md. Fehlt die Datei oder ein Feld, greifen
    die Vorgaben oben; `batterie_ah` hat keine Vorgabe — ohne sie gibt es
    keine Reichweite."""
    meta = {}
    if CAMPER_MD.exists():
        meta, _ = split_frontmatter(read_text(CAMPER_MD))
    return {
        "bordspannung_v": _num(meta.get("bordspannung_v")) or VORGABE_SPANNUNG,
        "batterie_ah": _num(meta.get("batterie_ah")),
        "batterie_nutzbar": _num(meta.get("batterie_nutzbar")) or VORGABE_NUTZBAR,
        "wirkungsgrad": _num(meta.get("wirkungsgrad")) or VORGABE_WIRKUNGSGRAD,
    }


def _verbrauch(row: dict, spannung: float) -> dict | None:
    """Ein Verbraucher, wenn Watt *und* Stunden gesetzt sind. Eines allein
    ergibt keinen Tagesverbrauch — dann fehlt die Angabe, statt sie zu raten."""
    watt = _num(row.get("watt"))
    stunden = _num(row.get("stunden_pro_tag"))
    if watt is None or stunden is None:
        return None
    menge = _num(row.get("menge")) or 1
    wh = menge * watt * stunden
    return {
        "id": row["id"], "titel": row["titel"], "kategorie": row["kategorie"],
        "status": row["status"],
        "menge": menge, "watt": watt, "stunden_pro_tag": stunden,
        "wh_pro_tag": round(wh, 1),
        "ah_pro_tag": round(wh / spannung, 2) if spannung else 0.0,
    }


def bilanz() -> dict:
    """Kennzahlen für Text- und JSON-Ausgabe von ``camper strom``."""
    a = anlage()
    spannung = a["bordspannung_v"]

    rows = parts.load()
    verbraucher = []
    unvollstaendig = []
    for row in rows:
        v = _verbrauch(row, spannung)
        if v:
            verbraucher.append(v)
        elif _num(row.get("watt")) is not None or _num(row.get("stunden_pro_tag")) is not None:
            # Halb gepflegt: das ist ein Hinweis wert, sonst fehlt es still.
            unvollstaendig.append({
                "id": row["id"], "titel": row["titel"],
                "watt": row.get("watt", ""),
                "stunden_pro_tag": row.get("stunden_pro_tag", ""),
            })

    verbraucher.sort(key=lambda v: -v["wh_pro_tag"])
    wh = round(sum(v["wh_pro_tag"] for v in verbraucher), 1)
    ah = round(wh / spannung, 2) if spannung else 0.0
    # Der Wirkungsgrad schlägt auf den Bedarf: was aus der Batterie muss,
    # ist mehr als was am Verbraucher ankommt.
    ah_roh = round(ah / a["wirkungsgrad"], 2) if a["wirkungsgrad"] else ah

    nutzbar_ah = (round(a["batterie_ah"] * a["batterie_nutzbar"], 1)
                  if a["batterie_ah"] is not None else None)
    reichweite = (round(nutzbar_ah / ah_roh, 1)
                  if nutzbar_ah is not None and ah_roh > 0 else None)

    return {
        "verbraucher": verbraucher,
        "unvollstaendig": unvollstaendig,
        "teile_gesamt": len(rows),
        "wh_pro_tag": wh,
        "ah_pro_tag": ah,
        "ah_pro_tag_brutto": ah_roh,
        "bordspannung_v": spannung,
        "batterie_ah": a["batterie_ah"],
        "batterie_nutzbar": a["batterie_nutzbar"],
        "nutzbar_ah": nutzbar_ah,
        "wirkungsgrad": a["wirkungsgrad"],
        "reichweite_tage": reichweite,
    }


def text() -> str:
    d = bilanz()

    if not d["verbraucher"]:
        zeilen = [
            "Keine Verbraucher erfasst — die Strombilanz braucht an den Teilen "
            "`watt` und `stunden_pro_tag`.",
            "",
            "Beispiel: `camper parts excel` öffnen, beim Kühlschrank 45 W und "
            "8 h/Tag eintragen, `camper parts import`.",
            "Nur Teile mit *beiden* Werten zählen als Verbraucher.",
        ]
        if d["unvollstaendig"]:
            zeilen += ["", f"Halb gepflegt ({len(d['unvollstaendig'])}):"]
            zeilen += [f"  {u['titel']} — watt={u['watt'] or '—'}, "
                       f"stunden_pro_tag={u['stunden_pro_tag'] or '—'}"
                       for u in d["unvollstaendig"]]
        return "\n".join(zeilen)

    zeilen = [[v["titel"], v["kategorie"],
               f"{v['menge']:g}× {v['watt']:g} W",
               f"{v['stunden_pro_tag']:g} h",
               f"{v['wh_pro_tag']:.0f}",
               f"{v['ah_pro_tag']:.1f}"]
              for v in d["verbraucher"]]
    bloecke = [
        f"Strombilanz — {len(d['verbraucher'])} Verbraucher bei "
        f"{d['bordspannung_v']:g} V",
        table(zeilen, ["verbraucher", "kategorie", "leistung", "täglich",
                       "Wh/Tag", "Ah/Tag"]),
        f"Tagesbedarf: {d['wh_pro_tag']:.0f} Wh = {d['ah_pro_tag']:.1f} Ah"
        + (f" (aus der Batterie {d['ah_pro_tag_brutto']:.1f} Ah bei "
           f"{d['wirkungsgrad'] * 100:.0f} % Wirkungsgrad)"
           if d["wirkungsgrad"] != 1.0 else ""),
    ]

    if d["unvollstaendig"]:
        bloecke.append(
            f"⚠ {len(d['unvollstaendig'])} Teile haben nur einen der beiden "
            "Werte und fehlen in der Bilanz:\n"
            + "\n".join(f"  {u['titel']} — watt={u['watt'] or '—'}, "
                        f"stunden_pro_tag={u['stunden_pro_tag'] or '—'}"
                        for u in d["unvollstaendig"]))

    if d["batterie_ah"] is None:
        bloecke.append(
            "Keine Reichweite: `batterie_ah` fehlt im Kopf von "
            "vault/Camper.md. Eintragen, z. B.:\n"
            "  batterie_ah: 200\n"
            "  bordspannung_v: 12\n"
            "  batterie_nutzbar: 0.8")
        return "\n\n".join(bloecke)

    bloecke.append(
        f"Batterie: {d['batterie_ah']:.0f} Ah, davon nutzbar "
        f"{d['nutzbar_ah']:.0f} Ah ({d['batterie_nutzbar'] * 100:.0f} %)")

    tage = d["reichweite_tage"]
    if tage is None:
        return "\n\n".join(bloecke)

    anteil = min(d["ah_pro_tag_brutto"] / d["nutzbar_ah"], 1.0) if d["nutzbar_ah"] else 1.0
    bloecke.append(bar(round(anteil * 100), 100)
                   + f"  {d['ah_pro_tag_brutto']:.1f} / {d['nutzbar_ah']:.0f} Ah pro Tag"
                   + f"\nReichweite ohne Nachladen: {tage:.1f} Tage")
    if tage < SCHWELLE_TAGE:
        bloecke.append("⚠ Unter einem Tag Reserve — ohne Solar oder Landstrom "
                       "ist das zu knapp.")
    return "\n\n".join(bloecke)
