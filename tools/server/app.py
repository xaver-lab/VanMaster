"""FastAPI-App für den neuen Server (UMBAU.md Phase 4).

``app_erstellen()`` baut die App frisch auf — kein globaler Zustand, damit
Tests mehrere unabhängige Apps auf verschiedenen ``repo``-Kopien anlegen
können. Jede Schreibroute läuft über ``tools.kern`` (Quelle immer
``"web"`` — die Matrix wird dort durchgesetzt, FORMAT.md §8/§10) und meldet
sich danach bei den ``nach_schreiben``-Hooks (Einhängepunkt für Live-
Aktualisierung/Auto-Commit, kommen in späteren Phasen dazu).

Noch nicht enthalten: SSE, Auto-Commit, Auslieferung von ``web/dist``.
"""
from __future__ import annotations

from typing import Any, Callable

from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import JSONResponse

from .. import common
from ..kern import (
    Konflikt, Ungueltig, Unerlaubt,
    abschnitte as kern_abschnitte, aufgaben as kern_aufgaben,
    aufgaben_lesen, bereiche_lesen, datei as kern_datei,
    einzelteile_lesen, tabellen as kern_tabellen, teile_lesen,
)
from .daten import daten_json
from .modelle import (
    AbschnittAnfrage, AufgabeAnlegenAnfrage, AufgabeAntwort,
    AufgabePatchAnfrage, DatenAntwort, EinzelteilAnlegenAnfrage,
    EinzelteilAntwort, EinzelteilPatchAnfrage, KopfAnfrage, SchreibErfolg,
    TeilAnlegenAnfrage, TeilAntwort, TeilPatchAnfrage,
)

_UNBEKANNTE_ID = "Keine Zeile mit id"  # Präfix aus kern.tabellen._feld_setzen/_loeschen


def _fehler(code: int, text: str) -> JSONResponse:
    return JSONResponse(status_code=code, content={"fehler": text})


def _konflikt(exc: Konflikt, stand: Any) -> JSONResponse:
    return JSONResponse(status_code=409, content={
        "fehler": str(exc),
        "datei": kern_datei.rel(exc.pfad),
        "version_aktuell": exc.aktuell,
        "stand": stand,
    })


def _ungueltig(exc: Ungueltig) -> JSONResponse:
    # `_feld_setzen`/`_loeschen` melden eine unbekannte id ebenfalls über
    # `Ungueltig` — dafür ist die HTTP-Antwort 404, nicht 422.
    if _UNBEKANNTE_ID in str(exc):
        return _fehler(404, str(exc))
    return _fehler(422, str(exc))


def _aufgabe_stand(aufgabe_id: str) -> dict | None:
    for a in aufgaben_lesen():
        if a.id == aufgabe_id:
            return AufgabeAntwort.model_validate(a).model_dump()
    return None


def _teil_stand(teil_id: str) -> dict | None:
    for t in teile_lesen():
        if t.id == teil_id:
            return TeilAntwort.model_validate(t).model_dump()
    return None


def _einzelteil_stand(einzelteil_id: str) -> dict | None:
    for e in einzelteile_lesen():
        if e.id == einzelteil_id:
            return EinzelteilAntwort.model_validate(e).model_dump()
    return None


def _bereich_stand(name: str):
    for b in bereiche_lesen():
        if b.name == name:
            return b
    return None


def _abschnitt_stand(name: str, abschnitt: str) -> str | None:
    b = _bereich_stand(name)
    if b is None:
        return None
    a = b.abschnitte.get(abschnitt)
    return a.text if a else ""


def _kopf_stand(name: str, feld: str):
    b = _bereich_stand(name)
    if b is None:
        return None
    return {"kurz": b.kurz, "status": b.status, "phase": b.phase,
            "bereich": b.name}.get(feld)


def _bereichsdatei_rel(name: str) -> str:
    return kern_datei.rel(common.BEREICHE_DIR / f"{name}.md")


