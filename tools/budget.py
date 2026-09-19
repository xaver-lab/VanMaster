"""Budget: Zielbudget und Kategorie-Budgets aus dem Kopf von vault/Camper.md,
Soll/Ist gegen die Stückliste (data/parts.csv).

Das Zielbudget steht dort, weil ``vault/Camper.md`` schon heute die einzige
projektweite Datei mit YAML-Kopf ist (``projekt``, ``fahrzeug``) — genau der
Ort für eine weitere von Hand gepflegte, projektweite Zahl, statt eine neue
Ablage nur dafür zu erfinden. Gelesen wird nur, nie geschrieben: die Zahl
trägt der Nutzer selbst ein (FORMAT.md §11).

Bezahlt = Teile mit Status Bestellt/Geliefert/Verbaut (Geld ist geflossen).
Geplant = Teile mit Status Idee/Recherche/Entschieden (noch nicht gekauft).
Prognose = Bezahlt + Geplant.
"""
from __future__ import annotations

from . import parts
from .common import (
    CAMPER_MD, PART_KATEGORIEN, bar, euro, read_text, slug, split_frontmatter,
    table,
)

BEZAHLT_STATUS = ("Bestellt", "Geliefert", "Verbaut")
GEPLANT_STATUS = ("Idee", "Recherche", "Entschieden")


def _num(value) -> float | None:
    if value in (None, "", []):
        return None
    try:
        return float(str(value).replace(",", ".").strip())
    except ValueError:
        return None


def kategorie_feld(kategorie: str) -> str:
    return f"budget_{slug(kategorie)}"


def ziel() -> dict:
    """Zielbudget und Kategorie-Budgets aus dem Kopf von vault/Camper.md.
    Fehlt die Datei oder das Feld, ist der Wert ``None``."""
    if not CAMPER_MD.exists():
        return {"gesamt": None, "kategorien": {}}
    meta, _ = split_frontmatter(read_text(CAMPER_MD))
    kategorien = {}
    for kat in PART_KATEGORIEN:
        wert = _num(meta.get(kategorie_feld(kat)))
        if wert is not None:
            kategorien[kat] = wert
    return {"gesamt": _num(meta.get("budget")), "kategorien": kategorien}


def daten() -> dict:
    """Kennzahlen für Text- und JSON-Ausgabe von ``camper budget``."""
    rows = parts.load()
    bezahlt_rows = [r for r in rows if r["status"] in BEZAHLT_STATUS]
    geplant_rows = [r for r in rows if r["status"] in GEPLANT_STATUS]
    bezahlt = round(parts.summe(bezahlt_rows), 2)
    geplant = round(parts.summe(geplant_rows), 2)
    prognose = round(bezahlt + geplant, 2)

    z = ziel()
    zg = z["gesamt"]

    kategorien = []
    for kat in PART_KATEGORIEN:
        krows = [r for r in rows if r["kategorie"] == kat]
        if not krows:
            continue
        kb = round(parts.summe([r for r in krows if r["status"] in BEZAHLT_STATUS]), 2)
        kp = round(parts.summe([r for r in krows if r["status"] in GEPLANT_STATUS]), 2)
        kategorien.append({
            "kategorie": kat, "bezahlt": kb, "geplant": kp,
            "prognose": round(kb + kp, 2),
            "budget": z["kategorien"].get(kat),
        })

    return {
        "ziel": zg,
        "bezahlt": bezahlt,
        "geplant": geplant,
        "prognose": prognose,
        "rest": round(zg - bezahlt, 2) if zg is not None else None,
        "differenz_prognose": round(prognose - zg, 2) if zg is not None else None,
        "kategorien": kategorien,
    }


def _vz(wert: float) -> str:
    """Betrag mit vorangestelltem Vorzeichen bei Überschreitung."""
    return ("+" if wert >= 0 else "") + euro(wert)


def text() -> str:
    d = daten()
    zeilen: list[str] = []

    if d["ziel"] is None:
        zeilen.append(
            "Kein Zielbudget gesetzt. Eintragen im Kopf von vault/Camper.md, "
            "z. B.:\n  budget: 25000\n"
            "Optional je Kategorie, z. B.:\n  budget_elektrik: 4000"
        )
    else:
        zeilen.append(f"Ziel:      {euro(d['ziel'])}")
        zeilen.append(f"Bezahlt:   "
                       f"{bar(round(min(d['bezahlt'], d['ziel'])), round(d['ziel']))}"
                       f"  {euro(d['bezahlt'])}")
        zeilen.append(f"Geplant:   {euro(d['geplant'])} (noch nicht gekauft)")
        zeilen.append(f"Prognose:  {euro(d['prognose'])} "
                       f"({_vz(d['differenz_prognose'])} ggü. Ziel)")
        zeilen.append(f"Rest:      {euro(d['rest'])} im Ziel noch nicht bezahlt")

    if d["kategorien"]:
        zeilen.append("")
        body = []
        for k in d["kategorien"]:
            budget_txt = euro(k["budget"]) if k["budget"] is not None else "—"
            balken = bar(round(min(k["bezahlt"], k["budget"])), round(k["budget"])) \
                if k["budget"] else ""
            body.append([k["kategorie"], euro(k["bezahlt"]), euro(k["geplant"]),
                        euro(k["prognose"]), budget_txt, balken])
        zeilen.append(table(
            body, ["Kategorie", "Bezahlt", "Geplant", "Prognose", "Budget", ""]))

    return "\n".join(zeilen)
