"""Ablaufplan: die `@braucht:`-Bezüge zwischen Aufgaben als Stufen statt als
Hinweistext.

`camper next` sagt, was gerade möglich ist, und hängt eine flache Liste
„wartet noch" an. Das beantwortet nicht die Frage, die beim Planen zählt:
*in welcher Reihenfolge* geht es, und was hält am meisten auf.

Hier wird derselbe Bestand in Stufen gelegt. Stufe 1 ist alles, was sofort
angefangen werden kann. Stufe 2 alles, dessen Blocker vollständig in Stufe 1
stehen, und so weiter. Die Stufennummer ist damit die früheste Runde, in der
eine Aufgabe drankommen kann — nicht ein Termin, sondern eine Reihenfolge.

Zwei Dinge fallen dabei nebenbei ab und stehen sonst nirgends:

- **Schlüsselaufgaben**: wie viele andere Aufgaben eine Aufgabe aufhält,
  direkt und über die ganze Kette. Das ist die Rangliste, nach der sich
  Aufwand lohnt.
- **Ringe**: `a @braucht:b` und `b @braucht:a`. Die lösen sich nie von
  selbst auf und bleiben ohne diese Auswertung unbemerkt.

Nur lesend — rührt keine Datei an.
"""
from __future__ import annotations

from . import bereiche, tasks
from .common import STANDARD_SORTIERUNG, table
from .kern.format import ERLEDIGT, PRIOS


def _offene(aufgaben: list[dict]) -> list[dict]:
    """Blätter, die noch anstehen. Sammelaufgaben zählen nicht mit: sie sind
    nur die Summe ihrer Unterpunkte (so misst auch ``tasks.fortschritt``)."""
    return [a for a in tasks.blaetter(aufgaben) if a["status"] not in ERLEDIGT]


def _offene_blocker(a: dict, nach_id: dict[str, dict]) -> set[str]:
    """IDs der Blocker, die noch nicht erledigt sind. Ein `@braucht:` auf eine
    unbekannte Kennung wird still übergangen — `camper check` meldet solche
    Verweise, der Ablaufplan soll daran nicht scheitern."""
    return {b for b in a["braucht"]
            if b in nach_id and nach_id[b]["status"] not in ERLEDIGT}


def _wartende(offen: list[dict], nach_id: dict[str, dict]) -> dict[str, set[str]]:
    return {a["id"]: _offene_blocker(a, nach_id) for a in offen}


def _stufen_legen(wartet: dict[str, set[str]]) -> tuple[list[list[str]], list[str]]:
    """Topologisch in Stufen legen. Zurück kommen die Stufen und, falls der
    Graph nicht aufgeht, die Kennungen im Ring."""
    rest = {k: set(v) for k, v in wartet.items()}
    stufen: list[list[str]] = []
    while rest:
        # Frei ist, wessen Blocker alle schon in einer früheren Stufe liegen
        # (oder gar nicht mehr offen sind).
        frei = sorted(k for k, blocker in rest.items() if not (blocker & rest.keys()))
        if not frei:
            break  # nur noch Ringe übrig
        stufen.append(frei)
        for k in frei:
            del rest[k]
    return stufen, sorted(rest)


def _haelt_auf(wartet: dict[str, set[str]]) -> dict[str, int]:
    """Wie viele offene Aufgaben je Kennung insgesamt aufgehalten werden —
    direkt und über die Kette. Der Ring bricht über die besuchten Knoten ab."""
    direkt: dict[str, set[str]] = {k: set() for k in wartet}
    for k, blocker in wartet.items():
        for b in blocker:
            direkt.setdefault(b, set()).add(k)

    ergebnis: dict[str, int] = {}
    for k in wartet:
        gesehen: set[str] = set()
        rand = list(direkt.get(k, ()))
        while rand:
            n = rand.pop()
            if n in gesehen:
                continue
            gesehen.add(n)
            rand.extend(direkt.get(n, ()))
        ergebnis[k] = len(gesehen)
    return ergebnis


