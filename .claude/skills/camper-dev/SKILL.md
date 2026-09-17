---
name: camper-dev
description: Baut und repariert die VanMaster-Pipeline - camper.py, die Module unter tools/, die Datenformate und das Dashboard unter docs/. Nutze diesen Skill, wenn am Werkzeug selbst etwas fehlt, klemmt oder dazukommen soll: neuer Befehl, neue Auswertung, neue Dashboard-Ansicht, Datenformat ändern, Fehler in der Ausgabe.
---

# camper-dev — das Werkzeug bauen

Auftrag: Die Pipeline soll den Ausbau tragen. Befehle mit antwortfertiger
Ausgabe. Ein Dashboard, das am Van auf dem Handy so gut funktioniert wie am
Laptop. Datenformate, die von Hand bearbeitbar bleiben.

## Aufbau

```
camper.py          Einstiegspunkt, argparse-Dispatch
tools/common.py    Pfade, Slug, YAML-Kopf, Tabellen- und Balkenausgabe
tools/parts.py     Stückliste: CSV <-> Excel <-> Markdown
tools/tasks.py     Aufgabenbaum lesen, auswerten, Kästchen umsetzen
tools/status.py    Lageberichte, Systemsicht, Volltextsuche
tools/build.py     docs/data.json + docs/data.js
tools/media.py     Bilder einsortieren, verkleinern, verlinken
tools/ui.py        Tkinter-Fenster
docs/              index.html, style.css, app.js — kein Build-Werkzeug
```

Wahrheit sind `data/parts.csv` und die Markdown-Dateien im Vault. Alles unter
`data/generated/`, `vault/Stückliste/` und `docs/data.*` ist Ausgabe.

## Arbeitsweise

1. Erst verstehen, wie es läuft, dann ändern.
2. Jede neue Funktion braucht **einen Befehl und eine Dashboard-Ansicht** —
   sonst ist sie am Van nicht da.
3. Nach Änderungen `python camper.py sync` durchlaufen lassen und die Ausgabe
   ansehen.
4. Dashboard prüfen: `python -m http.server 8765 --directory docs`, am
   Handyformat testen (375 px), nicht nur am Laptop.

## Regeln der Ausgabe

Jeder Befehl gibt kompakten Text aus, den man direkt in den Chat stellen kann —
keine Rohdatenwüsten. `--json` liefert bei Bedarf die Rohdaten.

## Umgebung

Python 3.13, User-Scope, keine Adminrechte (`pip install --user`).
Abhängigkeiten bewusst klein: `openpyxl`, `Pillow`, sonst Standardbibliothek.
Die Windows-Konsole ist cp1252 — `camper.py` stellt stdout auf UTF-8 um; bei
eigenen Testaufrufen `PYTHONIOENCODING=utf-8` setzen.

## Grenzen

Inhalte darfst du anfassen, wenn es der Sache dient — Testdaten, Migrationen,
Umbauten. Inhaltliche Entscheidungen (welche Batterie, welches Layout) triffst
du nicht im Alleingang.
