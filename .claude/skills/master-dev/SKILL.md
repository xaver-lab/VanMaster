---
name: master-dev
description: Baut und repariert die VanMaster-Pipeline - camper.py, den Datenkern unter tools/kern/, den Server unter tools/server/, die Datenformate und das Svelte-Dashboard unter web/. Nutze diesen Skill, wenn am Werkzeug selbst etwas fehlt, klemmt oder dazukommen soll: neuer Befehl, neue Auswertung, neue Dashboard-Ansicht, Datenformat ändern, Fehler in der Ausgabe.
---

# master-dev — das Werkzeug bauen

Auftrag: Die Pipeline soll den Ausbau tragen. Befehle mit antwortfertiger
Ausgabe. Ein Dashboard, das am Laptop gut funktioniert (Handy nur lesend über
Pages, siehe unten). Datenformate, die von Hand bearbeitbar bleiben — das
Format steht in `FORMAT.md`, die Geschichte des Umbaus in `UMBAU.md`.

## Aufbau

```
camper.py            Einstiegspunkt, argparse-Dispatch
tools/kern/          Datenkern — einzige Stelle, die Vault und CSVs liest und
                     schreibt: lesen, aufgaben, abschnitte, tabellen, datei
                     (Hash je Datei, Konflikt bei veraltetem Stand), pruefen
tools/common.py      Pfade, Slug, Vokabular, Tabellen- und Balkenausgabe
tools/parts.py       Stückliste: CSV <-> Excel <-> Markdown
tools/bauteile.py    Einzelteile/Zuschnitt: CSV <-> Excel
tools/tasks.py       Aufgabenbaum auswerten
tools/bereiche.py    Bereichsbefehle (`bereich set`)
tools/status.py      Lageberichte, Systemsicht, Volltextsuche
tools/build.py       Kennzahlen und Kategorien für Server und Befehle
tools/media.py       Bilder einsortieren, verkleinern (→ data/generated/medien/)
tools/server/        FastAPI: app (REST, 409 bei Konflikt), daten (/api/daten),
                     live (SSE /api/live), commit (gesammelte Auto-Commits),
                     start (`camper serve`, liefert web/dist und /medien),
                     schema (Pydantic → web/src/lib/api-typen.ts)
tools/web.py         `camper web build|dev|check|daten` (npm aus ~/nodejs oder PATH)
tools/ui.py          Tkinter-Fenster
web/src/             Svelte 5 + TypeScript. lib/daten.svelte.ts (Store, SSE,
                     Schreibfunktionen), lib/router.svelte.ts, lib/ui/
                     (Bausteine, siehe web/DESIGN.md), lib/<ansicht>/,
                     routen/ (eine Datei je Ansicht)
.github/workflows/pages.yml   baut bei jedem Push die Leseansicht für Pages
tests/               pytest, Fixture `repo` kopiert vault/ und data/ nach tmp
```

Das Dashboard läuft in zwei Betriebsarten: mit `camper serve` schreibend über
die REST-API (jede Schreibanfrage trägt den Dateihash), auf GitHub Pages rein
lesend aus `data.json` (`camper web daten`). `Schreibbar.svelte` blendet im
Lesemodus alle Bearbeitungselemente aus. Was im Web bearbeitbar ist, liefert
`/api/daten` unter `bearbeitbar`, das Vokabular unter `vokabular` — keine
eigenen Listen im Web.

Wahrheit sind `data/parts.csv`, `data/bauteile.csv` und die Markdown-Dateien
im Vault. Alles unter `data/generated/`, `vault/Stückliste/` und `web/dist/`
ist Ausgabe.

## Arbeitsweise

1. Erst verstehen, wie es läuft, dann ändern.
2. Jede neue Funktion braucht **einen Befehl und eine Dashboard-Ansicht** —
   sonst ist sie am Van nicht da. Schreiben immer über `tools/kern/`.
3. Server-Modelle geändert: `python -m tools.server.schema` für die TS-Typen.
4. Tests: `PYTHONIOENCODING=utf-8 python -m pytest -q tests/<datei>`, am Ende
   einer größeren Änderung einmal alles.