def plan(bereich: str = "", sortierung: str = STANDARD_SORTIERUNG) -> dict:
    """Stufen, Schlüsselaufgaben und Ringe. ``bereich`` filtert nur, was
    angezeigt wird — gerechnet wird immer über alle Aufgaben, sonst fehlen
    Blocker aus anderen Bereichen."""
    aufgaben = tasks.load()
    nach_id = {a["id"]: a for a in aufgaben}
    offen = _offene(aufgaben)
    wartet = _wartende(offen, nach_id)
    roh_stufen, ring = _stufen_legen(wartet)
    haelt_auf = _haelt_auf(wartet)

    ordnung = bereiche.reihenfolge(sortierung)

    def platz(a: dict) -> tuple:
        return (PRIOS.get(a["prio"], 2),
                a["status"] != "laeuft",
                ordnung.index(a["bereich"]) if a["bereich"] in ordnung else len(ordnung),
                a["titel"])

    def passt(a: dict) -> bool:
        return not bereich or a["bereich"].lower() == bereich.lower()

    def satz(a: dict) -> dict:
        return {
            "id": a["id"], "titel": a["titel"], "bereich": a["bereich"],
            "status": a["status"], "prio": a["prio"], "dauer": a["dauer"],
            "braucht": sorted(wartet[a["id"]]),
            "haelt_auf": haelt_auf.get(a["id"], 0),
        }

    stufen = []
    for nr, kennungen in enumerate(roh_stufen, start=1):
        eintraege = sorted((nach_id[k] for k in kennungen), key=platz)
        sichtbar = [satz(a) for a in eintraege if passt(a)]
        if sichtbar:
            stufen.append({"stufe": nr, "aufgaben": sichtbar})

    schluessel = sorted(
        (satz(nach_id[k]) for k in wartet if haelt_auf.get(k, 0) > 0 and passt(nach_id[k])),
        key=lambda s: (-s["haelt_auf"], s["titel"]),
    )

    return {
        "stufen": stufen,
        "tiefe": len(roh_stufen),
        "offen_gesamt": len([a for a in offen if passt(a)]),
        "schluessel": schluessel,
        "ring": [satz(nach_id[k]) for k in ring if passt(nach_id[k])],
    }


def text(bereich: str = "", sortierung: str = STANDARD_SORTIERUNG) -> str:
    d = plan(bereich, sortierung)
    if not d["offen_gesamt"]:
        return ("Nichts offen" + (f" in {bereich}" if bereich else "")
                + " — der Ablaufplan ist leer.")

    kopf = "Ablaufplan" + (f" — {bereich}" if bereich else "")
    bloecke = [f"{kopf}\n{d['offen_gesamt']} offene Aufgaben in {d['tiefe']} Stufen"]

    for stufe in d["stufen"]:
        zeilen = []
        for a in stufe["aufgaben"]:
            zeilen.append([a["titel"], a["bereich"], a["prio"] or "",
                           a["dauer"] or "",
                           str(a["haelt_auf"]) if a["haelt_auf"] else ""])
        wort = "sofort möglich" if stufe["stufe"] == 1 else f"nach Stufe {stufe['stufe'] - 1}"
        bloecke.append(f"## Stufe {stufe['stufe']} — {wort}\n"
                       + table(zeilen, ["aufgabe", "bereich", "prio", "dauer", "hält auf"]))

    if d["schluessel"]:
        zeilen = [[a["titel"], a["bereich"], str(a["haelt_auf"])]
                  for a in d["schluessel"][:8]]
        bloecke.append("## Schlüsselaufgaben — was am meisten aufhält\n"
                       + table(zeilen, ["aufgabe", "bereich", "hält auf"]))

    if d["ring"]:
        zeilen = [[a["titel"], ", ".join(a["braucht"])] for a in d["ring"]]
        bloecke.append("## Ring — lösen sich nie von selbst\n"
                       + table(zeilen, ["aufgabe", "braucht"])
                       + "\nEin `@braucht:` in diesem Kreis muss weg.")

    return "\n\n".join(bloecke)
