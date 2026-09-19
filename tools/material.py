"""Materialliste fürs Baumarkt: Einzelteile aus data/bauteile.csv nach
Material und Dicke gruppiert, mit Bedarf (m² bei Platten, laufende Meter bei
Leisten/Kantholz) und den einzelnen Zuschnitten darunter. Nur lesend — rührt
keine Datei an.
"""
from __future__ import annotations

from . import bauteile
from .common import table

_FLAECHE_ARTEN = ("Platte",)
_LAUFMETER_ARTEN = ("Leiste", "Kantholz")


def _schluessel(row: dict) -> tuple[str, str]:
    return (row.get("material") or "(ohne Material)", row.get("dicke_mm") or "")


def gruppieren(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    gruppen: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        gruppen.setdefault(_schluessel(row), []).append(row)
    return gruppen


def bedarf(rows: list[dict]) -> str:
    """Bedarfstext einer Materialgruppe: m² für Platten und laufende Meter
    für Leisten/Kantholz getrennt summiert, Rest als Stückzahl."""
    teile = []
    qm = sum(bauteile.flaeche(r) for r in rows if r.get("art") in _FLAECHE_ARTEN)
    lfm = sum(bauteile.laufmeter(r) for r in rows if r.get("art") in _LAUFMETER_ARTEN)
    sonst = sum(bauteile.anzahl(r) for r in rows
               if r.get("art") not in _FLAECHE_ARTEN + _LAUFMETER_ARTEN)
    if qm:
        teile.append(f"{qm:.2f} m²")
    if lfm:
        teile.append(f"{lfm:.2f} lfm")
    if sonst:
        teile.append(f"{sonst:g} Stk")
    return " + ".join(teile) if teile else "—"


def liste(bereich: str = "") -> list[dict]:
    rows = bauteile.load()
    if bereich:
        rows = bauteile.filtered(rows, bereich=bereich)
    ergebnis = []
    for (material, dicke), grows in sorted(gruppieren(rows).items()):
        ergebnis.append({
            "material": material,
            "dicke_mm": dicke,
            "bedarf": bedarf(grows),
            "zuschnitte": sorted(grows, key=lambda r: r.get("titel", "")),
        })
    return ergebnis


def text(bereich: str = "") -> str:
    gruppen = liste(bereich)
    if not gruppen:
        return ("Keine Einzelteile" + (f" in {bereich}" if bereich else "") +
                ". Anlegen mit `camper bauteile add --titel ... --bereich ...`")

    bloecke = []
    for g in gruppen:
        titel = g["material"]
        if g["dicke_mm"]:
            titel += f", {g['dicke_mm']} mm"
        kopf = f"## {titel} — {g['bedarf']}"
        zeilen = [[r["titel"], bauteile.mass_text(r), f"{bauteile.anzahl(r):g}",
                  r.get("bereich", ""), r.get("status", "")]
                 for r in g["zuschnitte"]]
        body = table(zeilen, ["zuschnitt", "maß", "anz", "bereich", "status"])
        bloecke.append(kopf + "\n" + body)

    kopf_gesamt = "Materialliste" + (f" — {bereich}" if bereich else "")
    anzahl_teile = sum(len(g["zuschnitte"]) for g in gruppen)
    fuss = f"\n\n{len(gruppen)} Materialgruppen · {anzahl_teile} Zuschnitte"
    return kopf_gesamt + "\n\n" + "\n\n".join(bloecke) + fuss
