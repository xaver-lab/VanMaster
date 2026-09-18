# Umbau — Svelte-Dashboard, FastAPI, Datenkern

Abhakplan für den Umbau des Werkzeugs. Diese Datei ist das Gedächtnis des
Umbaus: Jeder neue Chat liest nur sie, arbeitet den nächsten offenen Punkt ab
und hakt ihn hier ab. Stand, Entscheidungen und offene Fragen stehen hier,
nicht im Chat.

## Ziel

Ein sauberes Werkzeug zum aktiven Arbeiten am PC: Texte und Aufgaben im
Browser anlegen, bearbeiten, abhaken, löschen. Gleichzeitig arbeitet Claude
Code auf denselben Dateien im Repo. Das Handy zeigt nur an (GitHub Pages).

## Festgelegter Stack

| Schicht | Wahl |
|---|---|
| Wahrheit | Markdown (`vault/`) und CSV (`data/`) im Repo, streng definiertes Format, kein Obsidian-Bezug mehr |
| Datenkern | Python-Paket `tools/kern/` — einzige Stelle, die liest und schreibt |
| Befehle | `camper.py` (argparse), ruft den Kern |
| Server | FastAPI + uvicorn, Live-Aktualisierung, Schutz vor Überschreiben, gesammelte Auto-Commits |
| Oberfläche | Svelte 5 + Vite + TypeScript in `web/` |
| Handy | GitHub Action baut Oberfläche + Daten, GitHub Pages nur lesend |
| Node | Nur Build-Werkzeug, portabel unter `~/nodejs/` (nicht im PATH) |

Bearbeitbar im Web: Bereichsabschnitte Beschreibung, Stand, Notizen, Links;
Aufgaben anlegen, abhaken, umbenennen, beschreiben, löschen; bei Teilen
Status, Preis, Menge, Notiz; Einzelteile.
Nur lesend (pflegt Claude): Auslegung, Entscheidungen, Recherche, Anleitungen,
`phase`, alles Berechnete.
Löschen entfernt wirklich aus der Datei (Git sichert), zusätzlich bleibt der
Status „verworfen“.

Das alte Dashboard (`docs/`) läuft unverändert weiter, bis Phase 9 es ablöst.

## Arbeitsweise

- **Hauptchat steuert, Sonnet-Subagenten bauen.** Jeder Punkt mit
  `[Sonnet]` geht per Agent-Werkzeug (`model: "sonnet"`,
  `subagent_type: "general-purpose"`) an einen Subagenten. Punkte mit
  `[Haupt]` macht der Hauptchat selbst (Entscheidungen, Abnahme, Feinschliff
  nach Rückmeldung des Nutzers).
- **Auftrag an den Subagenten:** Punkt aus dieser Datei wörtlich, betroffene
  Dateien, Abnahmekriterium, Verweis auf `FORMAT.md` und die Regeln in
  `CLAUDE.md` (Node-Pfad, `pip install --user`, `docs/data.*` nie lesen).
  Er committet nicht selbst.
- **Rückmeldung des Subagenten:** höchstens zehn Zeilen — was gebaut,
  welche Dateien, Testergebnis, offene Fragen. Kein Code im Bericht.
- **Abnahme im Hauptchat:** `git diff --stat`, Tests laufen lassen,
  höchstens gezielte Ausschnitte lesen. Keine ganzen Dateien.
- **Unabhängige Punkte** derselben Phase dürfen parallel an mehrere
  Subagenten gehen, wenn sie verschiedene Dateien berühren.
- **Nach jedem abgenommenen Punkt:** hier abhaken, Kurznotiz ins Protokoll,
  committen und pushen (eine Zeile, `Co-Authored-By` wie in `CLAUDE.md`).
- **Browser-Prüfungen** nur per Subagent, Befund in wenigen Zeilen,
  höchstens ein Screenshot am Ende einer Phase.
- **Inhaltliche Fragen** (was bearbeitbar ist, wie etwas heißt) stellt der
  Hauptchat dem Nutzer — Subagenten entscheiden das nicht.
- **Kontext knapp:** Wird der Hauptchat lang, Stand hier sichern und dem
  Nutzer einen neuen Chat mit dem Startprompt empfehlen.

## Phase 0 — Vorbereitung

- [x] [Haupt] In `PLAN.md` die Regel „Keine Frameworks, kein Build-Werkzeug, Doppelklick“ durch einen Verweis auf diese Datei ersetzen
- [x] [Sonnet] `fastapi`, `uvicorn`, `pytest` per `pip install --user` installieren; Node-Version prüfen; Ergebnis melden
- [x] [Haupt] `pytest`-Gerüst: `tests/` mit `conftest.py`, das Vault und `data/` nach `tmp_path` kopiert

