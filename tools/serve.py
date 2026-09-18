"""Kleiner Server für das Dashboard — liefert docs/ und nimmt Änderungen an.

    python camper.py serve            → http://localhost:8765
    python camper.py serve --port 80  → anderer Port
    python camper.py serve --offen    → auch vom Handy im WLAN erreichbar

Ohne diesen Server ist das Dashboard reine Anzeige; mit ihm schreiben die
Kästchen direkt in den Vault und die Statusknöpfe in parts.csv.
Nur Standardbibliothek, kein Framework.
"""
from __future__ import annotations

import json
import socket
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from . import build, parts, tasks
from .common import DASHBOARD_JSON, DOCS, STANDARD_SORTIERUNG
from .kern import tabellen as kern_tabellen

# Reihenfolge der Bereiche, mit der dieser Server data.json baut.
SORTIERUNG = STANDARD_SORTIERUNG

# Schreibende Zugriffe laufen nacheinander — die CSV und die Markdown-Dateien
# vertragen kein gleichzeitiges Schreiben aus zwei Browser-Tabs.
SCHLOSS = threading.Lock()


class Handler(SimpleHTTPRequestHandler):
    """Statische Dateien aus docs/ plus eine Handvoll API-Pfade."""

    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(DOCS), **kw)

    # ------------------------------------------------------------ Antworten

    def json_out(self, daten: dict, code: int = 200) -> None:
        rumpf = json.dumps(daten, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(rumpf)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(rumpf)

    def json_in(self) -> dict:
        laenge = int(self.headers.get("Content-Length") or 0)
        if not laenge:
            return {}
        return json.loads(self.rfile.read(laenge).decode("utf-8"))

    def end_headers(self):
        # data.json ändert sich bei jedem sync, Skript und Stil beim Bauen —
        # der Browser soll nachfragen statt Altes zu zeigen.
        if self.path.endswith((".json", ".js", ".css")):
            self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # -------------------------------------------------------------- Routen

    def do_GET(self):
        if self.path.startswith("/api/hallo"):
            # Der Zeitstempel von data.json sagt dem Browser, ob nebenher ein
            # `camper sync` gelaufen ist.
            stand = DASHBOARD_JSON.stat().st_mtime if DASHBOARD_JSON.exists() else 0
            self.json_out({"schreiben": True, "stand": round(stand, 3)})
            return
        super().do_GET()

    def do_POST(self):
        pfad = self.path.split("?")[0]
        try:
            nutzlast = self.json_in()
        except ValueError:
            self.json_out({"fehler": "kein gültiges JSON"}, 400)
            return

        try:
            with SCHLOSS:
                if pfad == "/api/task":
                    if "beschreibung" in nutzlast:
                        text = tasks.set_description(nutzlast["id"], nutzlast["beschreibung"])
                    else:
                        text = tasks.set_status(nutzlast["id"], nutzlast["status"])
                elif pfad == "/api/teil":
                    row = parts.find(nutzlast["id"])
                    if row is None:
                        raise ValueError(
                            f"Kein Teil mit der Kennung '{nutzlast['id']}'.")
                    alt = row.get(nutzlast["feld"], "")
                    kern_tabellen.teil_feld_setzen(
                        row["id"], nutzlast["feld"], nutzlast["wert"],
                        None, quelle="web")
                    text = (f"{row['titel']}: {nutzlast['feld']} {alt or '—'} "
                            f"→ {nutzlast['wert']}")
                elif pfad == "/api/sync":
                    text = "neu gebaut"
                else:
                    self.json_out({"fehler": "unbekannter Pfad"}, 404)
                    return
                frisch = build.daten(SORTIERUNG)
                build.schreiben(frisch)       # data.json + data.js nachziehen
                self.json_out({"ok": True, "text": text, "daten": frisch,
                               "stand": round(DASHBOARD_JSON.stat().st_mtime, 3)})
        except KeyError as fehler:
            self.json_out({"fehler": f"Feld fehlt: {fehler}"}, 400)
        except Exception as fehler:    # noqa: BLE001 — Fehler gehört in den Browser
            self.json_out({"fehler": str(fehler)}, 500)

    def log_message(self, format, *args):   # noqa: A002 — Signatur von http.server
        # Nur Schreibzugriffe sind interessant, nicht jedes Bild.
        if args and str(args[0]).startswith("POST"):
            print("  " + (format % args))


def adresse() -> str:
    """IP im WLAN — damit das Handy die Adresse abtippen kann."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def run(port: int = 8765, offen: bool = False, oeffnen: bool = True,
        sortierung: str = STANDARD_SORTIERUNG) -> None:
    global SORTIERUNG
    SORTIERUNG = sortierung
    build.build(sortierung)
    host = "0.0.0.0" if offen else "127.0.0.1"
    server = ThreadingHTTPServer((host, port), Handler)
    lokal = f"http://localhost:{port}/"
    print(f"Dashboard läuft — {lokal}")
    if offen:
        print(f"  am Handy im WLAN: http://{adresse()}:{port}/")
    print("  Kästchen und Statusknöpfe schreiben direkt. Strg+C beendet.")
    if oeffnen:
        webbrowser.open(lokal)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer beendet.")
    finally:
        server.server_close()
