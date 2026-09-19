# Handoff — Stand 2026-09-19

Der vorige Handoff kam aus einer Cloud-Sitzung ohne PyPI und npm. Der Branch
`claude/master-dev-hzcprp` ist seither in `main` gemergt; dieser Stand baut
darauf auf, diesmal mit beidem.

## Lage

Alles einmal durchgelaufen, alles grün:

```
pip install --user -r requirements.txt
PYTHONIOENCODING=utf-8 python -m pytest -q     # 256 Tests
python camper.py check                          # keine Abweichungen
python camper.py geheim                         # nichts gefunden
cd web && npm ci && npm run check && npm run build   # 0 Fehler, 0 Warnungen
```

Damit ist die Umgebungsnotiz des letzten Handoffs erledigt. Die vier
Testdateien, die damals ohne `pytest` geschrieben wurden, laufen sauber.

## Was in dieser Sitzung entstanden ist

**Ansicht `#/bilanz`** — `camper budget`, `camper gewicht` und
`camper material` hatten als einzige Befehle keine Dashboard-Ansicht; die
Projektregel „jede Funktion braucht Befehl und Ansicht" war verletzt. Jetzt
eine Ansicht mit drei Reitern statt drei Einträgen in der Schiene: alle drei
sind reine Auswertungen über denselben Bestand. Der aktive Reiter steht in der
Adresse (`#/bilanz/gewicht`), Links bleiben teilbar, Zifferntaste 7.

- `/api/daten` liefert `budget`, `gewicht` und `material`. Gerechnet wird
  weiter in `tools/`; die Ansicht zeigt nur an. `material` trägt nur die
  Einzelteil-IDs — die Sätze stehen schon unter `einzelteile`.
- Medien haben zusätzlich `groesse` (Byte, aus `datei.stat().st_size`).
- Zwei neue Tests in `tests/test_server.py` halten API und Befehle
  deckungsgleich, damit die Zahlen nicht auseinanderlaufen.

**Die drei verdächtigen Stellen aus dem letzten Handoff** sind im Browser
durchgeprüft (Playwright/Chromium gegen Port 8767). Zwei waren echte Fehler:

1. **Doppelte Kodierung.** `router.ausHash()` dekodierte den ganzen Hash, bevor
   er ihn zerlegte, während `gehe()` jedes Stück einzeln kodiert. Die Palette
   glich das mit einem zusätzlichen `encodeURIComponent` aus, die Medien-Ansicht
   mit einem zweiten `decodeURIComponent` — zwei Fehler, die sich gegenseitig
   trugen, solange kein Dateiname ein `/` oder `%` enthielt. Jetzt wird
   stückweise dekodiert, beide Ausgleiche sind raus. Geprüft mit einem Medium
   namens `Test Prüfung & Maß 100%.png`: öffnet sich, übersteht das Neuladen,
   Bild lädt.
2. **Lupe ließ sich nicht schließen**, wenn sie über einen Direktlink geöffnet
   wurde — weder mit Escape noch über den Knopf. Der Route-Effekt setzte den
   Index sofort wieder, den das Schließen genullt hatte. Er reagiert jetzt nur
   auf echte Adressänderungen.
3. **Dialog ohne Kopf** war in Ordnung: Escape schließt, der Dialog ist über
   `aria-label` benannt. Auch die Zuschnitt-Detailroute stimmt über beide Wege.

**Push-Wache** (`.claude/settings.json`) lief als
`python .claude/hooks/push_wache.py` relativ zum Arbeitsverzeichnis der Shell.
Nach einem `cd web` fand sie sich selbst nicht mehr und blockierte jeden
weiteren Bash-Aufruf. Jetzt über `$CLAUDE_PROJECT_DIR`.

**Ansicht `#/einkauf`** — damit hat auch `camper buy next` seine Ansicht, und
kein Befehl steht mehr ohne da. Nach Händler gebündelt, mit Links in den Shop.
Der eigentliche Gewinn ist die Mehrfachauswahl: ganzen Korb anhaken, einmal
bestätigen, alle Teile wandern von „Entschieden“ auf „Bestellt“. Dafür wurde
`parts.buy_next()` in `buy_daten()` (Daten) und `buy_next()` (Text) getrennt —
Befehl, `--json` und Ansicht zeigen jetzt zwingend dieselbe Reihenfolge, sieben
Tests in `tests/test_einkauf.py` halten das fest. Im Browser durchgespielt bis
zum geschriebenen CSV.

**Paket C angefangen:**