## Phase 1 — Formatbeschreibung

- [x] [Sonnet] `FORMAT.md` entwerfen aus `tools/*.py` und dem echten Vault: Aufbau Bereichsdatei (YAML-Kopf, feste Abschnitte), Aufgabenzeile (`- [ ]`, `^id`, `#prio`, `@braucht:`, Dauer, eingerückte Beschreibung, Verschachtelung), Querverweise `[[…]]`, Entscheidungen/Anleitungen/Recherche, CSV-Spalten, Medienablage, Matrix bearbeitbar/nur Claude. Abweichungen im Bestand auflisten
- [x] [Haupt] `FORMAT.md` mit dem Nutzer durchgehen, offene Punkte entscheiden
- [x] [Sonnet] Bestand an `FORMAT.md` angleichen (nur Form, kein Inhalt); Liste der Änderungen melden

## Phase 2 — Datenkern `tools/kern/`

- [x] [Sonnet] Lesen: Bereiche, Abschnitte, Aufgabenbaum, Querverweise, Entscheidungen, Teile, Einzelteile, Medien → typisierte Datenklassen. Test: alle echten Dateien lesen ohne Fehler, Ergebnis gleich wie heutiges `tools/tasks.py`/`parts.py`
- [x] [Sonnet] Schreiben Aufgaben: anlegen (ID erzeugen, eindeutig), Status, Titel, Beschreibung, Priorität, löschen (mit Unterpunkten). Test: Rundlauf lesen→schreiben ist bytegleich; Änderung berührt nur die betroffenen Zeilen
- [x] [Sonnet] Schreiben Abschnitte: Bereichsabschnitt ersetzen, nur erlaubte Abschnitte laut Matrix. Test wie oben
- [x] [Sonnet] Schreiben CSV: Teile- und Einzelteilfelder ändern, anlegen, löschen. Test: Spaltenreihenfolge und unberührte Zeilen bleiben gleich
- [x] [Sonnet] Versionsschutz: Hash je Datei; Schreiben mit veraltetem Hash wird abgelehnt
- [x] [Sonnet] Prüfung: `kern.pruefen()` meldet Formatfehler mit Datei und Zeile
- [x] [Haupt] Abnahme: Tests grün, Stichprobe an einer echten Datei

## Phase 3 — Befehle auf den Kern

- [x] [Sonnet] Bestehende Befehle (`task`, `parts`, `bauteile`, `status`, `sync` …) auf den Kern umstellen, Ausgabe bleibt gleich. Vorher/Nachher-Ausgaben vergleichen
- [x] [Sonnet] Neue Befehle: `task add`, `task delete`, `task rename`, `bereich set <Bereich> <Abschnitt>`, `camper check`
- [x] [Haupt] Abnahme mit dem Nutzer: zwei, drei Befehle im Chat ausprobieren

## Phase 4 — FastAPI-Server

- [x] [Sonnet] `tools/server/`: FastAPI-App mit Pydantic-Modellen; `GET /api/daten`, CRUD für Aufgaben, Abschnitte, Teile, Einzelteile; jede Schreibanfrage trägt den Dateihash, Konflikt → 409 mit aktuellem Stand
- [ ] [Sonnet] Live-Aktualisierung: Dateien per mtime überwachen (Standardbibliothek), Änderungen als Server-Sent Events an den Browser
- [ ] [Sonnet] Auto-Commit: Web-Änderungen sammeln, nach einigen Minuten ohne Eingabe ein Commit mit einer Zeile; kein Push
- [ ] [Sonnet] `camper serve` startet die neue App (liefert `web/dist` aus); alte Oberfläche weiter unter `/alt/` erreichbar; `.claude/launch.json` ergänzen
- [ ] [Sonnet] JSON-Schema aus den Pydantic-Modellen exportieren → TypeScript-Typen für `web/`
- [ ] [Haupt] Abnahme: API-Tests grün, Konfliktfall einmal von Hand durchgespielt

## Phase 5 — Web-Grundgerüst

- [ ] [Sonnet] `web/`: Vite + Svelte 5 + TypeScript, Build per `camper web build` (ruft `~/nodejs/npm.cmd`), `node_modules` und `dist` in `.gitignore`
- [ ] [Sonnet] Datenschicht im Browser: ein Store, lädt `/api/daten` (Server) oder `data.json` (statisch), hört auf SSE, Schreibfunktionen mit Hash und Konfliktanzeige, Sperre während laufender Anfrage
- [ ] [Sonnet] Rahmen: Navigation, Routing per Hash, Hell/Dunkel, Toasts, Tastenkürzel wie heute; Lesemodus blendet alle Bearbeitungselemente aus
- [ ] [Haupt] Stil aus `docs/css/` übernehmen, Abnahme mit dem Nutzer

