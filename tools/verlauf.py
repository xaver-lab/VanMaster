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


def text(limit: int = 12) -> str:
    rows = lesen()
    if not rows:
        return ("Noch kein Verlauf erfasst — 'camper verlauf' legt für heute "
                "den ersten Datensatz an.")
    zeigen = rows[-limit:]
    body = [[
        r["datum"], euro(float(r["bezahlt"] or 0)), euro(float(r["geplant"] or 0)),
        bar(int(r["aufgaben_fertig"] or 0), int(r["aufgaben_gesamt"] or 0), 8),
        f"{r['gewicht_kg']} kg" if r["gewicht_kg"] else "—",
    ] for r in zeigen]
    kopf = table(body, ["Datum", "Bezahlt", "Geplant", "Aufgaben", "Gewicht"])

    if len(rows) < 2:
        return kopf
    erster, letzter = rows[0], rows[-1]
    delta = float(letzter["bezahlt"] or 0) - float(erster["bezahlt"] or 0)
    vz = "+" if delta >= 0 else ""
    return (f"{kopf}\n\nSeit {erster['datum']}: {vz}{euro(delta)} bezahlt "
            f"({len(rows)} Datensätze)")
