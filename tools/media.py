"""Bilder, Dokumente und 3D-Modelle aus _input einsortieren und verlinken."""
from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

from .common import DOCS, INPUT, MEDIEN_DIR, MODELLE_DIR, slug, write_text

BILDER = (".jpg", ".jpeg", ".png", ".webp")
DOKUMENTE = (".pdf", ".docx", ".doc", ".odt", ".xlsx")
# 3D-Zeichnungen. .glb/.gltf lassen sich im Browser zeigen, der Rest ist
# vorerst nur Download — der Viewer kommt, wenn die erste Datei da ist.
MODELLE = (".glb", ".gltf", ".stl", ".step", ".stp", ".3mf", ".f3d", ".skp", ".dxf")
MODELLE_WEB = (".glb", ".gltf", ".stl")
MAX_KANTE = 1600
# Das Dashboard liegt auf dem Handy — die Web-Kopie darf kleiner sein.
WEB_KANTE = 1000
WEB_DIR = DOCS / "medien"


def wurzel(endung: str) -> Path:
    """Modelle liegen getrennt von Bildern — sie werden anders benutzt."""
    return MODELLE_DIR if endung.lower() in MODELLE else MEDIEN_DIR


def zielname(quelle: Path, bereich: str) -> Path:
    stamm = slug(quelle.stem) or "bild"
    ordner = wurzel(quelle.suffix) / (bereich or "Unsortiert")
    ziel = ordner / f"{date.today():%Y-%m-%d}-{stamm}{quelle.suffix.lower()}"
    i = 2
    while ziel.exists():
        ziel = ordner / f"{date.today():%Y-%m-%d}-{stamm}-{i}{quelle.suffix.lower()}"
        i += 1
    return ziel


def verkleinern(quelle: Path, ziel: Path, kante: int = MAX_KANTE) -> str:
    """Lange Kante auf `kante` — am Handy zählt jedes Megabyte."""
    try:
        from PIL import Image
    except ImportError:
        ziel.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(quelle, ziel)
        return "kopiert (Pillow fehlt)"
    with Image.open(quelle) as bild:
        bild = bild.convert("RGB") if bild.mode in ("P", "RGBA") and \
            ziel.suffix.lower() in (".jpg", ".jpeg") else bild
        if max(bild.size) > kante:
            bild.thumbnail((kante, kante))
            hinweis = f"verkleinert auf {bild.size[0]}x{bild.size[1]}"
        else:
            hinweis = f"{bild.size[0]}x{bild.size[1]}"
        ziel.parent.mkdir(parents=True, exist_ok=True)
        bild.save(ziel, quality=85, optimize=True)
    return hinweis