## Phase 6 — Aufgaben und Bereichstexte (ab hier nutzbar)

- [ ] [Sonnet] Aufgabenliste mit Filter, Gruppierung, Suche; Statuswechsler; Anlegen, Umbenennen, Löschen (mit Rückfrage); Detailfenster mit Beschreibung
- [ ] [Sonnet] Bereichsansicht: Kopf, Reiter, bearbeitbare Abschnitte (Textfeld mit Markdown-Vorschau), nur-lesende Abschnitte sichtbar markiert
- [ ] [Sonnet] Browser-Prüfung: Anlegen/Ändern/Löschen landet in der Datei; Claude ändert parallel eine Datei → Oberfläche aktualisiert sich; Konflikt wird angezeigt
- [ ] [Haupt] Feinschliff nach Rückmeldung des Nutzers

## Phase 7 — Teile und Einzelteile

- [ ] [Sonnet] Teileansicht (Liste/Raster, Filter, Kosten), Statuswechsler, Felder bearbeiten, Detailfenster
- [ ] [Sonnet] Zuschnitt/Einzelteile mit Bearbeitung
- [ ] [Haupt] Feinschliff nach Rückmeldung

## Phase 8 — Start, Medien, Suche

- [ ] [Sonnet] Startseite mit Kennzahlen und Entscheidungen
- [ ] [Sonnet] Medien-Galerie und Lupe
- [ ] [Sonnet] Befehlspalette (Strg+K) über alle Inhalte
- [ ] [Sonnet] Browser-Prüfung aller Ansichten gegen das alte Dashboard: fehlt etwas?
- [ ] [Haupt] Feinschliff nach Rückmeldung

## Phase 9 — Veröffentlichen und Ablösen

- [ ] [Sonnet] GitHub Action: Python baut `data.json`, Node baut `web/`, Deploy auf Pages; Lesemodus
- [ ] [Sonnet] Erzeugte Dateien aus Git nehmen (`docs/data.*`, altes Dashboard), `.gitignore` anpassen
- [ ] [Haupt] Handy-Ansicht auf Pages einmal ansehen (nur lesen, nichts optimieren)
- [ ] [Sonnet] Altes Dashboard, `tools/serve.py` und nicht mehr gebrauchte Module entfernen
- [ ] [Haupt] `CLAUDE.md`, Skill `master-dev`, `README.md`, `PLAN.md` auf den neuen Stand bringen

## Protokoll

Eine Zeile je abgeschlossenem Punkt oder getroffener Entscheidung.

