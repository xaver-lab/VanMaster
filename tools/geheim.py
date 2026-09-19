"""Geheimnis-Wache — hält sensible Daten aus dem Repo.

Das Repo und die daraus gebaute Website sind kein privater Ort. Dieses Modul
durchsucht Dateien nach Mustern, die dort nicht hingehören: Zugangsdaten,
Bankverbindungen, Fahrzeug- und Personendaten.

Zwei Schweregrade, wie in ``tools/kern/pruefen.py``:

* ``fehler``   — blockiert den Commit (``.githooks/pre-commit``).
* ``warnung``  — wird gemeldet, blockiert nicht.

Einzelne Zeilen lassen sich freigeben, indem ``geheim-ok`` in der Zeile steht
(als Kommentar). Das ist für Testdaten und für die Muster in dieser Datei
gedacht, nicht für echte Geheimnisse.

Befehl: ``python camper.py geheim`` (alle versionierten Dateien) bzw.
``python camper.py geheim --staged`` (nur was zum Commit vorgemerkt ist).
"""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import common

FREIGABE = "geheim-ok"

#: Dateien, die nie durchsucht werden: erzeugt, gesperrt oder Binärkram.
UEBERSPRINGEN = (
    "web/dist/", "data/generated/", "web/node_modules/",
    "web/package-lock.json", "web/src/lib/api-schema.json",
)
BINAER_ENDUNGEN = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".heic", ".pdf", ".xlsx",
    ".woff", ".woff2", ".ttf", ".otf", ".zip", ".stl", ".step", ".f3d",
    ".mp4", ".mov", ".ico",
}
MAX_BYTES = 1_000_000


@dataclass
class Fund:
    datei: str
    zeile: int
    art: str        # "fehler" | "warnung"
    muster: str
    meldung: str
    auszug: str     # maskiert, nie der volle Treffer


def _m(text: str) -> str:
    """Maskiert einen Treffer: die ersten drei Zeichen, dann Punkte."""
    text = text.strip()
    return (text[:3] + "…" + str(len(text)) + " Zeichen") if len(text) > 4 else "…"


# --------------------------------------------------------------- Muster
# (name, regex, art, meldung). Zeilen mit geheim-ok werden übersprungen,
# deshalb steht in dieser Liste nie ein echtes Geheimnis.

MUSTER: list[tuple[str, re.Pattern, str, str]] = [
    ("Privater Schlüssel",
     re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----"),
     "fehler", "privater Schlüssel gehört nie ins Repo"),

    ("GitHub-Token",
     re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b"),
     "fehler", "GitHub-Token — sofort auf github.com zurückziehen"),

    ("AWS-Schlüssel",
     re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
     "fehler", "AWS-Zugangsschlüssel"),

    ("Cloudflare-Token",
     re.compile(r"\b[A-Za-z0-9_-]{40}\b(?=.*(?i:cloudflare|CF_API))"),
     "fehler", "sieht nach Cloudflare-API-Token aus — gehört in GitHub-Secrets"),

    ("Zugangsdaten-Zuweisung",
     re.compile(r"(?i)\b(api[_-]?key|apikey|auth[_-]?token|access[_-]?token"
                r"|client[_-]?secret|passwort|password|passwd)\b"
                r"\s*[:=]\s*[\"']?(?![\"']?\s*$)"
                # Platzhalter und Code-Verweise sind keine Geheimnisse:
                # os.environ[...], process.env.X, ${VAR}, <hier eintragen>
                r"(?!(?i:none|null|true|false|xxx+|\.\.\.|os\.environ"
                r"|process\.env|import\.meta|getenv|env\.|config\.|settings\.))"
                r"(?![^\s\"',]*[\[\](){}$<>])"
                r"[^\s\"',]{8,}"),
     "fehler", "Zugangsdaten im Klartext — in Umgebungsvariable oder GitHub-Secret"),

    ("IBAN",
     re.compile(r"\b[A-Z]{2}\d{2}(?:[ ]?[A-Z0-9]{4}){3,7}[ ]?[A-Z0-9]{1,4}\b"),
     "fehler", "Bankverbindung"),

    ("Fahrgestellnummer",
     re.compile(r"(?i:\b(?:VIN|FIN|Fahrgestellnummer|Fahrzeug[- ]?Ident[a-zä]*)\b)"
                r"[^\n]{0,20}?\b([A-HJ-NPR-Z0-9]{17})\b"),
     "fehler", "Fahrgestellnummer identifiziert das Fahrzeug eindeutig"),

    ("Kennzeichen",
     re.compile(r"(?i:\b(?:Kennzeichen|Nummernschild|amtliches Kennzeichen)\b)"
                r"[^\n]{0,20}?\b([A-ZÄÖÜ]{1,3}[- ][A-ZÄÖÜ]{1,2}[- ]?\d{1,4}[EH]?)\b"),
     "warnung", "amtliches Kennzeichen"),

    ("Versicherungsnummer",
     re.compile(r"(?i:\b(?:Versicherungs(?:schein)?nummer|Policennummer"
                r"|Sozialversicherungsnummer)\b)[^\n]{0,20}?\b([A-Z0-9]{6,})\b"),
     "warnung", "Versicherungsdaten"),

    ("Anschrift",
     re.compile(r"(?i)\b(?:Anschrift|Wohnadresse|Meldeadresse|Heimatadresse)\b\s*[:=]"),
     "warnung", "Postanschrift — lieber nur den Ort nennen"),

    ("Telefonnummer",
     re.compile(r"(?i)\b(?:Telefon|Telefonnummer|Handy|Mobil|Mobilnummer)\b"
                r"\s*[:=]?\s*(\+?[\d][\d /-]{8,})"),
     "warnung", "Telefonnummer"),

    ("Standortkoordinaten",
     re.compile(r"(?i)\b(?:Standort|Koordinaten|Stellplatz|GPS)\b[^\n]{0,20}?"
                r"\b(\d{1,2}[.,]\d{4,}\s*,\s*\d{1,3}[.,]\d{4,})"),
     "warnung", "genaue Koordinaten eines Stellplatzes"),
]