- `BereichDetail` zeigte im Reiter „Teile“ eine tote Liste ohne Bedienung.
  Jetzt steht dort die echte `TeileListe`, wie bei Aufgaben und Zuschnitt
  schon länger. Sie hat dafür eine Eigenschaft `kategorie` bekommen: feste
  Kategorie, keine Kategorie-Auswahl, Neuanlagen landen im Bereich, und das
  Detail bleibt im Bereich statt die Adresse auf `#/teile` umzubiegen.
- `AufgabeZeile` hatte Kontrollkästchen **und** volle Status-Auswahl für
  denselben Zustand. Jetzt ein Weg je Sache: das Kästchen schaltet
  offen↔erledigt, die Statusmarke führt mit einem Klick ins Detail, wo die
  übrigen Status ohnehin schon standen. Nebenbei fiel eine unscoped
  `:global(.status-wahl)`-Regel weg, die aus der Aufgabenzeile in alle
  anderen Ansichten leckte.
- Die Filterleiste stand vierfach fast byte-gleich da. Jetzt ein Baustein
  `lib/ui/Filterleiste.svelte` (Reiter links, Werkzeuge rechts; ohne Reiter
  alles in einer Reihe), benutzt von `AufgabenListe`, `TeileListe`,
  `EinzelteilListe` und `MedienAnsicht`. Schmale Auswahlfelder tragen jetzt
  alle `class="filter-wahl"` statt vier verschiedener Namen. Auf `#/muster`
  in beiden Ausführungen zu sehen, in `web/DESIGN.md` beschrieben.
- Dabei fielen fünf unscoped `:global(.…-wahl)`-Regeln auf, die aus einer
  Ansicht in alle anderen leckten (`gruppen-`, `kategorie-`, `bereich-`,
  `material-`, `sortier-`, `status-wahl`). Vier sind im Baustein
  aufgegangen, die übrigen zwei an ihren Container gebunden.
- `Start.svelte` hatte sieben dauerhaft sichtbare Blöcke, alle nur lesend.
  Drei davon — Budget-Karte, Teilestufen, Kosten je Kategorie — wiederholten
  nur, was `#/bilanz` und `#/teile` vollständig und bedienbar zeigen; mit der
  neuen Bilanz-Ansicht war das schlicht dieselbe Tabelle zweimal. Geblieben
  ist, was es sonst nirgends gibt: Gesamtstand, Bauabschnitte in ihrer
  Reihenfolge, „Jetzt dran" und offene Entscheidungen (die haben keine eigene
  Ansicht). Die vier Eckdaten im Kopf sind jetzt Wege nach `#/bilanz`,
  `#/einkauf` und `#/bilanz/gewicht`. Vor allem: „Jetzt dran" hat
  Kontrollkästchen — abhaken, ohne die Seite zu wechseln. Im Browser geprüft,
  der Gesamtstand springt sofort mit. Die Datei ist von 582 auf 527 Zeilen
  geschrumpft, der Rest passt auf einen Bildschirm.
- Teile lassen sich jetzt sortieren: Titel, Preis (beide Richtungen),
  Priorität, Status, zuletzt gekauft. Die Wahl wird gemerkt. Ein
  „Status-Alter" war nicht machbar — die CSV führt keinen Zeitpunkt des
  letzten Statuswechsels, nur `gekauft_am`. Teile ohne Preis gelten als
  unbekannt, nicht als billig, und stehen bei „günstigste zuerst" hinten.
**Ablaufplan** (`camper ablauf`, im Dashboard der Umschalter „Ablauf" in der
Aufgabenansicht) — die `@braucht:`-Bezüge waren bisher nur Hinweistext unter
`camper next`. Jetzt liegen die offenen Aufgaben in Stufen: Stufe 1 ist sofort
möglich, Stufe 2 wird frei, sobald Stufe 1 steht. Zwei Dinge fallen dabei ab,
die es sonst nirgends gab:

- **Schlüsselaufgaben** — wie viele Aufgaben an einer hängen, über die ganze
  Kette. Beim jetzigen Stand: „Position bestimmen" hält 6 auf, „Holzrahmen
  bauen" und „Strombilanz rechnen" je 5. Da lohnt Aufwand am meisten.
- **Ringe** — `a @braucht:b` und `b @braucht:a`. Die lösen sich nie auf und
  blieben bisher unbemerkt; jetzt stehen sie als Warnung oben. Derzeit keiner.

Der Plan rechnet immer über alle Bereiche, auch wenn nur einer angezeigt wird —
sonst verschöben sich die Stufen, obwohl die Abhängigkeit bleibt. 10 Tests in
`tests/test_ablauf.py`, dazu einer, der API und Befehl deckungsgleich hält.

