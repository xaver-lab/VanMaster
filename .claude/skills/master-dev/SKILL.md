---
name: master-dev
description: Baut und repariert die VanMaster-Pipeline - camper.py, die Module unter tools/, die Datenformate und das Dashboard unter docs/. Nutze diesen Skill, wenn am Werkzeug selbst etwas fehlt, klemmt oder dazukommen soll: neuer Befehl, neue Auswertung, neue Dashboard-Ansicht, Datenformat ändern, Fehler in der Ausgabe.
---

# master-dev — das Werkzeug bauen

Auftrag: Die Pipeline soll den Ausbau tragen. Befehle mit antwortfertiger
Ausgabe. Ein Dashboard, das am Laptop gut funktioniert (Handy kommt später, siehe unten). Datenformate, die von Hand bearbeitbar bleiben.

## Aufbau

```
camper.py          Einstiegspunkt, argparse-Dispatch
tools/common.py    Pfade, Slug, YAML-Kopf, Tabellen- und Balkenausgabe
tools/parts.py     Stückliste: CSV <-> Excel <-> Markdown
tools/tasks.py     Aufgabenbaum lesen, auswerten, Kästchen umsetzen
tools/status.py    Lageberichte, Systemsicht, Volltextsuche
tools/build.py     docs/data.json + docs/data.js
tools/media.py     Bilder einsortieren, verkleinern, verlinken
tools/serve.py     Dashboard-Server mit Schreib-API (nur Standardbibliothek)
tools/ui.py        Tkinter-Fenster
docs/index.html    Gerüst, lädt css/ und js/ in fester Reihenfolge
docs/css/          basis, aufgaben, leiste, teile, themen, medien, palette, handy
docs/js/           grund (Helfer, Laden, Bausteine, Toasts), markdown, start,
                   themen, aufgaben, teile, zuschnitt, medien, palette,
                   bedienung (Routing, Ereignisse, Start — muss zuletzt laden)
                   Kein Build-Werkzeug, keine Module: alle Dateien teilen
                   einen globalen Raum. Neue Datei → in index.html eintragen.
```

Das Dashboard läuft in zwei Betriebsarten: statisch (Doppelklick, GitHub
Pages) nur lesend, mit `camper serve` schreiben Kästchen und Statusknöpfe
über `POST api/task` und `POST api/teil` direkt in Vault und `parts.csv`.
Neue Interaktionen gehören auf beide Wege: schreibend über die API, sonst
den passenden `camper`-Befehl zum Kopieren anbieten.

Wahrheit sind `data/parts.csv` und die Markdown-Dateien im Vault. Alles unter
`data/generated/`, `vault/Stückliste/` und `docs/data.*` ist Ausgabe.

## Arbeitsweise

1. Erst verstehen, wie es läuft, dann ändern.
2. Jede neue Funktion braucht **einen Befehl und eine Dashboard-Ansicht** —
   sonst ist sie am Van nicht da.
3. Nach Änderungen `python camper.py sync` durchlaufen lassen und die Ausgabe
   ansehen.
4. Dashboard prüfen: siehe „Prüfen im Browser“.

## Sparsam lesen

Das Dashboard ist groß genug, um bei jeder Änderung viel Kontext zu kosten.
Diese Regeln gelten ohne Ausnahme:

- `docs/data.json` und `docs/data.js` werden **nie** gelesen oder durchsucht
  (Lesesperre in `.claude/settings.json`). `data.js` ist eine einzige Zeile —
  jeder Treffer liefert die ganze Datei. Aufbau der Daten: `tools/build.py`
  lesen oder `python camper.py <befehl> --json`; einzelne Werte im Browser mit
  einem kurzen Skript (`Object.keys(DATEN)`, `DATEN.teile[0]`).
- Nie das ganze Dashboard lesen. Nur die Datei der betroffenen Ansicht aus
  `docs/js/` und `docs/css/`, `grund.js` nur bei Bedarf.
- Auch dort erst die Stelle suchen, dann den Ausschnitt lesen (Offset und
  Limit), nicht die ganze Datei.
- Unklar, wo etwas steckt, oder mehr als drei Dateien betroffen: die Suche an
  einen Explore-Subagenten geben, der nur Fundstellen mit Zeilennummern
  zurückmeldet.
- Diffs ohne erzeugte Dateien: `git diff -- docs/js docs/css docs/index.html`.
- Nach einer Änderung die Datei nicht erneut lesen, um sie zu prüfen.

## Prüfen im Browser

- Preview `dashboard` (nur lesen) oder `camper-serve` (mit Schreibzugriff)
  aus `.claude/launch.json`.
- Nur am Laptop. Handy-Ansicht nicht prüfen, `css/handy.css` nicht anfassen.
- Geprüft wird über Text: Konsolenfehler, Netzwerkanfragen, Seitentext, kurze
  Skripte im Browser. **Keine Screenshots bei Zwischenschritten.** Höchstens
  einer am Ende einer fertigen Änderung, verkleinert (Skalierung 0.5). Der
  Nutzer gibt selbst Rückmeldung.
- Größere Prüfungen, die mehrere Ansichten durchklicken, an einen
  Subagenten geben, der einen kurzen Befund zurückmeldet. Die eigentliche
  Code-Änderung macht der Hauptagent selbst.

## Handy-Ansicht — zurückgestellt

Der Nutzer arbeitet derzeit nur am Laptop. Die Handy-Ansicht (unter 820 px,
`css/handy.css`) wird erst verbessert, wenn der Nutzer das ausdrücklich
anstößt. Bis dahin nicht prüfen, nicht verbessern, nicht vorschlagen. Nur
nichts mutwillig kaputt machen.

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
