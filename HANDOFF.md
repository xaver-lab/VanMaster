# Handoff — Stand 2026-09-19

Übergabe aus einer Cloud-Sitzung ohne PyPI- und npm-Zugang an eine Sitzung,
in der `pytest` und `npm` laufen. Branch: `claude/master-dev-hzcprp`,
vier Commits über `main`.

## Zuerst tun

```bash
pip install --user -r requirements.txt
PYTHONIOENCODING=utf-8 python -m pytest -q
cd web && npm ci && npm run check && npm run build
```

Die vier neuen Testdateien sind **nie gelaufen** — sie wurden geschrieben,
ohne dass ein `pytest` zur Verfügung stand:

- `tests/test_budget.py`
- `tests/test_verlauf.py`
- `tests/test_gewicht.py`
- `tests/test_material.py`

Dazu angepasst: `tests/test_kern_pruefen.py` (neue Spalte `gewicht_kg`).

Hinweis: Der Workflow `.github/workflows/pruefen.yml` prüft genau das bei
jedem Push auf einen Arbeitszweig. Vor dem Nacharbeiten also erst dort
nachsehen, was rot ist — das spart das Raten.

## Was in dieser Sitzung entstanden ist

**Aufgeräumt** (`cc5c234`)
- `appjs_full.diff.txt` und `_input/screen_b_dashboard.html` gelöscht, beides
  Reste des alten, in Phase 9 entfernten Dashboards.
- README: `camper.py system elektrik` gab es nicht, jetzt `camper.py bereich Elektrik`.
- `.claude/settings.json` sperrt `web/dist/**` und `web/src/lib/api-schema.json`
  statt der gelöschten `docs/data.*`.

**Prüf-Workflow** (`64fb96c`) — `.github/workflows/pruefen.yml`: läuft auf jedem
Zweig außer `main`, ohne zu veröffentlichen. Job `python`: `camper check` und
`pytest`. Job `web`: `npm ci`, `npm run check`, `npm run build`.

**Vier neue Auswertungen** (`cd3ed12`)
- `camper gewicht` — Zuladungsbilanz. Liest `leergewicht_kg` und
  `zul_gesamtgewicht_kg` aus dem Kopf von `vault/Camper.md` (FORMAT.md §13).
- `camper material` — Materialliste fürs Baumarkt, nach Material und Dicke,
  m² bei Platten, lfm bei Leisten. `--bereich`, `--json`.
- `camper budget` — Ziel gegen bezahlt, geplant, Prognose, je Kategorie.
  Zielbudget im Kopf von `vault/Camper.md` (FORMAT.md §11), optional
  `budget_<kategorie>`.
- `camper verlauf` — schreibt einen Datensatz je Tag nach `data/verlauf.csv`
  (FORMAT.md §12), mehrfacher Aufruf am selben Tag ersetzt die Zeile.
- Einzelteile haben ein optionales Feld `gewicht_kg`. Ist es leer und Art und
  Material passen auf eine Holzdichte aus `common.MATERIAL_DICHTE`, rechnet
  `bauteile.gewicht()` aus den Maßen; sonst gilt das Gewicht als fehlend.

**Dashboard** (`4a49b1f`) — die fünf offenen Fragen aus UMBAU.md abgearbeitet:
- Palette zeigt lose Buchstabentreffer nur noch, wenn es sonst gar keine
  Treffer gäbe.
- `Dialog` hat eine Eigenschaft `kopflos`; die Palette nutzt sie, das
  Eingabefeld trägt das `aria-label`.
- Einzelteile haben eine Detail-Route `#/zuschnitt/<id>`.
- Medien-Treffer öffnen die Lupe direkt über `#/medien/<id>`.
- 3D-Modell-Kacheln zeigen Dateiname und Vault-Pfad mit Knopf „Pfad kopieren".

## Im Browser gegenprüfen

In dieser Sitzung lief kein Browser. Drei Stellen sind bewusst als
verdächtig markiert:

1. **Medien-Route mit Sonderzeichen.** Der Dateiname wird doppelt kodiert,
   weil der Router den ganzen Hash dekodiert, bevor er ihn zerlegt. Ein
   Medium mit Leerzeichen oder Umlaut im Dateinamen anklicken und prüfen, ob
   die Lupe aufgeht und die Adresszeile stimmt.
