"""Zuladungsbilanz: Gewicht aus data/parts.csv + data/bauteile.csv gegen das
zulässige Gesamtgewicht des Fahrzeugs (FORMAT.md §13).

Die Fahrzeug-Kenndaten (`leergewicht_kg`, `zul_gesamtgewicht_kg`) stehen im
Kopf von ``vault/Camper.md`` — genau wie das Zielbudget in ``tools/budget.py``
ist das die einzige projektweite Datei mit YAML-Kopf, statt eine eigene
Ablage nur für zwei Zahlen zu erfinden. Gelesen wird nur, nie geschrieben:
der Nutzer trägt die Werte aus dem Fahrzeugschein selbst ein.
"""
from __future__ import annotations

from . import bauteile, parts
from .common import CAMPER_MD, bar, read_text, split_frontmatter

SCHWELLE_WARNUNG = 0.9  # ab 90 % der zulässigen Zuladung wird gewarnt


def _num(value) -> float | None:
    if value in (None, "", []):
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except ValueError:
        return None


def fahrzeug() -> dict:
    """`leergewicht_kg`/`zul_gesamtgewicht_kg` aus dem Kopf von
    vault/Camper.md. Fehlt die Datei oder ein Feld, ist der Wert ``None``."""
    if not CAMPER_MD.exists():
        return {"leergewicht_kg": None, "zul_gesamtgewicht_kg": None}
    meta, _ = split_frontmatter(read_text(CAMPER_MD))
    return {
        "leergewicht_kg": _num(meta.get("leergewicht_kg")),
        "zul_gesamtgewicht_kg": _num(meta.get("zul_gesamtgewicht_kg")),
    }


def bilanz() -> dict:
    """Kennzahlen für Text- und JSON-Ausgabe von ``camper gewicht``."""
    teile = parts.load()
    einzelteile = bauteile.load()

    teile_kg = round(parts.gewicht_summe(teile), 1)
    teile_fehlt = len([r for r in teile if not str(r.get("gewicht_kg") or "").strip()])
    bauteile_kg, bauteile_fehlt = bauteile.gewicht_summe(einzelteile)
    bauteile_kg = round(bauteile_kg, 1)

    fz = fahrzeug()
    leer, zul = fz["leergewicht_kg"], fz["zul_gesamtgewicht_kg"]
    zuladung_erlaubt = (round(zul - leer, 1)
                        if leer is not None and zul is not None else None)

    return {
        "teile_kg": teile_kg, "teile_fehlt": teile_fehlt, "teile_gesamt": len(teile),
        "bauteile_kg": bauteile_kg, "bauteile_fehlt": bauteile_fehlt,
        "bauteile_gesamt": len(einzelteile),
        "ausbau_kg": round(teile_kg + bauteile_kg, 1),
        "leergewicht_kg": leer, "zul_gesamtgewicht_kg": zul,
        "zuladung_erlaubt_kg": zuladung_erlaubt,
    }


def text() -> str:
    d = bilanz()
    zeilen = [
        f"Stückliste:  {d['teile_kg']:.1f} kg "
        f"({d['teile_gesamt'] - d['teile_fehlt']}/{d['teile_gesamt']} Teile mit Gewicht)",
        f"Einzelteile: {d['bauteile_kg']:.1f} kg "
        f"({d['bauteile_gesamt'] - d['bauteile_fehlt']}/{d['bauteile_gesamt']} Teile mit Gewicht)",
        f"Ausbau gesamt: {d['ausbau_kg']:.1f} kg",
    ]
    fehlt = d["teile_fehlt"] + d["bauteile_fehlt"]
    if fehlt:
        zeilen.append(f"⚠ {fehlt} Teile ohne Gewichtsangabe — die Bilanz ist "
                      "unvollständig, nicht zu niedrig verlassen.")

    zeilen.append("")
    beispiel = {"leergewicht_kg": 2100, "zul_gesamtgewicht_kg": 3500}
    fehlende = [feld for feld in beispiel if d[feld] is None]
    if fehlende:
        namen = {"leergewicht_kg": "Leergewicht",
                 "zul_gesamtgewicht_kg": "zulässiges Gesamtgewicht"}
        zeilen.append(
            "Keine Zuladungsbilanz: "
            + " und ".join(namen[feld] for feld in fehlende)
            + " fehlt im Kopf von vault/Camper.md. Aus dem Fahrzeugschein "
              "eintragen, z. B.:\n"
            + "\n".join(f"  {feld}: {beispiel[feld]}" for feld in fehlende))
        return "\n".join(zeilen)

    zuladung = d["zuladung_erlaubt_kg"]
    zeilen.append(
        f"Zulässige Zuladung: {zuladung:.0f} kg "
        f"(zul. Gesamtgewicht {d['zul_gesamtgewicht_kg']:.0f} kg − "
        f"Leergewicht {d['leergewicht_kg']:.0f} kg)")

    if zuladung <= 0:
        zeilen.append("⚠ Zuladung ist 0 kg oder weniger — Werte in "
                      "vault/Camper.md prüfen.")
        return "\n".join(zeilen)

    genutzt = round(min(d["ausbau_kg"], zuladung))
    zeilen.append(bar(genutzt, round(zuladung))
                 + f"  {d['ausbau_kg']:.0f} / {zuladung:.0f} kg")
    anteil = d["ausbau_kg"] / zuladung
    if anteil >= SCHWELLE_WARNUNG:
        wort = "über" if anteil > 1 else "nahe an"
        zeilen.append(f"⚠ Ausbau liegt {wort} der zulässigen Zuladung "
                      f"({anteil * 100:.0f} %).")
    return "\n".join(zeilen)
