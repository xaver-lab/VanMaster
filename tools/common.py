"""Gemeinsame Helfer: Pfade, Slugs, YAML-Kopf, Textausgabe."""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VAULT = ROOT / "vault"
DATA = ROOT / "data"
GENERATED = DATA / "generated"
DOCS = ROOT / "docs"
INPUT = ROOT / "_input"

PARTS_CSV = DATA / "parts.csv"
PARTS_XLSX = GENERATED / "Stueckliste.xlsx"
DASHBOARD_JSON = DOCS / "data.json"

TASKS_DIR = VAULT / "Aufgaben"
PARTS_MD_DIR = VAULT / "Stückliste"
SYSTEME_DIR = VAULT / "Systeme"
ENTSCHEIDUNGEN_DIR = VAULT / "Entscheidungen"
ANLEITUNGEN_DIR = VAULT / "Anleitungen"
RECHERCHE_DIR = VAULT / "Recherche"
MEDIEN_DIR = VAULT / "Medien"

# Reihenfolge = Fortschritt eines Teils vom Einfall bis zum Einbau.
PART_STATUS = ["Idee", "Recherche", "Entschieden", "Bestellt", "Geliefert", "Verbaut"]
PART_PRIO = ["Kritisch", "Hoch", "Mittel", "Nice-to-have"]
PART_KATEGORIEN = [
    "Dämmung", "Elektrik", "Wasser", "Heizung", "Möbel", "Küche",
    "Stauraum", "Werkzeug", "Verbrauchsmaterial",
]

_UMLAUTE = {"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"}


def slug(text: str) -> str:
    """Kleingeschriebene, ASCII-sichere Kennung — stabil über Umlaute hinweg."""
    text = text.strip().lower()
    for k, v in _UMLAUTE.items():
        text = text.replace(k, v)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n",
    )


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Winziger YAML-Kopf-Leser — nur flache `schlüssel: wert`-Paare und Listen."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("\n---", 1)
    if len(parts) != 2:
        return {}, text
    head, body = parts[0][3:], parts[1].lstrip("-").lstrip("\n")
    meta: dict = {}
    key = None
    for line in head.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        if line.lstrip().startswith("- ") and key:
            meta.setdefault(key, [])
            if isinstance(meta[key], list):
                meta[key].append(line.lstrip()[2:].strip().strip("\"'"))
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip("\"'")
            meta[key] = value if value else []
    return meta, body


def frontmatter(meta: dict) -> str:
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {v}" for v in value)
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines)


def euro(value: float) -> str:
    return f"{value:,.2f} €".replace(",", "\u00a0").replace(".", ",", 1)


def bar(done: int, total: int, width: int = 12) -> str:
    """Fortschrittsbalken für die Textausgabe im Chat."""
    if total <= 0:
        return "─" * width + "   —"
    filled = round(width * done / total)
    return "█" * filled + "░" * (width - filled) + f" {done}/{total}"


def table(rows: list[list[str]], headers: list[str]) -> str:
    """Schlichte, monospace-taugliche Tabelle ohne Fremdbibliothek."""
    if not rows:
        return "(keine Einträge)"
    cols = list(zip(*([headers] + rows)))
    widths = [max(len(str(cell)) for cell in col) for col in cols]
    def line(cells):
        return "  ".join(str(c).ljust(w) for c, w in zip(cells, widths)).rstrip()
    out = [line(headers), "  ".join("─" * w for w in widths)]
    out.extend(line(r) for r in rows)
    return "\n".join(out)


def out(text: str) -> None:
    print(text)


def fail(message: str) -> None:
    print(f"Fehler: {message}", file=sys.stderr)
    raise SystemExit(1)
