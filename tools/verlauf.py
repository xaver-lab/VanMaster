"""Kostenverlauf: ein Datensatz je Tag mit den wichtigsten Kennzahlen.

Liegt unter ``data/verlauf.csv`` — bewusst nicht unter ``data/generated/``:
das wird bei jedem ``sync`` verworfen und neu geschrieben, die Historie muss
aber über sync-Läufe und Git-Commits hinweg erhalten bleiben. Eine CSV neben
``parts.csv``/``bauteile.csv`` bleibt von Hand lesbar und diffbar in Git,
ohne ein neues Format zu erfinden.

``erfassen()`` schreibt einen Datensatz für heute fort und ersetzt dabei
einen vorhandenen Eintrag desselben Tages, statt eine Dublette anzulegen —
mehrfacher Aufruf am selben Tag aktualisiert nur den heutigen Stand.
"""
from __future__ import annotations

import csv
from datetime import date

from . import budget, parts, tasks
from .common import VERLAUF_CSV, bar, euro, table

FELDER = ["datum", "bezahlt", "geplant", "prognose",
          "aufgaben_fertig", "aufgaben_gesamt", "gewicht_kg"]


def lesen() -> list[dict]:
    if not VERLAUF_CSV.exists():
        return []
    with VERLAUF_CSV.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _schreiben(rows: list[dict]) -> None:
    VERLAUF_CSV.parent.mkdir(parents=True, exist_ok=True)
    with VERLAUF_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=FELDER, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({f: row.get(f, "") for f in FELDER})


def erfassen(heute: str | None = None) -> str:
    heute = heute or date.today().isoformat()
    d = budget.daten()
    alle = tasks.load()
    fertig, gesamt = tasks.fortschritt(alle)
    gewicht = round(parts.gewicht_summe(parts.load()), 2)

    rows = [r for r in lesen() if r["datum"] != heute]
    rows.append({
        "datum": heute,
        "bezahlt": f"{d['bezahlt']:.2f}",
        "geplant": f"{d['geplant']:.2f}",
        "prognose": f"{d['prognose']:.2f}",
        "aufgaben_fertig": str(fertig),
        "aufgaben_gesamt": str(gesamt),
        "gewicht_kg": f"{gewicht:.2f}" if gewicht else "",
    })
    rows.sort(key=lambda r: r["datum"])
    _schreiben(rows)

    gewicht_txt = f", {gewicht:.1f} kg" if gewicht else ""
    return (f"Verlauf erfasst für {heute}: {euro(d['bezahlt'])} bezahlt, "
            f"{euro(d['geplant'])} geplant, {fertig}/{gesamt} Aufgaben"
            f"{gewicht_txt}")


def _zahl(wert: str) -> float:
    try:
        return float(wert or 0)
    except ValueError:
        return 0.0


def _ganz(wert: str) -> int:
    try:
        return int(float(wert or 0))
    except ValueError:
        return 0


def daten(limit: int | None = None) -> dict:
    """Die Zeitreihe als Zahlen, samt Veränderung über den ganzen Zeitraum.

    Einzige Rechenstelle: ``text()``, ``--json`` und die Dashboard-Ansicht
    lesen hier, damit die drei nicht auseinanderlaufen. ``limit`` kürzt nur
    die Punkte auf die letzten n; die Veränderung wird immer über den
    vollen Verlauf gerechnet, sonst hinge sie am Ausschnitt.
    """
    rows = lesen()
    alle = [{
        "datum": r.get("datum", ""),
        "bezahlt": round(_zahl(r.get("bezahlt", "")), 2),
        "geplant": round(_zahl(r.get("geplant", "")), 2),
        "prognose": round(_zahl(r.get("prognose", "")), 2),
        "aufgaben_fertig": _ganz(r.get("aufgaben_fertig", "")),
        "aufgaben_gesamt": _ganz(r.get("aufgaben_gesamt", "")),
        "gewicht_kg": round(_zahl(r["gewicht_kg"]), 2) if r.get("gewicht_kg") else None,
    } for r in rows]

    punkte = alle[-limit:] if limit else alle
    if not alle:
        return {"punkte": [], "anzahl": 0, "von": None, "bis": None,
                "delta_bezahlt": 0.0, "delta_geplant": 0.0,
                "delta_prognose": 0.0, "delta_aufgaben_fertig": 0}

    erster, letzter = alle[0], alle[-1]
    return {
        "punkte": punkte,
        "anzahl": len(alle),
        "von": erster["datum"],
        "bis": letzter["datum"],
        "delta_bezahlt": round(letzter["bezahlt"] - erster["bezahlt"], 2),
        "delta_geplant": round(letzter["geplant"] - erster["geplant"], 2),
        "delta_prognose": round(letzter["prognose"] - erster["prognose"], 2),
        "delta_aufgaben_fertig": letzter["aufgaben_fertig"] - erster["aufgaben_fertig"],
    }


def text(limit: int = 12) -> str:
    d = daten(limit=limit)
    if not d["punkte"]:
        return ("Noch kein Verlauf erfasst — 'camper verlauf' legt für heute "
                "den ersten Datensatz an.")
    body = [[
        p["datum"], euro(p["bezahlt"]), euro(p["geplant"]),
        bar(p["aufgaben_fertig"], p["aufgaben_gesamt"], 8),
        f"{p['gewicht_kg']:.1f} kg" if p["gewicht_kg"] else "—",
    ] for p in d["punkte"]]
    kopf = table(body, ["Datum", "Bezahlt", "Geplant", "Aufgaben", "Gewicht"])

    if d["anzahl"] < 2:
        return kopf
    vz = "+" if d["delta_bezahlt"] >= 0 else ""
    return (f"{kopf}\n\nSeit {d['von']}: {vz}{euro(d['delta_bezahlt'])} bezahlt "
            f"({d['anzahl']} Datensätze)")
