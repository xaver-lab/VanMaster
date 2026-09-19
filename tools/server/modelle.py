"""Pydantic-Modelle des Servers — Antworten spiegeln die Kern-Datenklassen
(``tools/kern/modelle.py``), Anfragen bilden die Schreibrouten ab.

Reine Datenhaltung für FastAPI (Validierung, OpenAPI, spätere TS-Typen aus
dem JSON-Schema). Kein Verhalten, keine Kern-Logik.
"""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class _Basis(BaseModel):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------- Antworten

class AbschnittAntwort(_Basis):
    name: str
    text: str
    zeile_von: int
    zeile_bis: int


class AufgabeAntwort(_Basis):
    id: str
    titel: str
    status: str
    bereich: str
    gruppe: str = ""
    ebene: int = 0
    eltern: str = ""
    kinder: list[str] = []
    braucht: list[str] = []
    prio: str = ""
    dauer: str = ""
    beschreibung: str = ""
    datei: str = ""
    zeile: int = 0


class BereichAntwort(_Basis):
    name: str
    kurz: str
    status: str
    phase: int | None
    datei: str
    abschnitte: dict[str, AbschnittAntwort] = {}
    aufgaben: list[AufgabeAntwort] = []


class QuerverweisAntwort(_Basis):
    ziel: str
    anzeigetext: str
    datei: str
    zeile: int
    ziel_typ: str | None = None
    ziel_id: str | None = None


class SeiteAntwort(_Basis):
    titel: str
    typ: str
    status: str
    bereich: str
    datei: str
    abschnitte: dict[str, AbschnittAntwort] = {}
    text: str = ""


class TeilAntwort(_Basis):
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
    watt: str
    stunden_pro_tag: str
    notiz: str
    gekauft_am: str
    zeile: int = 0


class EinzelteilAntwort(_Basis):
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
    notiz: str
    zeile: int = 0


class MediumAntwort(_Basis):
    name: str
    dateiname: str
    bereich: str
    art: str
    datei: str
    groesse: int = 0


class KennzahlenAntwort(_Basis):
    aufgaben_fertig: int
    aufgaben_gesamt: int
    teile: int
    kosten: float
    kosten_bestellt: float
    gewicht: float
    offene_entscheidungen: int
    bauteile: int


class KategorieAntwort(_Basis):
    name: str
    teile: int
    kosten: float
    gewicht: float
    verbaut: int


class BudgetKategorieAntwort(_Basis):
    kategorie: str
    bezahlt: float
    geplant: float
    prognose: float
    budget: float | None = None


class BudgetAntwort(_Basis):
    """``camper budget`` — Zielbudget gegen bezahlt und geplant."""

    ziel: float | None = None
    bezahlt: float
    geplant: float
    prognose: float
    rest: float | None = None
    differenz_prognose: float | None = None
    kategorien: list[BudgetKategorieAntwort] = []


class GewichtAntwort(_Basis):
    """``camper gewicht`` — Zuladungsbilanz."""

    teile_kg: float
    teile_fehlt: int
    teile_gesamt: int
    bauteile_kg: float
    bauteile_fehlt: int
    bauteile_gesamt: int
    ausbau_kg: float
    leergewicht_kg: float | None = None
    zul_gesamtgewicht_kg: float | None = None
    zuladung_erlaubt_kg: float | None = None


class MaterialGruppeAntwort(_Basis):
    """Eine Zeile von ``camper material`` — Material + Dicke mit Bedarf.
    ``zuschnitte`` sind Einzelteil-IDs; die Sätze stehen in ``einzelteile``."""

    material: str
    dicke_mm: str = ""
    bedarf: str
    zuschnitte: list[str] = []


class EinkaufGruppeAntwort(_Basis):
    """Ein Händlerbündel aus ``camper buy next``. ``teile`` sind Teile-IDs;
    die Sätze stehen in ``teile`` der Gesamtantwort."""

    haendler: str
    summe: float
    teile: list[str] = []


class EinkaufAntwort(_Basis):
    """``camper buy next`` — was als Nächstes bestellt werden kann."""

    gruppen: list[EinkaufGruppeAntwort] = []
    teile_gesamt: int
    summe: float


