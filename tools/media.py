"""Bilder aus _input einsortieren, verkleinern, im Vault verlinken."""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from .common import INPUT, MEDIEN_DIR, slug, write_text

BILDER = (".jpg", ".jpeg", ".png", ".webp")
MAX_KANTE = 1600


def zielname(quelle: Path, bereich: str) -> Path:
    stamm = slug(quelle.stem) or "bild"
    ordner = MEDIEN_DIR / (bereich or "Unsortiert")
    ziel = ordner / f"{date.today():%Y-%m-%d}-{stamm}{quelle.suffix.lower()}"
    i = 2
    while ziel.exists():
        ziel = ordner / f"{date.today():%Y-%m-%d}-{stamm}-{i}{quelle.suffix.lower()}"
        i += 1
    return ziel


def verkleinern(quelle: Path, ziel: Path) -> str:
    """Lange Kante auf MAX_KANTE — am Handy zählt jedes Megabyte."""
    try:
        from PIL import Image
    except ImportError:
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(quelle, ziel)
        return "kopiert (Pillow fehlt)"
    with Image.open(quelle) as bild:
        bild = bild.convert("RGB") if bild.mode in ("P", "RGBA") and \
            ziel.suffix.lower() in (".jpg", ".jpeg") else bild
        if max(bild.size) > MAX_KANTE:
            bild.thumbnail((MAX_KANTE, MAX_KANTE))
            hinweis = f"verkleinert auf {bild.size[0]}x{bild.size[1]}"
        else:
            hinweis = f"{bild.size[0]}x{bild.size[1]}"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        bild.save(ziel, quality=85, optimize=True)
    return hinweis


def index() -> int:
    """Übersichtsseite mit Einbettungen, nach Bereich gruppiert."""
    if not MEDIEN_DIR.exists():
        return 0
    nach_bereich: dict[str, list[Path]] = {}
    for datei in sorted(MEDIEN_DIR.rglob("*")):
        if datei.suffix.lower() not in BILDER:
            continue
        rel = datei.relative_to(MEDIEN_DIR)
        bereich = rel.parts[0] if len(rel.parts) > 1 else "Unsortiert"
        nach_bereich.setdefault(bereich, []).append(datei)
    zeilen = ["---", "typ: medien", "erzeugt: true", "---", "", "# Medien", "",
              "> Erzeugt von `camper media` — nicht von Hand ändern.", ""]
    anzahl = 0
    for bereich, dateien in sorted(nach_bereich.items()):
        zeilen += [f"## {bereich}", ""]
        for datei in dateien:
            rel = datei.relative_to(MEDIEN_DIR.parent).as_posix()
            zeilen.append(f"![[{rel}]]")
            anzahl += 1
        zeilen.append("")
    write_text(MEDIEN_DIR / "Medien.md", "\n".join(zeilen))
    return anzahl


def index_text() -> str:
    return f"{index()} Bilder in vault/Medien/Medien.md verlinkt"


def einsortieren(bereich: str = "", apply: bool = True) -> str:
    quellen = [p for p in sorted(INPUT.rglob("*"))
               if p.suffix.lower() in BILDER] if INPUT.exists() else []
    if not quellen:
        return f"Keine Bilder in _input/. Im Vault verlinkt: {index()}."
    zeilen = []
    for quelle in quellen:
        ziel = zielname(quelle, bereich)
        if not apply:
            zeilen.append(f"  {quelle.name} → {ziel.relative_to(MEDIEN_DIR.parent)}")
            continue
        hinweis = verkleinern(quelle, ziel)
        quelle.unlink()
        zeilen.append(f"  {quelle.name} → "
                      f"{ziel.relative_to(MEDIEN_DIR.parent)} ({hinweis})")
    kopf = (f"{len(quellen)} Bilder"
            + ("" if apply else " würden einsortiert (Probelauf)"))
    schluss = f"\nIm Vault verlinkt: {index()}." if apply else ""
    return f"{kopf}\n" + "\n".join(zeilen) + schluss