def app_erstellen() -> FastAPI:
    """Baut eine neue App. Wer Live-Aktualisierung oder Auto-Commit
    anschließen will, hängt sich in ``app.state.nach_schreiben`` ein:
    eine Liste von Funktionen ``callback(datei_relativ: str) -> None``,
    die nach jedem erfolgreichen Schreiben (auch bei löschen/anlegen)
    aufgerufen werden."""
    app = FastAPI(title="VanMaster")
    app.state.nach_schreiben: list[Callable[[str], None]] = []

    def _melde(datei_rel: str) -> None:
        for hook in app.state.nach_schreiben:
            hook(datei_rel)

    router = APIRouter(prefix="/api")

    # ---------------------------------------------------------------- Daten

    @router.get("/daten", response_model=DatenAntwort)
    def get_daten():
        return daten_json()

    # -------------------------------------------------------------- Aufgaben

    @router.post("/aufgaben")
    def aufgabe_anlegen(anfrage: AufgabeAnlegenAnfrage):
        try:
            neue_id, neuer_hash = kern_aufgaben.anlegen(
                anfrage.bereich, anfrage.titel, anfrage.version,
                status=anfrage.status, beschreibung=anfrage.beschreibung,
                prio=anfrage.prio, gruppe=anfrage.gruppe,
                eltern_id=anfrage.eltern_id,
            )
        except Konflikt as exc:
            return _konflikt(exc, None)
        except ValueError as exc:
            return _fehler(422, str(exc))
        datei_rel = _bereichsdatei_rel(anfrage.bereich)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel, id=neue_id)

    @router.patch("/aufgaben/{aufgabe_id}")
    def aufgabe_patch(aufgabe_id: str, anfrage: AufgabePatchAnfrage):
        a = next((x for x in aufgaben_lesen() if x.id == aufgabe_id), None)
        if a is None:
            return _fehler(404, f"Aufgabe '{aufgabe_id}' nicht gefunden.")
        version = anfrage.version
        try:
            if anfrage.status is not None:
                version = kern_aufgaben.status_setzen(aufgabe_id, anfrage.status, version)
            if anfrage.titel is not None:
                version = kern_aufgaben.titel_setzen(aufgabe_id, anfrage.titel, version)
            if anfrage.beschreibung is not None:
                version = kern_aufgaben.beschreibung_setzen(
                    aufgabe_id, anfrage.beschreibung, version)
            if anfrage.prio is not None:
                version = kern_aufgaben.prio_setzen(aufgabe_id, anfrage.prio, version)
        except Konflikt as exc:
            return _konflikt(exc, _aufgabe_stand(aufgabe_id))
        except ValueError as exc:
            return _fehler(422, str(exc))
        _melde(a.datei)
        return SchreibErfolg(version=version, datei=a.datei)

    @router.delete("/aufgaben/{aufgabe_id}")
    def aufgabe_loeschen(aufgabe_id: str, version: str = Query(...)):
        a = next((x for x in aufgaben_lesen() if x.id == aufgabe_id), None)
        if a is None:
            return _fehler(404, f"Aufgabe '{aufgabe_id}' nicht gefunden.")
        try:
            neuer_hash = kern_aufgaben.loeschen(aufgabe_id, version)
        except Konflikt as exc:
            return _konflikt(exc, _aufgabe_stand(aufgabe_id))
        except ValueError as exc:
            return _fehler(422, str(exc))
        _melde(a.datei)
        return SchreibErfolg(version=neuer_hash, datei=a.datei)

    # -------------------------------------------------------------- Bereiche

    @router.put("/bereiche/{name}/abschnitte/{abschnitt}")
    def abschnitt_setzen(name: str, abschnitt: str, anfrage: AbschnittAnfrage):
        if _bereich_stand(name) is None:
            return _fehler(404, f"Bereich '{name}' nicht gefunden.")
        try:
            neuer_hash = kern_abschnitte.abschnitt_setzen(
                name, abschnitt, anfrage.text, anfrage.version, quelle="web")
        except Konflikt as exc:
            return _konflikt(exc, _abschnitt_stand(name, abschnitt))
        except Unerlaubt as exc:
            return _fehler(403, str(exc))
        except ValueError as exc:
            return _fehler(422, str(exc))
        datei_rel = _bereichsdatei_rel(name)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel)

    @router.patch("/bereiche/{name}/kopf")
    def kopf_setzen(name: str, anfrage: KopfAnfrage):
        if _bereich_stand(name) is None:
            return _fehler(404, f"Bereich '{name}' nicht gefunden.")
        try:
            neuer_hash = kern_abschnitte.kopf_setzen(
                name, anfrage.feld, anfrage.wert, anfrage.version, quelle="web")
        except Konflikt as exc:
            return _konflikt(exc, _kopf_stand(name, anfrage.feld))
        except Unerlaubt as exc:
            return _fehler(403, str(exc))
        except ValueError as exc:
            return _fehler(422, str(exc))
        datei_rel = _bereichsdatei_rel(name)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel)

    # ---------------------------------------------------------------- Teile

    @router.post("/teile")
    def teil_anlegen(anfrage: TeilAnlegenAnfrage):
        try:
            neue_id, neuer_hash = kern_tabellen.teil_anlegen(
                anfrage.felder, anfrage.version, quelle="web")
        except Konflikt as exc:
            return _konflikt(exc, None)
        except Ungueltig as exc:
            return _ungueltig(exc)
        datei_rel = kern_datei.rel(common.PARTS_CSV)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel, id=neue_id)

    @router.patch("/teile/{teil_id}")
    def teil_patch(teil_id: str, anfrage: TeilPatchAnfrage):
        if _teil_stand(teil_id) is None:
            return _fehler(404, f"Kein Teil mit der Kennung '{teil_id}'.")
        try:
            neuer_hash = kern_tabellen.teil_feld_setzen(
                teil_id, anfrage.feld, anfrage.wert, anfrage.version, quelle="web")
        except Konflikt as exc:
            return _konflikt(exc, _teil_stand(teil_id))
        except Ungueltig as exc:
            return _ungueltig(exc)
        datei_rel = kern_datei.rel(common.PARTS_CSV)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel)

    @router.delete("/teile/{teil_id}")
    def teil_loeschen(teil_id: str, version: str = Query(...)):
        if _teil_stand(teil_id) is None:
            return _fehler(404, f"Kein Teil mit der Kennung '{teil_id}'.")
        try:
            neuer_hash = kern_tabellen.teil_loeschen(teil_id, version)
        except Konflikt as exc:
            return _konflikt(exc, _teil_stand(teil_id))
        except Ungueltig as exc:
            return _ungueltig(exc)
        datei_rel = kern_datei.rel(common.PARTS_CSV)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel)

    # ----------------------------------------------------------- Einzelteile

    @router.post("/einzelteile")
    def einzelteil_anlegen(anfrage: EinzelteilAnlegenAnfrage):
        try:
            neue_id, neuer_hash = kern_tabellen.einzelteil_anlegen(
                anfrage.felder, anfrage.version, quelle="web")
        except Konflikt as exc:
            return _konflikt(exc, None)
        except Ungueltig as exc:
            return _ungueltig(exc)
        datei_rel = kern_datei.rel(common.BAUTEILE_CSV)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel, id=neue_id)

    @router.patch("/einzelteile/{einzelteil_id}")
    def einzelteil_patch(einzelteil_id: str, anfrage: EinzelteilPatchAnfrage):
        if _einzelteil_stand(einzelteil_id) is None:
            return _fehler(404, f"Kein Einzelteil mit der Kennung '{einzelteil_id}'.")
        try:
            neuer_hash = kern_tabellen.einzelteil_feld_setzen(
                einzelteil_id, anfrage.feld, anfrage.wert, anfrage.version,
                quelle="web")
        except Konflikt as exc:
            return _konflikt(exc, _einzelteil_stand(einzelteil_id))
        except Ungueltig as exc:
            return _ungueltig(exc)
        datei_rel = kern_datei.rel(common.BAUTEILE_CSV)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel)

    @router.delete("/einzelteile/{einzelteil_id}")
    def einzelteil_loeschen(einzelteil_id: str, version: str = Query(...)):
        if _einzelteil_stand(einzelteil_id) is None:
            return _fehler(404, f"Kein Einzelteil mit der Kennung '{einzelteil_id}'.")
        try:
            neuer_hash = kern_tabellen.einzelteil_loeschen(einzelteil_id, version)
        except Konflikt as exc:
            return _konflikt(exc, _einzelteil_stand(einzelteil_id))
        except Ungueltig as exc:
            return _ungueltig(exc)
        datei_rel = kern_datei.rel(common.BAUTEILE_CSV)
        _melde(datei_rel)
        return SchreibErfolg(version=neuer_hash, datei=datei_rel)

    app.include_router(router)
    return app