class AblaufAufgabeAntwort(_Basis):
    """Eine Aufgabe im Ablaufplan. ``haelt_auf`` ist die Zahl der offenen
    Aufgaben, die an ihr hängen — direkt und über die Kette."""

    id: str
    titel: str
    bereich: str
    status: str
    prio: str = ""
    dauer: str = ""
    braucht: list[str] = []
    haelt_auf: int = 0


class AblaufStufeAntwort(_Basis):
    stufe: int
    aufgaben: list[AblaufAufgabeAntwort] = []


class AblaufAntwort(_Basis):
    """``camper ablauf`` — offene Aufgaben in Stufen nach ``@braucht:``."""

    stufen: list[AblaufStufeAntwort] = []
    tiefe: int
    offen_gesamt: int
    schluessel: list[AblaufAufgabeAntwort] = []
    ring: list[AblaufAufgabeAntwort] = []


class StromVerbraucherAntwort(_Basis):
    id: str
    titel: str
    kategorie: str
    status: str
    menge: float
    watt: float
    stunden_pro_tag: float
    wh_pro_tag: float
    ah_pro_tag: float


class StromLueckeAntwort(_Basis):
    """Teil mit nur einem der beiden Werte — fehlt in der Bilanz."""

    id: str
    titel: str
    watt: str = ""
    stunden_pro_tag: str = ""


class StromAntwort(_Basis):
    """``camper strom`` — Tagesbedarf gegen die Batteriekapazität."""

    verbraucher: list[StromVerbraucherAntwort] = []
    unvollstaendig: list[StromLueckeAntwort] = []
    teile_gesamt: int
    wh_pro_tag: float
    ah_pro_tag: float
    ah_pro_tag_brutto: float
    bordspannung_v: float
    batterie_ah: float | None = None
    batterie_nutzbar: float
    nutzbar_ah: float | None = None
    wirkungsgrad: float
    reichweite_tage: float | None = None


class DatenAntwort(_Basis):
    """Form von ``GET /api/daten`` — vollständiger Bestand."""

    erzeugt: str
    bereiche: list[BereichAntwort]
    aufgaben: list[AufgabeAntwort]
    querverweise: list[QuerverweisAntwort]
    entscheidungen: list[SeiteAntwort]
    anleitungen: list[SeiteAntwort]
    recherche: list[SeiteAntwort]
    teile: list[TeilAntwort]
    einzelteile: list[EinzelteilAntwort]
    medien: list[MediumAntwort]
    versionen: dict[str, str]
    kennzahlen: KennzahlenAntwort
    kategorien: list[KategorieAntwort]
    budget: BudgetAntwort
    gewicht: GewichtAntwort
    material: list[MaterialGruppeAntwort]
    einkauf: EinkaufAntwort
    ablauf: AblaufAntwort
    strom: StromAntwort
    bearbeitbar: dict[str, Any]
    vokabular: dict[str, list[str]]


# -------------------------------------------------------------- Erfolg/Fehler

class SchreibErfolg(_Basis):
    ok: bool = True
    version: str
    datei: str
    id: str | None = None


class FehlerAntwort(_Basis):
    fehler: str


class KonfliktAntwort(_Basis):
    fehler: str
    datei: str
    version_aktuell: str
    stand: Any = None


# ------------------------------------------------------------------ Anfragen

class AufgabeAnlegenAnfrage(_Basis):
    bereich: str
    titel: str
    version: str
    status: str = "offen"
    beschreibung: str = ""
    prio: str = ""
    gruppe: str | None = None
    eltern_id: str | None = None


class AufgabePatchAnfrage(_Basis):
    version: str
    status: str | None = None
    titel: str | None = None
    beschreibung: str | None = None
    prio: str | None = None


class AbschnittAnfrage(_Basis):
    text: str
    version: str


class KopfAnfrage(_Basis):
    feld: str
    wert: Any
    version: str


class TeilAnlegenAnfrage(_Basis):
    felder: dict[str, Any]
    version: str


class TeilPatchAnfrage(_Basis):
    feld: str
    wert: str
    version: str


class EinzelteilAnlegenAnfrage(_Basis):
    felder: dict[str, Any]
    version: str


class EinzelteilPatchAnfrage(_Basis):
    feld: str
    wert: str
    version: str
