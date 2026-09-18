"""Aufgabenbaum: verschachtelte Checkboxen in vault/Bereiche/*.md.

Zeilenformat, so wie Obsidian es nativ abhakt:

    - [ ] Batteriehalterung bauen ^batteriehalterung #hoch @dauer:3h
      > Wie: Winkel aus 3mm Alu, an die Querträger geschraubt.
      - [x] Maße nehmen
    - [ ] Batterien anschließen ^batterien-anschliessen @braucht:batteriehalterung

Kästchen: [ ] offen · [/] läuft · [!] blockiert · [x] erledigt · [-] verworfen.
Marken: ^kennung (Obsidian-Blockanker) · #prio · @braucht:<kennung> · @dauer:<text>
Direkt unter einer Aufgabe stehende Blockquote-Zeilen (`> …`) sind ihre
Beschreibung ("wie wird das gemacht") — mehrere Zeilen werden aneinandergereiht.

Gelesen wird nur der Abschnitt "## Aufgaben" einer Bereichsdatei — eine
Checkbox in den Notizen ist ein Merker, keine Aufgabe.
"""
from __future__ import annotations

from pathlib import Path

from .common import (
    BEREICHE_DIR, STANDARD_SORTIERUNG, bar, fail, read_text, slug,
    split_frontmatter,
)
from .kern.format import (
    ANKER, BESCHREIBUNG, BOX, BOX_ZEICHEN, ERLEDIGT, MARKE, PRIO, PRIOS,
    ZEILE, ebene,
)


def load() -> list[dict]:
    """Alle Aufgaben aller Bereichsdateien, flach mit Eltern-/Kind-Bezügen."""
    aufgaben: list[dict] = []
    if not BEREICHE_DIR.exists():
        return aufgaben
    for datei in sorted(BEREICHE_DIR.glob("*.md")):
        meta, _ = split_frontmatter(read_text(datei))
        bereich = meta.get("bereich") or datei.stem
        gruppe = ""
        drin = False
        stapel: dict[int, str] = {}
        letzte_aufgabe: dict | None = None
        for nr, zeile in enumerate(read_text(datei).splitlines(), start=1):
            if zeile.startswith("## ") and not zeile.startswith("### "):
                drin = zeile[3:].strip().lower() == "aufgaben"
                gruppe = ""
                letzte_aufgabe = None
                continue
            if not drin:
                continue
            if zeile.startswith("#"):
                gruppe = zeile.lstrip("#").strip()
                letzte_aufgabe = None
                continue
            treffer = ZEILE.match(zeile)
            if not treffer:
                beschr = BESCHREIBUNG.match(zeile)
                if beschr and letzte_aufgabe is not None:
                    zusatz = beschr.group("text").rstrip()
                    letzte_aufgabe["beschreibung"] = (
                        f"{letzte_aufgabe['beschreibung']}\n{zusatz}"
                        if letzte_aufgabe["beschreibung"] else zusatz)
                continue
            tiefe = ebene(treffer.group("einzug"))
            rest = treffer.group("rest").strip()

            anker = ANKER.search(rest)
            kennung = anker.group(1) if anker else ""
            if anker:
                rest = ANKER.sub(" ", rest).strip()

            prio_t = PRIO.search(rest)
            prio = prio_t.group(1).lower() if prio_t else ""
            rest = PRIO.sub(" ", rest)

            braucht, dauer = [], ""
            for art, wert in MARKE.findall(rest):
                if art == "braucht":
                    braucht.extend(w for w in wert.split(",") if w)
                else:
                    dauer = wert
            titel = MARKE.sub("", rest).strip()

            if not kennung:
                kennung = slug(f"{bereich}-{titel}")[:60]
            neue_aufgabe = {
                "id": kennung,
                "titel": titel,
                "status": BOX[treffer.group("box")],
                "bereich": bereich,
                "gruppe": gruppe,
                "ebene": tiefe,
                "eltern": stapel.get(tiefe - 1, ""),
                "kinder": [],
                "braucht": braucht,
                "prio": prio,
                "dauer": dauer,
                "beschreibung": "",
                "datei": str(datei.relative_to(BEREICHE_DIR.parent.parent)),
                "zeile": nr,
            }
            aufgaben.append(neue_aufgabe)
            letzte_aufgabe = neue_aufgabe
            stapel[tiefe] = kennung
            for t in list(stapel):
                if t > tiefe:
                    del stapel[t]

    nach_id = {a["id"]: a for a in aufgaben}
    for a in aufgaben:
        if a["eltern"] in nach_id:
            nach_id[a["eltern"]]["kinder"].append(a["id"])
    return aufgaben