- **Rückgängig nach einem Statuswechsel.** Ein Statuswechsel ist ein Klick
  und schnell danebengegriffen. Der Toast nennt jetzt die Änderung
  („Dampfbremse setzen: offen → erledigt") und hat einen Knopf, der sie
  zurücknimmt; er steht 9 statt 3,5 Sekunden. Das sitzt zentral im Store
  (`daten.svelte.ts`), nicht in den Ansichten — wer `status` oder
  `prioritaet` schreibt, bekommt es ohne Zutun, bei Aufgaben, Teilen und
  Einzelteilen gleichermaßen. Freitextfelder bleiben außen vor, sonst käme
  nach jedem Tippen ein Toast. Das Zurücknehmen erzeugt keinen zweiten
  Toast, und ein Bestelllauf über mehrere Teile bündelt zu einem
  (`store.ohneRueckgaengig`).
- `scroll-padding-top` auf `html`: die Kopfzeile klebt oben, ohne das landete
  jeder programmatische Sprung (Tastaturfokus, Anker) darunter.

## Offen, nach Nutzen sortiert

**Entscheidungen des Nutzers** (unverändert, nur der Nutzer kann sie treffen)

1. `leergewicht_kg` aus dem Fahrzeugschein in den Kopf von `vault/Camper.md`.
   Ohne sie zeigt der Reiter Gewicht keine Zuladungsbilanz, sondern nur den
   Hinweis, welches Feld fehlt. `zul_gesamtgewicht_kg: 3500` steht drin, wurde
   aber vom Nutzer mit Fragezeichen genannt — gegen den Schein prüfen.
2. Gewichte in `parts.csv` nachtragen: 66 von 67 Teilen haben keins. Der Reiter
   Gewicht sagt das offen an, aber die Bilanz bleibt bis dahin wertlos. Lohnt
   vor allem bei Batterie, Wassertank, Möbelholz, Dämmung.
3. `common.MATERIAL_DICHTE` enthält Literatur-Richtwerte für Holz. Sobald
   konkrete Platten feststehen, echte Werte eintragen.
4. Optionale Kategorie-Budgets (`budget_elektrik: 1800` im Kopf von
   `vault/Camper.md`). Erst damit zeigt die Budget-Tabelle Auslastungsbalken
   statt einer leeren Spalte.

**Nächste Bauschritte**

5. **`data/bauteile.csv` ist leer.** Der Reiter Material und die
   Zuschnitt-Ansicht wurden in dieser Sitzung mit vier Testzeilen geprüft
   (Gruppierung, m²/lfm, Bereichsfilter, Sprung ins Detail — alles richtig) und
   die Zeilen danach wieder entfernt. Sobald echte Zuschnitte drin sind, lohnt
   ein zweiter Blick.

**Paket C — UI entschlacken** (durch bis auf einen Rest)

6. Vier getrennte Suchfelder statt einer Suche über alle Ansichten. Die
   Befehlspalette (Strg+K) deckt das inzwischen weitgehend ab — lohnt vor
   einer Umstellung erst zu prüfen, ob es überhaupt noch stört.

**Aus PLAN.md Stufe 3 noch offen**

7. Strombilanz (Verbraucher × Laufzeit → Ah/Tag gegen Batteriekapazität).
   Steht als Aufgabe in `vault/Bereiche/Elektrik.md`, es gibt keinen Befehl.
   Der Ablaufplan weist sie jetzt als Schlüsselaufgabe aus: fünf Aufgaben
   hängen daran. Sie braucht ein neues Datenformat (Verbraucherliste mit
   Watt und Laufzeit) — das ist eine Format-Entscheidung, keine Fleißarbeit.

## Zwei Lehren, die weiter gelten

1. Die Fixture `repo` biegt Pfadkonstanten **nur in den `tools`-Modulen** um.
   Wer in einer Testdatei `from tools.common import X` schreibt, hält den
   echten Repo-Pfad. Richtig ist `from tools import common` und dann
   `common.X`.
2. Die Fixture kopiert den **echten** Bestand. Kein Test darf voraussetzen,
   dass ein Kopffeld fehlt oder eine Datei noch nicht da ist. Die Tests stellen
   ihren Ausgangszustand selbst her.

Dazu neu: ein Ausgleich an zwei Stellen ist kein Fix. Die doppelte Kodierung
oben lief monatelang, weil Kodieren und Dekodieren beide zweimal passierten.
Wer so etwas findet, nimmt beide Hälften raus, nicht eine.
