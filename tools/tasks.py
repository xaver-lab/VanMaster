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

Die Grammatik selbst wohnt in ``tools/kern/format.py``; das Lesen in
``tools/kern/lesen.py``. Dieses Modul liefert nur die flache Dict-Sicht, die
die bestehenden Aufrufer erwarten, plus die Auswertungen (Fortschritt,
nächste Aufgaben, Kurzbericht) und die schreibenden Befehle, die über
``tools.kern.aufgaben`` laufen (Quelle ``claude`` — dieses Modul wird nur
von der Kommandozeile aus benutzt, das Web schreibt über
``tools/server/app.py`` direkt gegen den Kern).
"""
from __future__ import annotations

from .common import STANDARD_SORTIERUNG, bar, fail
from .kern import aufgaben as kern_aufgaben
from .kern import datei as kern_datei
from .kern.format import BOX_ZEICHEN, ERLEDIGT, PRIOS
from .kern.lesen import aufgaben_lesen


def _als_dict(a) -> dict:
    return {
        "id": a.id, "titel": a.titel, "status": a.status, "bereich": a.bereich,
        "gruppe": a.gruppe, "ebene": a.ebene, "eltern": a.eltern,
        "kinder": list(a.kinder), "braucht": list(a.braucht), "prio": a.prio,
        "dauer": a.dauer, "beschreibung": a.beschreibung,
        "datei": a.datei, "zeile": a.zeile,
    }


def load() -> list[dict]:
    """Alle Aufgaben aller Bereichsdateien, flach mit Eltern-/Kind-Bezügen."""
    return [_als_dict(a) for a in aufgaben_lesen()]


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
    kern_aufgaben.status_setzen(a["id"], status, None)
    lesbar = {"laeuft": "läuft"}
    return f"{a['titel']}: {lesbar.get(a['status'], a['status'])} → {lesbar.get(status, status)}"


def add(bereich: str, titel: str, *, gruppe: str = "", unter: str = "",
        prio: str = "") -> str:
    """Legt eine neue Aufgabe an — ans Ende von Abschnitt/Gruppe/Elternaufgabe."""
    try:
        kennung, _ = kern_aufgaben.anlegen(
            bereich, titel, None, prio=prio,
            gruppe=gruppe or None, eltern_id=unter or None)
    except (ValueError, kern_datei.Konflikt) as fehler:
        fail(str(fehler))
    return f"Angelegt: {titel} [{kennung}]"


def delete(task_id: str) -> str:
    """Löscht eine Aufgabe mit allen Unterpunkten."""
    aufgaben = load()
    a = find(task_id, aufgaben)
    if a is None:
        fail(f"Keine Aufgabe zu '{task_id}' gefunden.")
    kinder = len(a["kinder"])
    try:
        kern_aufgaben.loeschen(a["id"], None)
    except (ValueError, kern_datei.Konflikt) as fehler:
        fail(str(fehler))
    wort = "Unterpunkt" if kinder == 1 else "Unterpunkte"
    return f"Gelöscht: {a['titel']} ({kinder} {wort})"


def rename(task_id: str, titel: str) -> str:
    aufgaben = load()
    a = find(task_id, aufgaben)
    if a is None:
        fail(f"Keine Aufgabe zu '{task_id}' gefunden.")
    try:
        kern_aufgaben.titel_setzen(a["id"], titel, None)
    except (ValueError, kern_datei.Konflikt) as fehler:
        fail(str(fehler))
    return f"{a['titel']} → {titel}"


def set_description(task_id: str, text: str) -> str:
    """Setzt/ersetzt die Beschreibung einer Aufgabe — Blockquote-Zeilen direkt
    darunter, im gleichen Einzug wie ihre Unterpunkte."""
    aufgaben = load()
    a = find(task_id, aufgaben)
    if a is None:
        fail(f"Keine Aufgabe zu '{task_id}' gefunden.")
    kern_aufgaben.beschreibung_setzen(a["id"], text, None)
    neue = text.strip()
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