def blaetter(aufgaben: list[dict]) -> list[dict]:
    """Nur Aufgaben ohne Unterpunkte — daran misst sich der Fortschritt."""
    return [a for a in aufgaben if not a["kinder"]]


def fortschritt(aufgaben: list[dict]) -> tuple[int, int]:
    bl = blaetter(aufgaben)
    return len([a for a in bl if a["status"] in ERLEDIGT]), len(bl)


def nach_bereich(aufgaben: list[dict]) -> dict[str, list[dict]]:
    gruppen: dict[str, list[dict]] = {}
    for a in aufgaben:
        gruppen.setdefault(a["bereich"], []).append(a)
    return gruppen


def find(task_id: str, aufgaben: list[dict] | None = None) -> dict | None:
    aufgaben = load() if aufgaben is None else aufgaben
    gesucht = task_id.strip().lower()
    for a in aufgaben:
        if a["id"].lower() == gesucht:
            return a
    treffer = [a for a in aufgaben if gesucht in a["titel"].lower()]
    return treffer[0] if len(treffer) == 1 else None


def blocker(a: dict, nach_id: dict[str, dict]) -> list[dict]:
    return [nach_id[b] for b in a["braucht"]
            if b in nach_id and nach_id[b]["status"] not in ERLEDIGT]


def next_tasks(limit: int = 8, bereich: str = "",
               sortierung: str = STANDARD_SORTIERUNG) -> str:
    from . import bereiche

    aufgaben = load()
    if not aufgaben:
        return "Noch keine Aufgaben in vault/Bereiche/."
    nach_id = {a["id"]: a for a in aufgaben}
    offen = [a for a in blaetter(aufgaben) if a["status"] not in ERLEDIGT]
    if bereich:
        offen = [a for a in offen if a["bereich"].lower() == bereich.lower()]
    frei = [a for a in offen if not blocker(a, nach_id)]
    blockiert = [a for a in offen if blocker(a, nach_id)]
    ordnung = bereiche.reihenfolge(sortierung)
    frei.sort(key=lambda a: (PRIOS.get(a["prio"], 2), a["status"] != "laeuft",
                             ordnung.index(a["bereich"])
                             if a["bereich"] in ordnung else len(ordnung),
                             a["titel"]))

    zeilen = []
    for a in frei[:limit]:
        marke = " (läuft)" if a["status"] == "laeuft" else ""
        prio = f" · {a['prio']}" if a["prio"] else ""
        dauer = f" · {a['dauer']}" if a["dauer"] else ""
        zeilen.append(f"  {a['bereich']}: {a['titel']}{marke}{prio}{dauer}"
                      f"   [{a['id']}]")
    text = "Als Nächstes möglich:\n" + ("\n".join(zeilen) or "  (nichts offen)")
    if blockiert:
        text += "\n\nWartet noch:"
        for a in blockiert[:limit]:
            warum = ", ".join(b["titel"] for b in blocker(a, nach_id))
            text += f"\n  {a['titel']} — braucht: {warum}"
    return text