# ------------------------------------------------------------ Prüfungen

def text_pruefen(text: str, datei: str) -> list[Fund]:
    """Durchsucht einen Text. ``datei`` ist nur die Beschriftung."""
    funde: list[Fund] = []
    for nr, zeile in enumerate(text.splitlines(), start=1):
        if FREIGABE in zeile:
            continue
        for name, regex, art, meldung in MUSTER:
            treffer = regex.search(zeile)
            if not treffer:
                continue
            roh = treffer.group(treffer.lastindex or 0)
            funde.append(Fund(datei, nr, art, name, meldung, _m(roh)))
    return funde


def _ueberspringen(rel: str) -> bool:
    if any(rel.startswith(p) for p in UEBERSPRINGEN):
        return True
    return Path(rel).suffix.lower() in BINAER_ENDUNGEN


def _git(repo: Path, *args: str) -> str | None:
    try:
        fertig = subprocess.run(["git", *args], cwd=repo, check=True,
                                capture_output=True)
    except (subprocess.CalledProcessError, OSError):
        return None
    return fertig.stdout.decode("utf-8", "replace")


def versioniert_pruefen(repo: Path | None = None) -> list[Fund]:
    """Alle von git verwalteten Dateien im Arbeitsbaum."""
    repo = repo or common.ROOT
    liste = _git(repo, "ls-files", "-z")
    if liste is None:
        return []
    funde: list[Fund] = []
    for rel in filter(None, liste.split("\0")):
        if _ueberspringen(rel):
            continue
        pfad = repo / rel
        try:
            if pfad.stat().st_size > MAX_BYTES:
                continue
            text = pfad.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        funde.extend(text_pruefen(text, rel))
    return funde


def staged_pruefen(repo: Path | None = None) -> list[Fund]:
    """Nur der zum Commit vorgemerkte Inhalt — genau das, was der
    pre-commit-Hook sehen muss. Liest die Blobs aus dem Index, nicht die
    Dateien im Arbeitsbaum."""
    repo = repo or common.ROOT
    liste = _git(repo, "diff", "--cached", "--name-only", "-z",
                 "--diff-filter=ACMR")
    if liste is None:
        return []
    funde: list[Fund] = []
    for rel in filter(None, liste.split("\0")):
        if _ueberspringen(rel):
            continue
        inhalt = _git(repo, "show", f":{rel}")
        if inhalt is None:
            continue
        funde.extend(text_pruefen(inhalt, rel))
    return funde


# -------------------------------------------------------------- Ausgabe

def bericht(funde: list[Fund], umfang: str = "versionierte Dateien") -> str:
    if not funde:
        return f"Geheimnis-Wache: nichts gefunden ({umfang})."
    fehler = [f for f in funde if f.art == "fehler"]
    zeilen = [f"Geheimnis-Wache: {len(fehler)} Fehler, "
              f"{len(funde) - len(fehler)} Warnungen ({umfang})", ""]
    for f in sorted(funde, key=lambda f: (f.art != "fehler", f.datei, f.zeile)):
        zeichen = "FEHLER " if f.art == "fehler" else "Warnung"
        zeilen.append(f"  {zeichen}  {f.datei}:{f.zeile}  {f.muster} — "
                      f"{f.meldung}  [{f.auszug}]")
    zeilen += ["",
               "Echte Treffer entfernen und, wenn schon gepusht, das Geheimnis",
               f"zurückziehen. Falscher Alarm: '{FREIGABE}' in die Zeile schreiben."]
    return "\n".join(zeilen)
