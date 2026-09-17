"""Lageberichte — kurz genug, um sie direkt in den Chat zu stellen."""
from __future__ import annotations

from . import parts, tasks
from .common import (
    ENTSCHEIDUNGEN_DIR, PART_STATUS, RECHERCHE_DIR, VAULT,
    bar, euro, read_text, split_frontmatter,
)


def offene_entscheidungen() -> list[str]:
    if not ENTSCHEIDUNGEN_DIR.exists():
        return []
    offen = []
    for datei in sorted(ENTSCHEIDUNGEN_DIR.glob("*.md")):
        meta, _ = split_frontmatter(read_text(datei))
        if str(meta.get("status", "offen")).lower() != "entschieden":
            offen.append(datei.stem)
    return offen


def brief() -> str:
    """Ein Absatz: Fortschritt, Kosten, nächster Schritt, offene Entscheidungen."""
    alle = tasks.load()
    fertig, gesamt_n = tasks.fortschritt(alle)
    teile = parts.load()
    kosten = parts.summe(teile)
    bezahlt = parts.summe([t for t in teile
                           if t["status"] in ("Bestellt", "Geliefert", "Verbaut")])

    zeilen = [
        f"Aufgaben {bar(fertig, gesamt_n)}"
        f"  ·  Teile {len(teile)}  ·  Kosten {euro(kosten)} "
        f"(davon bestellt/da: {euro(bezahlt)})"
        f"  ·  Gewicht {parts.gewicht_summe(teile):.0f} kg",
    ]

    nach_id = {a["id"]: a for a in alle}
    offen = [a for a in tasks.blaetter(alle) if a["status"] not in tasks.ERLEDIGT]
    frei = [a for a in offen if not tasks.blocker(a, nach_id)]
    frei.sort(key=lambda a: (tasks.PRIOS.get(a["prio"], 2), a["bereich"]))
    if frei:
        naechste = ", ".join(f"{a['titel']} [{a['id']}]" for a in frei[:3])
        zeilen.append(f"Als Nächstes: {naechste}")

    bestellen = [t for t in teile if t["status"] == "Entschieden"]
    if bestellen:
        zeilen.append(f"Zu bestellen: {len(bestellen)} Teile für "
                      f"{euro(parts.summe(bestellen))}")

    offen_e = offene_entscheidungen()
    if offen_e:
        zeilen.append(f"Offene Entscheidungen: {', '.join(offen_e[:4])}")
    return "\n".join(zeilen)


def full() -> str:
    teile = parts.load()
    bloecke = [brief(), "", tasks.overview_text(), "", parts.overview_text()]

    zeilen = []
    for st in PART_STATUS:
        n = len([t for t in teile if t["status"] == st])
        if n:
            zeilen.append(f"  {st:<14} {n:>3}")
    if zeilen:
        bloecke += ["", "Teile nach Status", *zeilen]

    offen_e = offene_entscheidungen()
    if offen_e:
        bloecke += ["", "Offene Entscheidungen",
                    *[f"  - {e}" for e in offen_e]]
    return "\n".join(bloecke)


def system(name: str) -> str:
    """Lage eines Systems: Aufgaben, Teile, Kosten, Gewicht, Strom."""
    name_l = name.lower()
    alle = tasks.load()
    saufgaben = [a for a in alle if a["bereich"].lower() == name_l
                 or a["gruppe"].lower() == name_l]
    teile = [t for t in parts.load()
             if name_l in (t["system"].lower(), t["kategorie"].lower())]
    if not saufgaben and not teile:
        return f"Zu '{name}' ist noch nichts hinterlegt."

    kopf = f"System {name}"
    zeilen = [kopf, "─" * len(kopf)]
    if saufgaben:
        fertig, gesamt_n = tasks.fortschritt(saufgaben)
        zeilen.append(f"Aufgaben {bar(fertig, gesamt_n)}")
        offen = [a for a in tasks.blaetter(saufgaben)
                 if a["status"] not in tasks.ERLEDIGT]
        zeilen += [f"  offen: {a['titel']} [{a['id']}]" for a in offen[:5]]
    if teile:
        zeilen.append(f"\nTeile: {len(teile)} · {euro(parts.summe(teile))} · "
                      f"{parts.gewicht_summe(teile):.1f} kg")
        for t in sorted(teile, key=lambda t: t["status"]):
            kenn = f" · {t['kennwerte']}" if t["kennwerte"] else ""
            zeilen.append(f"  {t['status']:<12} {t['titel']}{kenn}")

    seite = VAULT / "Systeme" / f"{name.capitalize()}.md"
    if seite.exists():
        zeilen.append(f"\nSystemseite: {seite.relative_to(VAULT.parent)}")
    return "\n".join(zeilen)


def find(text: str) -> str:
    """Volltextsuche über den Vault und die Stückliste — liefert Pfade."""
    nadel = text.lower()
    treffer = []
    for datei in sorted(VAULT.rglob("*.md")):
        try:
            inhalt = read_text(datei)
        except OSError:
            continue
        for nr, zeile in enumerate(inhalt.splitlines(), start=1):
            if nadel in zeile.lower():
                treffer.append((f"{datei.relative_to(VAULT.parent)}:{nr}",
                                zeile.strip()[:90]))
                break
    teile = parts.filtered(parts.load(), text=text)
    zeilen = []
    if treffer:
        zeilen.append("Vault:")
        zeilen += [f"  {pfad}\n      {vorschau}" for pfad, vorschau in treffer[:12]]
    if teile:
        zeilen.append("\nStückliste:")
        zeilen += [f"  {t['titel']} [{t['id']}] · {t['status']}" for t in teile[:12]]
    if not zeilen:
        return f"Nichts zu '{text}' gefunden."
    if RECHERCHE_DIR.exists() and not treffer:
        zeilen.append("\n(nichts im Recherche-Ordner — vielleicht lohnt eine Suche)")
    return "\n".join(zeilen)