def uebernehmen(quelle: Path, ziel: Path) -> str:
    """Bild verkleinern, alles andere unverändert kopieren."""
    if quelle.suffix.lower() in BILDER:
        return verkleinern(quelle, ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(quelle, ziel)
    return f"{ziel.stat().st_size // 1024} kB"


def ablage() -> list[tuple[Path, str, str]]:
    """Alles im Medienordner als (Datei, Bereich, Art)."""
    if not MEDIEN_DIR.exists():
        return []
    out = []
    for datei in sorted(MEDIEN_DIR.rglob("*")):
        endung = datei.suffix.lower()
        art = "bild" if endung in BILDER else \
            "dokument" if endung in DOKUMENTE else ""
        if not art:
            continue
        rel = datei.relative_to(MEDIEN_DIR)
        out.append((datei, rel.parts[0] if len(rel.parts) > 1 else "Unsortiert",
                    art))
    return out


def index() -> int:
    """Übersichtsseite mit Einbettungen, nach Bereich gruppiert."""
    nach_bereich: dict[str, list[tuple[Path, str]]] = {}
    for datei, bereich, art in ablage():
        nach_bereich.setdefault(bereich, []).append((datei, art))
    zeilen = ["---", "typ: medien", "erzeugt: true", "---", "", "# Medien", "",
              "> Erzeugt von `camper media` — nicht von Hand ändern.", ""]
    anzahl = 0
    for bereich, eintraege in sorted(nach_bereich.items()):
        zeilen += [f"## {bereich}", ""]
        for datei, art in eintraege:
            rel = datei.relative_to(MEDIEN_DIR.parent).as_posix()
            zeilen.append(f"![[{rel}]]" if art == "bild"
                          else f"- [[{rel}|{datei.name}]]")
            anzahl += 1
        zeilen.append("")
    write_text(MEDIEN_DIR / "Medien.md", "\n".join(zeilen))
    return anzahl


def index_text() -> str:
    return f"{index()} Dateien in vault/Medien/Medien.md verlinkt"


def web_export() -> dict:
    """Kopien neben dem Dashboard — ausgeliefert wird nur `docs/`.

    Bilder werden dabei ein zweites Mal verkleinert, Dokumente bleiben wie sie
    sind. Was im Vault verschwunden ist, fliegt hier mit raus.
    """
    bilder, dokumente, modelle, behalten = [], [], [], set()
    for datei, bereich, art in ablage():
        basis = MODELLE_DIR if art == "modell" else MEDIEN_DIR
        rel = datei.relative_to(basis)
        # Umlaute im Ordnernamen nur im Vault — die Web-Kopie bleibt ASCII.
        rel = Path(*[slug(teil) for teil in rel.parts[:-1]], rel.name)
        if art == "modell":
            rel = Path("modelle", rel)
        ziel = WEB_DIR / rel
        behalten.add(ziel)
        if not ziel.exists() or ziel.stat().st_mtime < datei.stat().st_mtime:
            if art == "bild":
                verkleinern(datei, ziel, WEB_KANTE)
            else:
                ziel.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(datei, ziel)
        eintrag = {"name": datei.stem, "bereich": bereich,
                   "datei": datei.name,
                   "pfad": "medien/" + rel.as_posix()}
        if art == "modell":
            eintrag["zeigbar"] = datei.suffix.lower() in MODELLE_WEB
            modelle.append(eintrag)
        else:
            (bilder if art == "bild" else dokumente).append(eintrag)

    if WEB_DIR.exists():
        for alt in sorted(WEB_DIR.rglob("*"), reverse=True):
            if alt.is_file() and alt not in behalten:
                alt.unlink()
            elif alt.is_dir() and not any(alt.iterdir()):
                alt.rmdir()
    return {"bilder": bilder, "dokumente": dokumente, "modelle": modelle}


def einsortieren(bereich: str = "", apply: bool = True,
                 ordner: str = "") -> str:
    """`ordner` grenzt auf einen Unterordner von _input/ ein — beim
    Einarbeiten wird Stück für Stück übernommen, nicht alles auf einmal."""
    quelle_wurzel = INPUT / ordner if ordner else INPUT
    quellen = [p for p in sorted(quelle_wurzel.rglob("*"))
               if p.suffix.lower() in BILDER + DOKUMENTE + MODELLE]         if quelle_wurzel.exists() else []
    if not quellen:
        return (f"Nichts in {quelle_wurzel.name}/. "
                f"Im Vault verlinkt: {index()}.")
    zeilen = []
    for quelle in quellen:
        ziel = zielname(quelle, bereich)
        if not apply:
            zeilen.append(f"  {quelle.name} → {ziel.relative_to(MEDIEN_DIR.parent.parent)}")
            continue
        hinweis = uebernehmen(quelle, ziel)
        quelle.unlink()
        zeilen.append(f"  {quelle.name} → "
                      f"{ziel.relative_to(MEDIEN_DIR.parent.parent)} ({hinweis})")
    kopf = (f"{len(quellen)} Dateien"
            + ("" if apply else " würden einsortiert (Probelauf)"))
    schluss = f"\nIm Vault verlinkt: {index()}." if apply else ""
    return f"{kopf}\n" + "\n".join(zeilen) + schluss
