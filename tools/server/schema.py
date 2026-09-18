"""JSON-Schema aus den Pydantic-Modellen (``tools/server/modelle.py``) →
TypeScript-Typen für ``web/`` (UMBAU.md Phase 4).

Aufruf: ``python -m tools.server.schema``. Schreibt
``web/src/lib/api-typen.ts`` (TypeScript, von Hand gepflegt vermieden) und
``web/src/lib/api-schema.json`` (das zugrundeliegende JSON-Schema, zur
Kontrolle). Kein npm-Paket nötig — der kleine Umsetzer JSON-Schema → TS
unten deckt ab, was ``modelle.py`` tatsächlich braucht: object/properties/
required, array, enum/Literal, Union/anyOf, nullable, $ref/$defs, dict →
Record. Kein allgemeiner json-schema-to-typescript-Ersatz.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel
from pydantic.json_schema import models_json_schema

from . import modelle

KOPF = (
    "// erzeugt — nicht von Hand ändern, neu mit `python -m tools.server.schema`\n"
    "// Quelle: tools/server/modelle.py (JSON-Schema der Pydantic-Modelle)\n"
)

_TS_PRIMITIV = {
    "string": "string",
    "integer": "number",
    "number": "number",
    "boolean": "boolean",
    "null": "null",
}


def _modelle() -> list[type[BaseModel]]:
    """Alle Pydantic-Modelle aus ``modelle.py`` außer der Basisklasse —
    Reihenfolge wie im Modul definiert, damit die Ausgabe deterministisch
    bleibt."""
    gefunden: list[type[BaseModel]] = []
    for name in vars(modelle):
        objekt = getattr(modelle, name)
        if (isinstance(objekt, type) and issubclass(objekt, BaseModel)
                and objekt not in (BaseModel, modelle._Basis)
                and objekt.__module__ == modelle.__name__):
            gefunden.append(objekt)
    gefunden.sort(key=lambda m: m.__name__)
    return gefunden


def sammeln() -> dict[str, Any]:
    """JSON-Schema aller Modelle in ``modelle.py``, ein gemeinsames
    ``$defs`` (Name → Schema)."""
    paare = [(m, "validation") for m in _modelle()]
    _, oben = models_json_schema(paare, ref_template="#/$defs/{model}")
    return oben.get("$defs", {})


# ------------------------------------------------------------- JSON→TS


def _ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def _feld_name(name: str) -> str:
    """Gültiger TS-Bezeichner, sonst als String-Literal in Anführungszeichen."""
    if name.isidentifier():
        return name
    return json.dumps(name)


def _literal(wert: Any) -> str:
    if wert is None:
        return "null"
    if isinstance(wert, bool):
        return "true" if wert else "false"
    if isinstance(wert, str):
        return json.dumps(wert)
    return json.dumps(wert)


def _typ(schema: Any) -> str:
    """Ein JSON-Schema-Knoten → TypeScript-Typausdruck."""
    if schema is True or schema == {}:
        return "any"
    if schema is False:
        return "never"
    if not isinstance(schema, dict):
        return "any"

    if "$ref" in schema:
        return _ref_name(schema["$ref"])

    if "allOf" in schema:
        teile = [t for t in schema["allOf"]]
        if len(teile) == 1:
            return _typ(teile[0])
        return " & ".join(f"({_typ(t)})" for t in teile)

    if "anyOf" in schema or "oneOf" in schema:
        varianten = schema.get("anyOf", schema.get("oneOf", []))
        return " | ".join(_typ(v) for v in varianten)

    if "const" in schema:
        return _literal(schema["const"])

    if "enum" in schema:
        return " | ".join(_literal(w) for w in schema["enum"])

    typ = schema.get("type")
    if isinstance(typ, list):
        return " | ".join(_typ({**schema, "type": t}) for t in typ)

    if typ == "array":
        elemente = schema.get("items")
        if elemente is None:
            return "any[]"
        inner = _typ(elemente)
        return f"({inner})[]" if " " in inner and "|" in inner else f"{inner}[]"

    if typ == "object":
        eigenschaften = schema.get("properties")
        if eigenschaften:
            pflicht = set(schema.get("required", []))
            zeilen = []
            for name, teilschema in eigenschaften.items():
                optional = "" if name in pflicht else "?"
                zeilen.append(
                    f"  {_feld_name(name)}{optional}: {_typ(teilschema)};")
            objekt_typ = "{\n" + "\n".join(zeilen) + "\n}"
            zusatz = schema.get("additionalProperties")
            if zusatz not in (None, False):
                objekt_typ += f" & Record<string, {_typ(zusatz)}>"
            return objekt_typ
        zusatz = schema.get("additionalProperties")
        if zusatz is None or zusatz is True:
            return "Record<string, any>"
        if zusatz is False:
            return "Record<string, never>"
        return f"Record<string, {_typ(zusatz)}>"

    if typ in _TS_PRIMITIV:
        return _TS_PRIMITIV[typ]

    return "any"


def erzeugen() -> str:
    """Die vollständige ``api-typen.ts``-Datei als Text."""
    defs = sammeln()
    teile = [KOPF]
    for name in sorted(defs):
        schema = defs[name]
        typ = _typ(schema)
        if typ.startswith("{"):
            teile.append(f"export interface {name} {typ}\n")
        else:
            teile.append(f"export type {name} = {typ};\n")
    return "\n".join(teile)


def schreiben(ziel_ordner: Path, mit_json: bool = True) -> tuple[Path, Path | None]:
    ziel_ordner.mkdir(parents=True, exist_ok=True)
    ts_pfad = ziel_ordner / "api-typen.ts"
    ts_pfad.write_text(erzeugen(), encoding="utf-8", newline="\n")
    json_pfad = None
    if mit_json:
        json_pfad = ziel_ordner / "api-schema.json"
        json_pfad.write_text(
            json.dumps(sammeln(), indent=2, ensure_ascii=False, sort_keys=True) + "\n",
            encoding="utf-8", newline="\n")
    return ts_pfad, json_pfad


def main() -> None:
    from .. import common
    ziel = common.ROOT / "web" / "src" / "lib"
    ts_pfad, json_pfad = schreiben(ziel)
    print(f"geschrieben: {ts_pfad}")
    if json_pfad:
        print(f"geschrieben: {json_pfad}")


if __name__ == "__main__":
    main()