5. Web geändert: `python camper.py web check` (0 Fehler, 0 Warnungen) und
   `python camper.py web build` — der Server liefert `web/dist` aus.
6. Nach inhaltlichen Änderungen `python camper.py sync` durchlaufen lassen.
7. Dashboard prüfen: siehe „Prüfen im Browser“.

## Sparsam lesen

Diese Regeln gelten ohne Ausnahme:

- `web/dist/` und `web/src/lib/api-schema.json` werden **nie** gelesen oder
  durchsucht — erzeugt und groß. Aufbau der Daten: `tools/server/daten.py`
  und `modelle.py` bzw. `web/src/lib/api-typen.ts` lesen, oder
  `python camper.py <befehl> --json`.
- Nie das ganze Dashboard lesen. Nur die Dateien der betroffenen Ansicht aus
  `web/src/lib/<ansicht>/` und `web/src/routen/`; neue Ansichten erst
  `web/DESIGN.md` lesen und nur Bausteine aus `lib/ui/` benutzen.
- Auch dort erst die Stelle suchen, dann den Ausschnitt lesen (Offset und
  Limit), nicht die ganze Datei.
- Unklar, wo etwas steckt, oder mehr als drei Dateien betroffen: die Suche an
  einen Explore-Subagenten geben, der nur Fundstellen mit Zeilennummern
  zurückmeldet.
- Diffs ohne erzeugte Dateien: `git diff -- web/src tools tests`.
- Nach einer Änderung die Datei nicht erneut lesen, um sie zu prüfen.

## Prüfen im Browser

- Preview `camper-neu` (Port 8765, mit Auto-Commit) oder `camper-pruef`
  (Port 8767, `--kein-commit`) aus `.claude/launch.json`. Selbst gestartete
  Prüfserver immer mit `--kein-commit`.
- Den Tab mit `tabs_select` sichtbar machen — im versteckten Fenster kommen
  Enter und Escape nicht an.
- Nur am Laptop. Handy-Ansicht nicht prüfen.
- Geprüft wird über Text: Konsolenfehler, Netzwerkanfragen, Seitentext, kurze
  Skripte im Browser. **Keine Screenshots bei Zwischenschritten.** Höchstens
  einer am Ende einer fertigen Änderung, verkleinert (Skalierung 0.5). Der
  Nutzer gibt selbst Rückmeldung.
- Größere Prüfungen, die mehrere Ansichten durchklicken, an einen
  Subagenten geben, der einen kurzen Befund zurückmeldet. Die eigentliche
  Code-Änderung macht der Hauptagent selbst.

## Handy-Ansicht — zurückgestellt

Der Nutzer arbeitet derzeit nur am Laptop. Das Handy sieht die Leseansicht auf
GitHub Pages (https://xaver-lab.github.io/VanMaster/). Sie wird erst
verbessert, wenn der Nutzer das ausdrücklich anstößt. Bis dahin nicht prüfen,
nicht verbessern, nicht vorschlagen. Nur nichts mutwillig kaputt machen.

## Regeln der Ausgabe

Jeder Befehl gibt kompakten Text aus, den man direkt in den Chat stellen kann —
keine Rohdatenwüsten. `--json` liefert bei Bedarf die Rohdaten.

## Umgebung

Python 3.13, User-Scope, keine Adminrechte (`pip install --user -r
requirements.txt`). Node 24 nur als Build-Werkzeug, portabel unter `~/nodejs/`
(nicht im PATH) oder systemweit. Für `npx` in der Sitzung
`PATH=~/nodejs:$PATH` setzen.
Die Windows-Konsole ist cp1252 — `camper.py` stellt stdout auf UTF-8 um; bei
eigenen Testaufrufen `PYTHONIOENCODING=utf-8` setzen.

## Grenzen

Inhalte darfst du anfassen, wenn es der Sache dient — Testdaten, Migrationen,
Umbauten. Inhaltliche Entscheidungen (welche Batterie, welches Layout) triffst
du nicht im Alleingang.