def brief(task_id: str) -> str:
    from . import parts

    aufgaben = load()
    a = find(task_id, aufgaben)
    if a is None:
        fail(f"Keine Aufgabe zu '{task_id}' gefunden.")
    nach_id = {x["id"]: x for x in aufgaben}

    kopf = f"{a['titel']}  [{a['id']}]"
    zeilen = [kopf, "─" * len(kopf),
              f"Bereich: {a['bereich']}"
              + (f" · {a['gruppe']}" if a["gruppe"] else "")
              + f" · Status: {a['status']}"
              + (f" · {a['prio']}" if a["prio"] else "")
              + (f" · {a['dauer']}" if a["dauer"] else "")]

    kinder = [nach_id[k] for k in a["kinder"]]
    if kinder:
        fertig = len([k for k in kinder if k["status"] in ERLEDIGT])
        zeilen.append(f"\nUnterpunkte {bar(fertig, len(kinder), 8)}")
        for k in kinder:
            zeilen.append(f"  [{BOX_ZEICHEN[k['status']]}] {k['titel']}")

    offene_blocker = blocker(a, nach_id)
    if offene_blocker:
        zeilen.append("\nBlockiert durch:")
        zeilen += [f"  - {b['titel']} [{b['id']}]" for b in offene_blocker]

    teile = [p for p in parts.load() if p["fuer_aufgabe"] == a["id"]]
    if teile:
        zeilen.append(f"\nTeile ({parts.euro(parts.summe(teile))}):")
        for p in teile:
            zeilen.append(f"  - {p['titel']} · {p['status']} · "
                          f"{parts.euro(parts.gesamt(p))}"
                          + (f" · {p['haendler']}" if p["haendler"] else ""))
        fehlt = [p for p in teile if p["status"] != "Verbaut"]
        if fehlt:
            wort = "Teil" if len(fehlt) == 1 else "Teile"
            zeilen.append(f"  → {len(fehlt)} {wort} noch nicht verbaut")

    zeilen.append(f"\nQuelle: {a['datei']}:{a['zeile']}")
    return "\n".join(zeilen)


def set_status(task_id: str, status: str) -> str:
    aufgaben = load()
    a = find(task_id, aufgaben)
    if a is None:
        fail(f"Keine Aufgabe zu '{task_id}' gefunden.")
    if status not in BOX_ZEICHEN:
        fail(f"Status muss einer von {', '.join(BOX_ZEICHEN)} sein.")
    datei = Path(BEREICHE_DIR.parent.parent / a["datei"])
    zeilen = read_text(datei).splitlines()
    i = a["zeile"] - 1
    treffer = ZEILE.match(zeilen[i])
    if not treffer:
        fail(f"Zeile {a['zeile']} in {a['datei']} passt nicht mehr — bitte 'sync'.")
    zeilen[i] = (f"{treffer.group('einzug')}- [{BOX_ZEICHEN[status]}] "
                 f"{treffer.group('rest').strip()}")
    datei.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="\n")
    return f"{a['titel']}: {a['status']} → {status}"


def set_description(task_id: str, text: str) -> str:
    """Setzt/ersetzt die Beschreibung einer Aufgabe — Blockquote-Zeilen direkt
    darunter, im gleichen Einzug wie ihre Unterpunkte."""
    aufgaben = load()
    a = find(task_id, aufgaben)
    if a is None:
        fail(f"Keine Aufgabe zu '{task_id}' gefunden.")
    datei = Path(BEREICHE_DIR.parent.parent / a["datei"])
    zeilen = read_text(datei).splitlines()
    i = a["zeile"] - 1
    treffer = ZEILE.match(zeilen[i])
    if not treffer:
        fail(f"Zeile {a['zeile']} in {a['datei']} passt nicht mehr — bitte 'sync'.")
    einzug = treffer.group("einzug").replace("\t", "  ") + "  "

    ende = i + 1
    while ende < len(zeilen) and BESCHREIBUNG.match(zeilen[ende]):
        ende += 1

    text = text.strip("\n")
    neue = [f"{einzug}> {z}" for z in text.splitlines()] if text.strip() else []
    zeilen[i + 1:ende] = neue
    datei.write_text("\n".join(zeilen) + "\n", encoding="utf-8", newline="\n")
    return f"{a['titel']}: Beschreibung {'gespeichert' if neue else 'gelöscht'}"


def overview_text(sortierung: str = "") -> str:
    from . import bereiche

    aufgaben = load()
    if not aufgaben:
        return "Noch keine Aufgaben in vault/Bereiche/."
    # Gleiche Reihenfolge wie Themenliste und Dashboard.
    gruppen = nach_bereich(aufgaben)
    ordnung = bereiche.reihenfolge(sortierung or STANDARD_SORTIERUNG)
    reihe = sorted(gruppen, key=lambda n: (ordnung.index(n) if n in ordnung
                                           else len(ordnung), n.lower()))
    zeilen = []
    for bereich in reihe:
        liste = gruppen[bereich]
        fertig, gesamt_n = fortschritt(liste)
        zeilen.append(f"  {bereich:<16} {bar(fertig, gesamt_n)}")
    fertig, gesamt_n = fortschritt(aufgaben)
    return ("Aufgaben\n" + "\n".join(zeilen)
            + f"\n  {'gesamt':<16} {bar(fertig, gesamt_n)}")