2. **Dialog ohne Kopf.** Escape muss schließen, der Dialog muss trotz
   fehlendem sichtbaren Titel benannt sein.
3. **Zuschnitt-Detailroute im eingebetteten Fall.** Die Liste navigiert nur,
   wenn sie nicht im Bereich-Detail eingebettet ist — beide Wege durchklicken.

## Offen, nach Nutzen sortiert

**Entscheidungen des Nutzers**
1. `leergewicht_kg` aus dem Fahrzeugschein in den Kopf von `vault/Camper.md`.
   Ohne sie gibt `camper gewicht` keine Zuladungsbilanz aus. Eingetragen sind
   bereits `budget: 6000` und `zul_gesamtgewicht_kg: 3500` (letzteres vom
   Nutzer mit Fragezeichen genannt — gegen den Schein prüfen).
2. `common.MATERIAL_DICHTE` enthält Literatur-Richtwerte für Holz. Sobald
   konkrete Platten feststehen, echte Werte eintragen.
3. Gewichte in `parts.csv` nachtragen: 66 von 67 Teilen haben keins, die
   Bilanz ist damit wertlos. Lohnt vor allem bei Batterie, Wassertank,
   Möbelholz, Dämmung.

**Nächste Bauschritte**
4. **Dashboard-Ansichten für `gewicht`, `budget` und `material`.** Die
   Projektregel „jede Funktion braucht Befehl und Ansicht" ist derzeit
   verletzt. Dazu gehören Server-Modelle (`tools/server/modelle.py`,
   `daten.py`) und danach `python -m tools.server.schema` für die TS-Typen.
5. **Einkaufsansicht zu `buy next`** — existiert nur als CLI-Text.
6. **`groesse` bei Medien.** Für die 3D-Kachel fehlt die Dateigröße:
   `tools/kern/modelle.py` (Medium) und `tools/server/modelle.py` (MediumAntwort)
   brauchen ein `groesse: int`, befüllt in `tools/kern/lesen.py:_medium()` über
   `datei.stat().st_size`.
7. **`data/bauteile.csv` ist leer.** Die Zuschnitt-Ansicht und `camper material`
   wurden nur im Leerzustand geprüft. Sobald echte Zuschnitte drin sind, beides
   nochmal ansehen.

**Paket C — UI entschlacken** (analysiert, noch nicht angefasst)
8. `Start.svelte` hat sieben dauerhaft sichtbare Blöcke, alle read-only, und
   dupliziert Kosten- und Kategoriezahlen aus Teile und Bereiche. Kürzen auf
   Kennzahlen und „Jetzt dran", letzteres mit Direkt-Aktion zum Abhaken.
9. `BereichDetail.svelte:122-132` zeigt eine tote Mini-Teileliste statt der
   echten, bedienbaren Komponente.
10. Die Filterleiste (Suche + Auswahl + Tabs) ist vierfach fast identisch
    kopiert: `AufgabenListe`, `TeileListe`, `EinzelteilListe`, `MedienAnsicht`.
    Ein gemeinsamer Baustein in `lib/ui/` gehört her.
11. `AufgabeZeile.svelte:50-76` bietet Kontrollkästchen und Status-Auswahl für
    denselben Zustand — zwei Wege für eine Sache.
12. Teile: keine Sortierung (Preis, Status-Alter), keine Mehrfachauswahl für
    Statuswechsel bei Bestellläufen.
13. Vier getrennte Suchfelder statt einer Suche über alle Ansichten; kein
    Rückgängig nach versehentlichem Statuswechsel, nur ein Toast.

**Aus PLAN.md Stufe 3 noch offen**
14. Strombilanz (Verbraucher × Laufzeit → Ah/Tag gegen Batteriekapazität).
    Steht als Aufgabe in `vault/Bereiche/Elektrik.md`, es gibt keinen Befehl.
15. Blocker-Übersicht über `@braucht:` als Ablaufplan statt nur Hinweistext.

## Umgebungsnotiz

Die Sitzung, aus der dieser Handoff stammt, hatte weder PyPI noch npm
(`pip install` bricht ab, `npm ci` bekommt 403 vom Proxy). Geprüft wurde
deshalb über die echten Befehlsaufrufe und über GitHub Actions. Wer das hier
liest und beides hat: einmal alles durchlaufen lassen, bevor weitergebaut wird.
