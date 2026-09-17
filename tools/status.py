"""Lageberichte — kurz genug, um sie direkt in den Chat zu stellen."""
from __future__ import annotations

from . import bauteile, bereiche, media, parts, tasks
from .common import (
    ENTSCHEIDUNGEN_DIR, PART_STATUS, RECHERCHE_DIR, STANDARD_SORTIERUNG, VAULT,
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


def brief(sortierung: str = STANDARD_SORTIERUNG) -> str:
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
    ordnung = bereiche.reihenfolge(sortierung)
    frei.sort(key=lambda a: (tasks.PRIOS.get(a["prio"], 2),
                             ordnung.index(a["bereich"])
                             if a["bereich"] in ordnung else len(ordnung)))
    if frei:
        naechste = ", ".join(f"{a['titel']} [{a['id']}]" for a in frei[:3])
        zeilen.append(f"Als Nächstes: {naechste}")

    bestellen = [t for t in teile if t["status"] == "Entschieden"]
    if bestellen:
        wort = "Teil" if len(bestellen) == 1 else "Teile"
        zeilen.append(f"Zu bestellen: {len(bestellen)} {wort} für "
                      f"{euro(parts.summe(bestellen))}")

    offen_e = offene_entscheidungen()
    if offen_e:
        zeilen.append(f"Offene Entscheidungen: {', '.join(offen_e[:4])}")
    return "\n".join(zeilen)


def full(sortierung: str = STANDARD_SORTIERUNG) -> str:
    teile = parts.load()
    bloecke = [brief(sortierung), "", tasks.overview_text(sortierung), "",
               parts.overview_text()]

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


def entscheidungen_zu(name: str) -> list[dict]:
    """Entscheidungsseiten, deren Bereich passt — offene zuerst."""
    if not ENTSCHEIDUNGEN_DIR.exists():
        return []
    name_l = name.lower()
    gefunden = []
    for datei in sorted(ENTSCHEIDUNGEN_DIR.glob("*.md")):
        meta, _ = split_frontmatter(read_text(datei))
        if str(meta.get("bereich", "")).lower() != name_l:
            continue
        gefunden.append({
            "titel": datei.stem,
            "status": str(meta.get("status", "offen")),
            "datei": str(datei.relative_to(VAULT.parent)).replace("\\", "/"),
        })
    gefunden.sort(key=lambda e: e["status"] == "entschieden")
    return gefunden


def bereich(name: str) -> str:
    """Der ganze Arbeitsbereich am Stück — Text zum Weiterreden.

    Alles, was zu einem Thema bekannt ist: Beschreibung, Stand, Notizen,
    Links, Aufgaben, gekaufte Teile, Einzelteile mit Maßen, Bilder, Modelle
    und offene Entscheidungen.
    """
    b = bereiche.find(name)
    name_l = (b["name"] if b else name).lower()

    alle = tasks.load()
    baufgaben = [a for a in alle if a["bereich"].lower() == name_l]
    teile = [t for t in parts.load()
             if name_l in (t["system"].lower(), t["kategorie"].lower())]
    einzel = [r for r in bauteile.load() if r["bereich"].lower() == name_l]
    dateien = [(d, art) for d, ber, art in media.ablage()
               if ber.lower() == name_l]
    ent = entscheidungen_zu(b["name"] if b else name)

    if not b and not baufgaben and not teile and not einzel:
        return f"Zu '{name}' ist noch nichts hinterlegt."

    titel = b["name"] if b else name
    kopf = f"Bereich {titel}"
    zeilen = [kopf, "═" * len(kopf)]
    if b and b["kurz"]:
        zeilen.append(b["kurz"])
    if baufgaben:
        fertig, gesamt_n = tasks.fortschritt(baufgaben)
        zeilen.append(f"Aufgaben {bar(fertig, gesamt_n)}"
                      + (f"  ·  Status {b['status']}" if b else ""))

    for ueberschrift, schluessel in (("Beschreibung", "beschreibung"),
                                     ("Stand", "stand"),
                                     ("Auslegung", "auslegung"),
                                     ("Notizen", "notizen")):
        if b and b[schluessel]:
            zeilen += ["", ueberschrift, "─" * len(ueberschrift), b[schluessel]]

    if b and b["links"]:
        zeilen += ["", "Links", "─────"]
        for l in b["links"]:
            zusatz = f" — {l['zusatz']}" if l["zusatz"] else ""
            zeilen.append(f"  {l['titel']}: {l['url']}{zusatz}")

    if baufgaben:
        nach_id = {a["id"]: a for a in alle}
        zeilen += ["", "Aufgaben", "────────"]
        for a in baufgaben:
            marke = {"offen": " ", "laeuft": "/", "erledigt": "x",
                     "verworfen": "-"}[a["status"]]
            blockiert = tasks.blocker(a, nach_id)
            hinweis = ""
            if blockiert:
                hinweis = " ← wartet auf " + ", ".join(x["titel"] for x in blockiert)
            prio = f" #{a['prio']}" if a["prio"] else ""
            zeilen.append(f"  [{marke}] {a['titel']} [{a['id']}]{prio}{hinweis}")

    if teile:
        zeilen += ["", f"Teile aus der Stückliste — {len(teile)} · "
                       f"{euro(parts.summe(teile))} · "
                       f"{parts.gewicht_summe(teile):.1f} kg",
                   "─" * 40]
        for t in sorted(teile, key=lambda t: t["status"]):
            kenn = f" · {t['kennwerte']}" if t["kennwerte"] else ""
            zeilen.append(f"  {t['status']:<12} {t['titel']}{kenn}")

    if einzel:
        qm = bauteile.flaeche_summe(einzel)
        zeilen += ["", f"Einzelteile — {len(einzel)}"
                       + (f" · {qm:.2f} m²" if qm else ""),
                   "─" * 40]
        for r in sorted(einzel, key=lambda r: r["titel"]):
            mass = bauteile.mass_text(r) or "Maß offen"
            anz = f"{bauteile.anzahl(r):g}x " if bauteile.anzahl(r) != 1 else ""
            quelle = f" ({r['massquelle']})" if r["massquelle"] else ""
            aus = f" aus [{r['teil_id']}]" if r["teil_id"] else ""
            zeilen.append(f"  {r['status']:<14} {anz}{r['titel']} · "
                          f"{mass}{quelle} · {r['material']}{aus}")

    bilder = [d for d, art in dateien if art == "bild"]
    docs = [d for d, art in dateien if art == "dokument"]
    modelle = [d for d, art in dateien if art == "modell"]
    for beschriftung, liste in (("Bilder", bilder), ("Dokumente", docs),
                                ("3D-Modelle", modelle)):
        if liste:
            zeilen += ["", f"{beschriftung} ({len(liste)})"]
            zeilen += [f"  {d.name}" for d in liste]

    if ent:
        zeilen += ["", "Entscheidungen", "──────────────"]
        for e in ent:
            zeilen.append(f"  {e['status']:<12} {e['titel']}")

    if b:
        zeilen.append(f"\nBereichsseite: {b['datei']}")
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
