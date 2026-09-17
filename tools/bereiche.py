"""Arbeitsbereiche: eine Datei je Bereich in vault/Bereiche/.

Eine Bereichsdatei ist die Heimat eines Themas — Beschreibung, Stand des
Wissens, Auslegung, lose Notizen, Links und die Aufgaben. Bilder, Teile,
Einzelteile und Modelle stehen nicht darin, sie werden beim Anzeigen
dazugemischt (siehe tools/status.py und tools/build.py).

Aufbau:

    ---
    bereich: Möbel
    kurz: Bett, Küchenblock, Hängeschränke
    status: in-arbeit
    phase: 4
    ---

`phase:` ist die Nummer des Bauabschnitts (1 = zuerst). Fehlt sie, sortiert der
Bereich hinten — die Dateien müssen nicht alle gleichzeitig umgestellt werden.

    # Möbel

    ## Beschreibung
    ## Stand
    ## Auslegung
    ## Notizen
    ## Links
    ## Aufgaben
"""
from __future__ import annotations

import re

from .common import (
    BEREICHE_DIR, SORTIERUNGEN, STANDARD_SORTIERUNG, abschnitte, read_text,
    split_frontmatter,
)

# - [Titel](url) — Zusatz   ·   der Zusatz ist freiwillig
LINK = re.compile(r"^\s*-\s*\[(?P<titel>[^\]]+)\]\((?P<url>[^)]+)\)\s*(?:[—-]\s*(?P<zusatz>.*))?$")

LEER = re.compile(r"^_\(.*\)_$")


def _sauber(text: str) -> str:
    """Platzhalter wie _(noch nichts eingetragen)_ zählen als leer."""
    text = text.strip()
    return "" if LEER.match(text) else text


def links(text: str) -> list[dict]:
    gefunden = []
    for zeile in text.splitlines():
        t = LINK.match(zeile)
        if t:
            gefunden.append({
                "titel": t.group("titel").strip(),
                "url": t.group("url").strip(),
                "zusatz": (t.group("zusatz") or "").strip(),
            })
    return gefunden


def load() -> list[dict]:
    """Alle Bereichsdateien, in Abschnitte zerlegt."""
    bereiche = []
    if not BEREICHE_DIR.exists():
        return bereiche
    for datei in sorted(BEREICHE_DIR.glob("*.md")):
        meta, body = split_frontmatter(read_text(datei))
        teile = abschnitte(body)
        bereiche.append({
            "name": meta.get("bereich") or datei.stem,
            "kurz": meta.get("kurz", ""),
            "status": meta.get("status", "geplant"),
            "phase": phase(meta.get("phase")),
            "beschreibung": _sauber(teile.get("Beschreibung", "")),
            "stand": _sauber(teile.get("Stand", "")),
            "auslegung": _sauber(teile.get("Auslegung", "")),
            "notizen": _sauber(teile.get("Notizen", "")),
            "links": links(teile.get("Links", "")),
            "datei": str(datei.relative_to(BEREICHE_DIR.parent.parent)).replace("\\", "/"),
        })
    return bereiche

# ------------------------------------------------------------- Sortierung
#
# Die einzige Stelle, an der die Reihenfolge der Bereiche festgelegt wird.
# Das Dashboard übernimmt sie aus docs/data.json und sortiert nur für den
# Wechsler selbst um (docs/app.js, bereicheSortiert) — dieselben Regeln.

# Baustellen zuerst: woran gearbeitet wird, vor dem, was noch ansteht.
STATUS_RANG = {"in-arbeit": 0, "geplant": 1, "fertig": 2}

OHNE_PHASE = 999  # kein `phase:` im Kopf → hinten, aber nicht weg.


def phase(wert) -> int | None:
    """`phase: 2` aus dem Kopf — alles Unbrauchbare zählt als nicht gesetzt."""
    try:
        return int(str(wert).strip())
    except (TypeError, ValueError):
        return None


def _offen(b: dict) -> int:
    return max(int(b.get("gesamt") or 0) - int(b.get("fertig") or 0), 0)


def schluessel(art: str):
    """Sortierschlüssel für einen Bereich — erwartet fertig/gesamt am Eintrag."""
    def nach_name(b):
        return b["name"].lower()
    if art == "name":
        return nach_name
    if art == "phase":
        # Innerhalb eines Abschnitts weiter wie bei "baustellen", damit auch
        # dort das Naheliegende oben steht.
        return lambda b: (b.get("phase") if b.get("phase") is not None else OHNE_PHASE,
                          STATUS_RANG.get(b.get("status"), 1), -_offen(b), nach_name(b))
    return lambda b: (STATUS_RANG.get(b.get("status"), 1), -_offen(b), nach_name(b))


def sortiere(alle: list[dict], art: str = STANDARD_SORTIERUNG) -> list[dict]:
    if art not in SORTIERUNGEN:
        art = STANDARD_SORTIERUNG
    return sorted(alle, key=schluessel(art))


def mit_fortschritt(alle: list[dict] | None = None) -> list[dict]:
    """Bereiche samt fertig/gesamt — ohne die zählt keine Sortierung richtig."""
    from . import tasks

    nach_b = tasks.nach_bereich(tasks.load())
    ergebnis = []
    for b in (load() if alle is None else alle):
        fertig, gesamt = tasks.fortschritt(nach_b.get(b["name"], []))
        ergebnis.append({**b, "fertig": fertig, "gesamt": gesamt})
    return ergebnis


def reihenfolge(art: str = STANDARD_SORTIERUNG) -> list[str]:
    """Nur die Namen, in der gewählten Reihenfolge — für Listen und Gruppen."""
    return [b["name"] for b in sortiere(mit_fortschritt(), art)]


def namen() -> list[str]:
    return [b["name"] for b in load()]


def find(name: str, alle: list[dict] | None = None) -> dict | None:
    alle = load() if alle is None else alle
    gesucht = name.strip().lower()
    for b in alle:
        if b["name"].lower() == gesucht:
            return b
    treffer = [b for b in alle if gesucht in b["name"].lower()]
    return treffer[0] if len(treffer) == 1 else None


def overview_text(sortierung: str = STANDARD_SORTIERUNG) -> str:
    from .common import SORT_WORT, bar, table

    alle = sortiere(mit_fortschritt(), sortierung)
    if not alle:
        return "Noch keine Bereiche in vault/Bereiche/."
    zeilen = []
    for b in alle:
        ph = b.get("phase")
        zeilen.append([
            b["name"], str(ph) if ph is not None else "—", b["status"],
            f"{b['fertig']}/{b['gesamt']}" if b["gesamt"] else "—",
            bar(b["fertig"], b["gesamt"]) if b["gesamt"] else "",
            b["kurz"],
        ])
    kopf = table(zeilen, ["Bereich", "Ph", "Status", "Aufgaben", "", "Kurz"])
    return f"{kopf}\n\nSortierung: {SORT_WORT.get(sortierung, sortierung)}"
