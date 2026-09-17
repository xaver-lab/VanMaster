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

from tools import build, media, parts, status, tasks  # noqa: E402
from tools.common import PART_KATEGORIEN, fail  # noqa: E402


def zeige(text: str, daten=None, als_json: bool = False) -> None:
    if als_json:
        print(json.dumps(daten, ensure_ascii=False, indent=2))
    else:
        print(text)


def cmd_sync(args) -> None:
    schritte = [parts.to_markdown(), media.index_text(), build.build()]
    try:
        schritte.insert(1, parts.to_excel())
    except PermissionError:
        schritte.insert(1, "Excel übersprungen — Datei ist gerade geöffnet.")
    print("Sync:\n" + "\n".join(f"  - {s}" for s in schritte))


def cmd_status(args) -> None:
    if args.json:
        zeige("", build.daten()["kennzahlen"], True)
        return
    print(status.brief() if args.brief else status.full())


def cmd_tasks(args) -> None:
    if args.was == "next":
        if args.json:
            alle = tasks.load()
            nach_id = {a["id"]: a for a in alle}
            offen = [a for a in tasks.blaetter(alle)
                     if a["status"] not in tasks.ERLEDIGT]
            zeige("", [a for a in offen if not tasks.blocker(a, nach_id)], True)
            return
        print(tasks.next_tasks(limit=args.limit, bereich=args.bereich or ""))
    else:
        print(tasks.overview_text())


def cmd_task(args) -> None:
    ziel = {"done": "erledigt", "start": "laeuft",
            "open": "offen", "drop": "verworfen"}[args.was]
    print(tasks.set_status(args.id, ziel))


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


def cmd_system(args) -> None:
    print(status.system(args.name))


def cmd_find(args) -> None:
    print(status.find(args.text))


def cmd_media(args) -> None:
    print(media.einsortieren(bereich=args.bereich or "", apply=not args.dry,
                         ordner=args.ordner or ""))


def cmd_build(args) -> None:
    print(build.build())


def cmd_ui(args) -> None:
    from tools import ui
    ui.run()


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="camper", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="befehl", required=True)

    s = sub.add_parser("sync", help="alles neu erzeugen")
    s.set_defaults(func=cmd_sync)

    s = sub.add_parser("status", help="Lageüberblick")
    s.add_argument("--brief", action="store_true", help="kompakt für den Chat")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_status)

    s = sub.add_parser("tasks", help="Aufgabenüberblick")
    s.add_argument("was", nargs="?", default="list", choices=["list", "next"])
    s.add_argument("--bereich")
    s.add_argument("--limit", type=int, default=8)
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_tasks)

    s = sub.add_parser("task", help="Aufgabe abhaken oder umstellen")
    s.add_argument("was", choices=["done", "start", "open", "drop"])
    s.add_argument("id")
    s.set_defaults(func=cmd_task)

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

    s = sub.add_parser("system", help="Lage eines Systems")
    s.add_argument("name")
    s.set_defaults(func=cmd_system)

    s = sub.add_parser("find", help="Volltextsuche, liefert Pfade")
    s.add_argument("text")
    s.set_defaults(func=cmd_find)

    s = sub.add_parser("media", help="Bilder und Dokumente aus _input einsortieren")
    s.add_argument("--bereich")
    s.add_argument("--ordner", help="nur diesen Unterordner von _input/")
    s.add_argument("--dry", action="store_true", help="nur zeigen, nichts bewegen")
    s.set_defaults(func=cmd_media)

    s = sub.add_parser("build", help="Dashboard-Daten bauen")
    s.set_defaults(func=cmd_build)

    s = sub.add_parser("ui", help="Tkinter-Fenster")
    s.set_defaults(func=cmd_ui)
    return p


def main(argv: list[str] | None = None) -> None:
    # Windows-Konsole ist cp1252 — Umlaute und Balken brauchen UTF-8.
    for strom in (sys.stdout, sys.stderr):
        try:
            strom.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    args = parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
