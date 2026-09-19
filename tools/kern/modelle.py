"""Typisierte Datenklassen des Kerns — reine Datenhaltung, kein Verhalten.

Jede aus Markdown oder CSV gelesene Einheit merkt sich, wo sie herkommt
(Datei + Zeile/Zeilenbereich), damit ein späterer Schreibzugriff nur die
betroffenen Zeilen anfasst statt die ganze Datei neu zu schreiben.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Aufgabe:
    """Eine Zeile ``- [ ] …`` unter ``## Aufgaben`` einer Bereichsdatei."""

    id: str
    titel: str
    status: str
    bereich: str
    gruppe: str = ""
    ebene: int = 0
    eltern: str = ""
    kinder: list[str] = field(default_factory=list)
    braucht: list[str] = field(default_factory=list)
    prio: str = ""
    dauer: str = ""
    beschreibung: str = ""
    # Fundstelle
    datei: str = ""
    zeile: int = 0                       # Zeile der Aufgabenzeile selbst
    beschreibung_von: int | None = None  # erste `> `-Zeile, falls vorhanden
    beschreibung_bis: int | None = None  # letzte `> `-Zeile
    block_bis: int = 0                   # letzte Zeile inkl. aller Unterpunkte


@dataclass
class Abschnitt:
    """Ein ``## Name``-Abschnitt eines Markdown-Dokuments."""

    name: str
    text: str
    zeile_von: int  # Zeile der Überschrift
    zeile_bis: int  # letzte Zeile des Abschnitts (vor der nächsten Überschrift)


@dataclass
class Bereich:
    """Eine Datei unter ``vault/Bereiche/*.md``."""

    name: str
    kurz: str
    status: str
    phase: int | None
    datei: str
    abschnitte: dict[str, Abschnitt] = field(default_factory=dict)
    aufgaben: list[Aufgabe] = field(default_factory=list)

    @property
    def beschreibung(self) -> str:
        a = self.abschnitte.get("Beschreibung")
        return a.text if a else ""

    @property
    def stand(self) -> str:
        a = self.abschnitte.get("Stand")
        return a.text if a else ""

    @property
    def auslegung(self) -> str:
        a = self.abschnitte.get("Auslegung")
        return a.text if a else ""

    @property
    def notizen(self) -> str:
        a = self.abschnitte.get("Notizen")
        return a.text if a else ""

    @property
    def links_text(self) -> str:
        a = self.abschnitte.get("Links")
        return a.text if a else ""


@dataclass
class Querverweis:
    """Ein handgeschriebener ``[[Ziel]]``- bzw. ``[[Ziel|Text]]``-Verweis."""

    ziel: str             # roher Name zwischen den Klammern
    anzeigetext: str      # Anzeigetext (= ziel, wenn kein "|Text")
    datei: str
    zeile: int
    ziel_typ: str | None = None  # bereich | entscheidung | anleitung | recherche | teil
    ziel_id: str | None = None   # aufgelöste Kennung/Name, None wenn nicht gefunden


@dataclass
class Seite:
    """Eine Datei unter Entscheidungen/, Anleitungen/ oder Recherche/."""

    titel: str
    typ: str  # "entscheidung" | "anleitung" | "recherche"
    status: str
    bereich: str
    datei: str
    abschnitte: dict[str, Abschnitt] = field(default_factory=dict)
    text: str = ""  # ganzer Rumpf als Rohtext (wie tools/build.py:seiten())


@dataclass
class Teil:
    """Eine Zeile aus ``data/parts.csv``."""

    id: str
    titel: str
    beschreibung: str
    kategorie: str
    menge: str
    einheit: str
    preis: str
    status: str
    prioritaet: str
    link: str
    haendler: str
    fuer_aufgabe: str
    entscheidung: str
    kennwerte: str
    gewicht_kg: str
    watt: str            # Leistungsaufnahme je Stück, für die Strombilanz
    stunden_pro_tag: str  # geschätzte Laufzeit am Tag
    notiz: str
    gekauft_am: str
    zeile: int = 0  # Zeilennummer in data/parts.csv (Kopfzeile = 1)


@dataclass
class Einzelteil:
    """Eine Zeile aus ``data/bauteile.csv``."""

    id: str
    titel: str
    bereich: str
    art: str
    material: str
    laenge_mm: str
    breite_mm: str
    dicke_mm: str
    anzahl: str
    teil_id: str
    fuer_aufgabe: str
    massquelle: str
    status: str
    gewicht_kg: str
    notiz: str
    zeile: int = 0


@dataclass
class Medium:
    """Ein Bild, Dokument oder Modell unter ``vault/Medien``/``vault/Modelle``."""

    name: str       # Dateiname ohne Endung
    dateiname: str  # Dateiname mit Endung
    bereich: str
    art: str        # "bild" | "dokument" | "modell"
    datei: str      # Pfad relativ zur Projektwurzel
    groesse: int = 0  # Dateigröße in Byte


@dataclass
class Bestand:
    """Alles zusammen — das Ergebnis von ``laden()``."""

    bereiche: list[Bereich] = field(default_factory=list)
    aufgaben: list[Aufgabe] = field(default_factory=list)
    querverweise: list[Querverweis] = field(default_factory=list)
    entscheidungen: list[Seite] = field(default_factory=list)
    anleitungen: list[Seite] = field(default_factory=list)
    recherche: list[Seite] = field(default_factory=list)
    teile: list[Teil] = field(default_factory=list)
    einzelteile: list[Einzelteil] = field(default_factory=list)
    medien: list[Medium] = field(default_factory=list)
