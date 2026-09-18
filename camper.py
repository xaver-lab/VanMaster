#!/usr/bin/env python3
"""VanMaster — ein Einstiegspunkt für alle Projektbefehle.

    python camper.py status --brief
    python camper.py tasks next
    python camper.py parts excel
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools import (  # noqa: E402
    bauteile, bereiche, build, kern, media, parts, status, tasks, web,
)
from tools.common import (  # noqa: E402
    BAUTEIL_ART, BAUTEIL_STATUS, MASSQUELLE, PART_KATEGORIEN, SORTIERUNGEN,
    STANDARD_SORTIERUNG, fail,
)
from tools.kern.format import PRIOS


def sortierung(args) -> str:
    """Reihenfolge der Bereiche — überall dieselbe, siehe tools/bereiche.py."""
    return getattr(args, "sortierung", None) or STANDARD_SORTIERUNG


def zeige(text: str, daten=None, als_json: bool = False) -> None:
    if als_json:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
    else:
        print(text)


def cmd_sync(args) -> None:
    schritte = [parts.to_markdown(), media.index_text(),
                build.build(sortierung(args))]
    for name, mach in (("Stückliste", parts.to_excel),
                       ("Einzelteile", bauteile.to_excel)):
        try:
            schritte.insert(1, mach())
        except PermissionError:
            schritte.insert(1, f"Excel {name} übersprungen — Datei ist offen.")
    print("Sync:\n" + "\n".join(f"  - {s}" for s in schritte))


def cmd_status(args) -> None:
    art = sortierung(args)
    if args.json:
        zeige("", build.daten(art)["kennzahlen"], True)
        return
    print(status.brief(art) if args.brief else status.full(art))


def cmd_tasks(args) -> None:
    if args.was == "next":
        if args.json:
            alle = tasks.load()
            nach_id = {a["id"]: a for a in alle}
            offen = [a for a in tasks.blaetter(alle)
                     if a["status"] not in tasks.ERLEDIGT]
            zeige("", [a for a in offen if not tasks.blocker(a, nach_id)], True)
            return
        print(tasks.next_tasks(limit=args.limit, bereich=args.bereich or "",
                               sortierung=sortierung(args)))
    else:
        print(tasks.overview_text(sortierung(args)))


def cmd_task(args) -> None:
    if args.was in ("done", "start", "open", "drop", "block"):
        ziel = {"done": "erledigt", "start": "laeuft", "open": "offen",
                "drop": "verworfen", "block": "blockiert"}[args.was]
        print(tasks.set_status(args.id, ziel))
    elif args.was == "add":
        print(tasks.add(args.bereich, args.titel, gruppe=args.gruppe or "",
                        unter=args.unter or "", prio=args.prio or ""))
    elif args.was == "delete":
        print(tasks.delete(args.id))
    elif args.was == "rename":
        print(tasks.rename(args.id, args.titel))


def cmd_brief(args) -> None:
    print(tasks.brief(args.id))


def cmd_parts(args) -> None:
    if args.was == "query":
        rows = parts.filtered(parts.load(), kategorie=args.kategorie,
                              status=args.status, haendler=args.haendler,
                              fuer_aufgabe=args.aufgabe, text=args.text)
        zeige(parts.query_text(rows), rows, args.json)
    elif args.was == "excel":
        print(parts.to_excel())
    elif args.was == "import":
        print(parts.import_excel(apply=args.apply))
    elif args.was == "md":
        print(parts.to_markdown())
    elif args.was == "set":
        if not (args.id and args.feld and args.wert):
            fail("Aufruf: parts set <id> <feld> <wert>")
        print(parts.set_field(args.id, args.feld, args.wert))
    elif args.was == "add":
        if not args.titel:
            fail("Aufruf: parts add <titel> --kategorie Elektrik")
        print(parts.add(args.titel, args.kategorie or "Verbrauchsmaterial",
                        preis=args.preis, haendler=args.haendler,
                        fuer_aufgabe=args.aufgabe))
    else:
        print(parts.overview_text())


def cmd_buy(args) -> None:
    print(parts.buy_next(limit=args.limit))


def cmd_bereich(args) -> None:
    if args.json:
        b = bereiche.find(args.name)
        zeige("", b or {}, True)
        return
    print(status.bereich(args.name))


def cmd_bereich_set(args) -> None:
    if args.kopf:
        for eintrag in args.kopf:
            if "=" not in eintrag:
                fail("Aufruf: bereich set <Bereich> --kopf feld=wert")
            feld, wert = eintrag.split("=", 1)
            print(bereiche.set_head(args.bereich, feld.strip(), wert.strip()))
        return
    if not args.abschnitt:
        fail("Aufruf: bereich set <Bereich> <Abschnitt> [--text \"…\"] "
             "(oder von stdin) — oder bereich set <Bereich> --kopf feld=wert")
    text = args.text if args.text is not None else sys.stdin.read()
    print(bereiche.set_section(args.bereich, args.abschnitt, text))


def cmd_check(args) -> None:
    from dataclasses import asdict

    befunde = kern.pruefen()
    if args.json:
        zeige("", [asdict(b) for b in befunde], True)
    else:
        if not befunde:
            print("Keine Abweichungen gefunden.")
        else:
            zeilen = [f"{b.datei}:{b.zeile}  {b.art}  {b.meldung}"
                     for b in befunde]
            anzahl_fehler = sum(1 for b in befunde if b.art == "fehler")
            anzahl_warnungen = len(befunde) - anzahl_fehler
            zeilen.append("")
            zeilen.append(f"{anzahl_fehler} Fehler, {anzahl_warnungen} Warnungen")
            print("\n".join(zeilen))
    if any(b.art == "fehler" for b in befunde):
        sys.exit(1)


def cmd_bereiche(args) -> None:
    art = sortierung(args)
    if args.json:
        zeige("", build.daten(art)["bereiche"], True)
        return
    print(bereiche.overview_text(art))


def cmd_bauteile(args) -> None:
    if args.was == "query":
        rows = bauteile.filtered(bauteile.load(), bereich=args.bereich,
                                 art=args.art, status=args.status,
                                 text=args.text)
        zeige(bauteile.query_text(rows), rows, args.json)
    elif args.was == "excel":
        print(bauteile.to_excel())
    elif args.was == "import":
        print(bauteile.import_excel(apply=args.apply))
    elif args.was == "set":
        if not (args.id and args.feld and args.wert):
            fail("Aufruf: bauteile set <id> <feld> <wert>")
        print(bauteile.set_field(args.id, args.feld, args.wert))
    elif args.was == "add":
        if not (args.titel and args.bereich):
            fail("Aufruf: bauteile add --titel \"Seitenwand\" --bereich Möbel")
        print(bauteile.add(
            args.titel, args.bereich, art=args.art, material=args.material,
            laenge_mm=args.laenge, breite_mm=args.breite, dicke_mm=args.dicke,
            anzahl=args.anzahl, teil_id=args.teil, fuer_aufgabe=args.aufgabe,
            massquelle=args.massquelle, notiz=args.notiz))
    else:
        print(bauteile.overview_text())


def cmd_find(args) -> None:
    print(status.find(args.text))


def cmd_media(args) -> None:
    print(media.einsortieren(bereich=args.bereich or "", apply=not args.dry,
                         ordner=args.ordner or ""))


def cmd_build(args) -> None:
    print(build.build(sortierung(args)))


def cmd_serve(args) -> None:
    if args.alt:
        from tools import serve
        serve.run(port=args.port, offen=args.offen, oeffnen=not args.kein_browser,
                  sortierung=sortierung(args))
        return
    from tools.server import start
    start.run(port=args.port, offen=args.offen, oeffnen=not args.kein_browser,
              sortierung=sortierung(args), kein_commit=args.kein_commit)


def cmd_ui(args) -> None:
    from tools import ui
    ui.run()


def cmd_web(args) -> None:
    if args.web_befehl == "install":
        print(web.install())
    elif args.web_befehl == "build":
        print(web.build())
    elif args.web_befehl == "dev":
        web.dev()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="camper", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="befehl", required=True)

    s = sub.add_parser("sync", help="alles neu erzeugen")
    s.add_argument("--sortierung", choices=SORTIERUNGEN,
                   default=STANDARD_SORTIERUNG,
                   help="Reihenfolge der Themen: baustellen (Status und "
                        "offene Aufgaben), phase (Bauabschnitt aus dem Kopf "
                        "der Bereichsdatei) oder name")
    s.set_defaults(func=cmd_sync)

    s = sub.add_parser("status", help="Lageüberblick")
    s.add_argument("--brief", action="store_true", help="kompakt für den Chat")
    s.add_argument("--json", action="store_true")
    s.add_argument("--sortierung", choices=SORTIERUNGEN,
                   default=STANDARD_SORTIERUNG,
                   help="Reihenfolge der Themen: baustellen (Status und "
                        "offene Aufgaben), phase (Bauabschnitt aus dem Kopf "
                        "der Bereichsdatei) oder name")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("tasks", help="Aufgabenüberblick")
    s.add_argument("was", nargs="?", default="list", choices=["list", "next"])
    s.add_argument("--bereich")
    s.add_argument("--limit", type=int, default=8)
    s.add_argument("--json", action="store_true")
    s.add_argument("--sortierung", choices=SORTIERUNGEN,
                   default=STANDARD_SORTIERUNG,
                   help="Reihenfolge der Themen: baustellen (Status und "
                        "offene Aufgaben), phase (Bauabschnitt aus dem Kopf "
                        "der Bereichsdatei) oder name")
    s.set_defaults(func=cmd_tasks)

    s = sub.add_parser("task", help="Aufgabe anlegen, umstellen, umbenennen, löschen")
    task_sub = s.add_subparsers(dest="was", required=True)

    for name, hilfe in (("done", "als erledigt markieren"),
                        ("start", "als laufend markieren"),
                        ("open", "als offen markieren"),
                        ("drop", "als verworfen markieren"),
                        ("block", "als blockiert markieren")):
        sp = task_sub.add_parser(name, help=hilfe)
        sp.add_argument("id")
        sp.set_defaults(func=cmd_task)

    sp = task_sub.add_parser("add", help="neue Aufgabe anlegen")
    sp.add_argument("bereich")
    sp.add_argument("titel")
    sp.add_argument("--gruppe", help="Gruppe (### Überschrift) im Aufgabenabschnitt")
    sp.add_argument("--unter", help="ID der Eltern-Aufgabe, legt einen Unterpunkt an")
    sp.add_argument("--prio", choices=list(PRIOS))
    sp.set_defaults(func=cmd_task)

    sp = task_sub.add_parser("delete", help="Aufgabe löschen (mit Unterpunkten)")
    sp.add_argument("id")
    sp.set_defaults(func=cmd_task)

    sp = task_sub.add_parser("rename", help="Titel ändern")
    sp.add_argument("id")
    sp.add_argument("titel")
    sp.set_defaults(func=cmd_task)

    s = sub.add_parser("brief", help="alles zu einer Aufgabe")
    s.add_argument("id")
    s.set_defaults(func=cmd_brief)

    s = sub.add_parser("parts", help="Stückliste")
    s.add_argument("was", nargs="?", default="overview",
                   choices=["overview", "query", "excel", "import", "md",
                            "set", "add"])
    s.add_argument("id", nargs="?")
    s.add_argument("feld", nargs="?")
    s.add_argument("wert", nargs="?")
    s.add_argument("--titel")
    s.add_argument("--kategorie", choices=PART_KATEGORIEN)
    s.add_argument("--status")
    s.add_argument("--haendler")
    s.add_argument("--aufgabe")
    s.add_argument("--preis")
    s.add_argument("--text")
    s.add_argument("--apply", action="store_true", help="Import wirklich schreiben")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_parts)

    s = sub.add_parser("buy", help="Einkaufsvorschlag")
    s.add_argument("was", nargs="?", default="next", choices=["next"])
    s.add_argument("--limit", type=int, default=0)
    s.set_defaults(func=cmd_buy)

    s = sub.add_parser("bereich", help="alles zu einem Arbeitsbereich")
    s.add_argument("name")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_bereich)

    s = sub.add_parser("bereich-set", prog="camper bereich set",
                       help="Abschnitt oder Kopf-Feld eines Bereichs setzen "
                            "(aufgerufen als 'camper bereich set …')")
    s.add_argument("bereich")
    s.add_argument("abschnitt", nargs="?",
                   help="z. B. Beschreibung, Stand, Auslegung, Notizen, Links")
    s.add_argument("--text", help="neuer Inhalt; ohne Angabe wird von stdin gelesen")
    s.add_argument("--kopf", action="append", default=[],
                   metavar="feld=wert", help="Kopf-Feld setzen, z. B. phase=3")
    s.set_defaults(func=cmd_bereich_set)

    s = sub.add_parser("bereiche", help="alle Arbeitsbereiche")
    s.add_argument("--json", action="store_true")
    s.add_argument("--sortierung", choices=SORTIERUNGEN,
                   default=STANDARD_SORTIERUNG,
                   help="Reihenfolge der Themen: baustellen (Status und "
                        "offene Aufgaben), phase (Bauabschnitt aus dem Kopf "
                        "der Bereichsdatei) oder name")
    s.set_defaults(func=cmd_bereiche)

    s = sub.add_parser("bauteile", help="Einzelteile mit Maßen")
    s.add_argument("was", nargs="?", default="overview",
                   choices=["overview", "query", "excel", "import",
                            "set", "add"])
    s.add_argument("id", nargs="?")
    s.add_argument("feld", nargs="?")
    s.add_argument("wert", nargs="?")
    s.add_argument("--titel")
    s.add_argument("--bereich")
    s.add_argument("--art", choices=BAUTEIL_ART)
    s.add_argument("--material")
    s.add_argument("--laenge", help="Länge in mm")
    s.add_argument("--breite", help="Breite in mm")
    s.add_argument("--dicke", help="Dicke in mm")
    s.add_argument("--anzahl")
    s.add_argument("--teil", help="Kennung des Stücklisten-Teils, aus dem es entsteht")
    s.add_argument("--aufgabe")
    s.add_argument("--massquelle", choices=MASSQUELLE)
    s.add_argument("--status", choices=BAUTEIL_STATUS)
    s.add_argument("--notiz")
    s.add_argument("--text")
    s.add_argument("--apply", action="store_true", help="Import wirklich schreiben")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_bauteile)

    s = sub.add_parser("check", help="Formatprüfung (FORMAT.md), Exit-Code 1 bei Fehlern")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_check)

    s = sub.add_parser("find", help="Volltextsuche, liefert Pfade")
    s.add_argument("text")
    s.set_defaults(func=cmd_find)

    s = sub.add_parser("media", help="Bilder und Dokumente aus _input einsortieren")
    s.add_argument("--bereich")
    s.add_argument("--ordner", help="nur diesen Unterordner von _input/")
    s.add_argument("--dry", action="store_true", help="nur zeigen, nichts bewegen")
    s.set_defaults(func=cmd_media)

    s = sub.add_parser("build", help="Dashboard-Daten bauen")
    s.add_argument("--sortierung", choices=SORTIERUNGEN,
                   default=STANDARD_SORTIERUNG,
                   help="Reihenfolge der Themen: baustellen (Status und "
                        "offene Aufgaben), phase (Bauabschnitt aus dem Kopf "
                        "der Bereichsdatei) oder name")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("serve", help="Dashboard mit Schreibzugriff starten")
    s.add_argument("--port", type=int, default=8765)
    s.add_argument("--offen", action="store_true",
                   help="auch vom Handy im WLAN erreichbar")
    s.add_argument("--kein-browser", dest="kein_browser", action="store_true",
                   help="Browser nicht selbst öffnen")
    s.add_argument("--alt", action="store_true",
                   help="altes Dashboard (tools/serve.py) statt der neuen App — Rückfallweg")
    s.add_argument("--kein-commit", dest="kein_commit", action="store_true",
                   help="keine Auto-Commits der Web-Änderungen (nur neue App)")
    s.add_argument("--sortierung", choices=SORTIERUNGEN,
                   default=STANDARD_SORTIERUNG,
                   help="Reihenfolge der Themen: baustellen (Status und "
                        "offene Aufgaben), phase (Bauabschnitt aus dem Kopf "
                        "der Bereichsdatei) oder name")
    s.set_defaults(func=cmd_serve)

    s = sub.add_parser("ui", help="Tkinter-Fenster")
    s.set_defaults(func=cmd_ui)

    s = sub.add_parser("web", help="Oberfläche unter web/ (Vite/Svelte) bauen oder starten")
    web_sub = s.add_subparsers(dest="web_befehl", required=True)
    web_sub.add_parser("install", help="Abhängigkeiten installieren (npm install)")
    web_sub.add_parser("build", help="Produktionsbau nach web/dist (npm run build)")
    web_sub.add_parser("dev", help="Vite-Dev-Server gegen den laufenden FastAPI-Server (npm run dev)")
    s.set_defaults(func=cmd_web)
    return p


def main(argv: list[str] | None = None) -> None:
    # Windows-Konsole ist cp1252 — Umlaute und Balken brauchen UTF-8.
    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    argv = list(sys.argv[1:] if argv is None else argv)
    # "bereich set …" ist intern ein eigener Unterbefehl (argparse kann eine
    # feste Kennung wie 'set' nicht neben einem freien Bereichsnamen an
    # derselben Stelle unterscheiden).
    if len(argv) >= 2 and argv[0] == "bereich" and argv[1] == "set":
        argv = ["bereich-set"] + argv[2:]
    args = parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