- 2026-09-18 Stack festgelegt (siehe oben), Plan angelegt.
- 2026-09-18 Phase 0: PLAN.md verweist auf UMBAU.md; fastapi 0.141.1, uvicorn 0.53.0, pytest 9.1.1 installiert (Skripte nicht im PATH → `python -m`); Node v24.14.0, npm 11.9.0.
- 2026-09-18 Phase 0: `tests/conftest.py` — Fixture `repo` kopiert vault/ und data/ nach tmp_path und biegt alle Pfadkonstanten der `tools`-Module um (auch künftige Unterpakete wie `tools/kern/`). Aufruf: `python -m pytest -q`.
- 2026-09-18 Phase 1: `FORMAT.md` entworfen (Code + Bestand, 8 Abweichungen); mit Nutzer entschieden: `[[…]]` bleibt und wird im Web aufgelöst, fester Aufbau für Anleitungen/Recherche, `system` in `kategorie` aufgehen lassen, zusätzliche Web-Felder — alles in FORMAT.md §10.
- 2026-09-18 Phase 1: Bestand angeglichen — Vault war schon formgerecht; Spalte `system` aus parts.csv entfernt (4 Teile → Dämmung/Karosserie), Code und altes Dashboard nachgezogen, `Karosserie` in die Kategorieliste. Phase 1 fertig.
- 2026-09-18 Phase 2: Kern liest alles (`tools/kern/lesen.py`, `modelle.py`, `format.py`); Grammatik und CSV-Spalten wohnen jetzt in `kern/format.py`, alte Module importieren von dort. Jede Einheit kennt Datei (repo-relativ, `/`) und Zeilenbereich. 9 Tests.
- 2026-09-18 Phase 2: Versionsschutz vom Hauptchat vorgezogen — `kern/datei.py` (Hash je Datei, `Konflikt` bei veraltetem Hash, atomares bytegleiches Schreiben); alle Schreibfunktionen laufen darüber.
- 2026-09-18 Phase 2: `kern/abschnitte.py` — Abschnitt und Kopffeld setzen mit Matrix-Prüfung (`quelle=web|claude`), fehlender Abschnitt an richtiger Stelle. 9 Tests.
- 2026-09-18 Phase 2: `kern/tabellen.py` — `teil_*`/`einzelteil_*` Feld setzen, anlegen, löschen; prüft Listen, Zahlen (Punkt), Datum, Matrix; nur die betroffene Zeile ändert sich. 21 Tests.
- 2026-09-18 Phase 2: `kern/aufgaben.py` — anlegen (ID aus Titel, eindeutig; in Gruppe oder als Unterpunkt), Status, Titel, Beschreibung, Prio, löschen mit Unterpunkten; Marken bleiben an ihrer Stelle. 26 Tests.
- 2026-09-18 Phase 2: `kern/pruefen.py` — `kern.pruefen()` meldet Befunde mit Datei/Zeile (Kopf, Abschnitte, Aufgaben, Abhängigkeitskreise, Querverweise, CSV). Entscheidungsseiten ohne festen Aufbau; Bezüge `fuer_aufgabe`/`entscheidung` und `gekauft_am` nur Warnung. Echter Bestand: 0 Befunde. 25 Tests.
- 2026-09-18 Phase 2 abgenommen: `tools.kern` exportiert `laden`, `aufgaben`, `abschnitte`, `tabellen`, `datei`, `pruefen`, Ausnahmen `Konflikt`/`Unerlaubt`/`Ungueltig`. 94 Tests grün. Stichprobe an echter Elektrik.md: anlegen, Status, Beschreibung, Konflikt, löschen → Datei danach bytegleich. Status-Schlüssel im Kern ohne Umlaut: `offen|laeuft|erledigt|verworfen|blockiert`.
- 2026-09-18 Phase 3: tasks/parts/bauteile/bereiche/status/serve lesen und schreiben über den Kern, doppelte Parser entfernt. 20 Befehlsausgaben + data.json vorher/nachher gleich (einzige Abweichung: Pfade mit `/`). Altes `/api/teil` setzt jetzt die Web-Matrix durch; Fehler dort noch als 500 (sauber ab Phase 4).
- 2026-09-18 Phase 3: neue Befehle `task add|rename|delete`, `bereich set <Bereich> <Abschnitt> --text` / `--kopf feld=wert`, `check` (Exit 1 bei Fehlern). CLAUDE.md und Skill `master` verweisen darauf. 113 Tests.
- 2026-09-18 Phase 3 abgenommen: add/rename/start/delete an Heizung vorgeführt, Bestand danach unverändert; Statusausgabe zeigt „läuft“.
- 2026-09-18 Phase 4: `tools/server/` (app.py, modelle.py, daten.py). `/api/daten` = erzeugt, bereiche, aufgaben, querverweise, entscheidungen, anleitungen, recherche, teile, einzelteile, medien, versionen, kennzahlen, bearbeitbar; `daten_json()` liefert dasselbe für den statischen Build. REST-Routen für Aufgaben, Abschnitte/Kopf, Teile, Einzelteile; 409 mit `stand`, 403/422/404. Einhängepunkt `app.state.nach_schreiben`. Teil-Felder außerhalb der Matrix → 422 (Kern meldet `Ungueltig`). 21 Tests.

## Offene Fragen

- keine

## Startprompt für jeden neuen Chat

```text
/master-dev Wir setzen den Umbau aus `UMBAU.md` um.

Lies zuerst nur `UMBAU.md` — sie ist Plan, Stand und Gedächtnis zugleich.
Dann den nächsten offenen Punkt (oder mehrere unabhängige derselben Phase)
abarbeiten, genau nach dem Abschnitt „Arbeitsweise“ dort:

- Du bist der steuernde Hauptchat und sparst Kontext. Punkte mit [Sonnet]
  gibst du per Agent-Werkzeug mit `model: "sonnet"` an Subagenten, mit
  klarem Auftrag und Abnahmekriterium. Sie melden höchstens zehn Zeilen zurück.
- Du liest keine ganzen Dateien, nur `git diff --stat`, Testausgaben und
  gezielte Ausschnitte.
- Nach jeder Abnahme: in `UMBAU.md` abhaken, Protokollzeile, committen, pushen.
- Inhaltliche Entscheidungen fragst du mich. Nach jeder Phase kurz melden,
  was jetzt geht, und auf mein „weiter“ warten.
- Wird der Chat lang: Stand in `UMBAU.md` sichern und mir einen neuen Chat
  mit genau diesem Prompt empfehlen.

Start.
```
