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
    ---

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
    BEREICHE_DIR, abschnitte, read_text, split_frontmatter,
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
            "beschreibung": _sauber(teile.get("Beschreibung", "")),
            "stand": _sauber(teile.get("Stand", "")),
            "auslegung": _sauber(teile.get("Auslegung", "")),
            "notizen": _sauber(teile.get("Notizen", "")),
            "links": links(teile.get("Links", "")),
            "datei": str(datei.relative_to(BEREICHE_DIR.parent.parent)).replace("\\", "/"),
        })
    return bereiche


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


def overview_text() -> str:
    from .common import bar, table
    from . import tasks

    alle = load()
    if not alle:
        return "Noch keine Bereiche in vault/Bereiche/."
    nach_b = tasks.nach_bereich(tasks.load())
    zeilen = []
    for b in alle:
        fertig, gesamt = tasks.fortschritt(nach_b.get(b["name"], []))
        zeilen.append([
            b["name"], b["status"],
            f"{fertig}/{gesamt}" if gesamt else "—",
            bar(fertig, gesamt) if gesamt else "",
            b["kurz"],
        ])
    return table(zeilen, ["Bereich", "Status", "Aufgaben", "", "Kurz"])
