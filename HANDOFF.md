# Handoff — Stand 2026-09-19

Der vorige Handoff kam aus einer Cloud-Sitzung ohne PyPI und npm. Der Branch
`claude/master-dev-hzcprp` ist seither in `main` gemergt; dieser Stand baut
darauf auf, diesmal mit beidem.

## Lage

Alles einmal durchgelaufen, alles grün:

```
pip install --user -r requirements.txt
PYTHONIOENCODING=utf-8 python -m pytest -q     # 248 Tests
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

5. **Einkaufsansicht zu `buy next`** — existiert nur als CLI-Text. Der letzte
   Befehl ohne Ansicht.
6. **`data/bauteile.csv` ist leer.** Der Reiter Material und die
   Zuschnitt-Ansicht wurden in dieser Sitzung mit vier Testzeilen geprüft
   (Gruppierung, m²/lfm, Bereichsfilter, Sprung ins Detail — alles richtig) und
   die Zeilen danach wieder entfernt. Sobald echte Zuschnitte drin sind, lohnt
   ein zweiter Blick.

**Paket C — UI entschlacken** (analysiert, noch nicht angefasst)

7. `Start.svelte` hat sieben dauerhaft sichtbare Blöcke, alle read-only, und
   dupliziert Kosten- und Kategoriezahlen aus Teile und Bereiche. Kürzen auf
   Kennzahlen und „Jetzt dran", letzteres mit Direkt-Aktion zum Abhaken.
8. `BereichDetail.svelte:122-132` zeigt eine tote Mini-Teileliste statt der
   echten, bedienbaren Komponente.
9. Die Filterleiste (Suche + Auswahl + Tabs) ist vierfach fast identisch
   kopiert: `AufgabenListe`, `TeileListe`, `EinzelteilListe`, `MedienAnsicht`.
   Ein gemeinsamer Baustein in `lib/ui/` gehört her.
10. `AufgabeZeile.svelte:50-76` bietet Kontrollkästchen und Status-Auswahl für
    denselben Zustand — zwei Wege für eine Sache.
11. Teile: keine Sortierung (Preis, Status-Alter), keine Mehrfachauswahl für
    Statuswechsel bei Bestellläufen.
12. Vier getrennte Suchfelder statt einer Suche über alle Ansichten; kein
    Rückgängig nach versehentlichem Statuswechsel, nur ein Toast.

**Aus PLAN.md Stufe 3 noch offen**

13. Strombilanz (Verbraucher × Laufzeit → Ah/Tag gegen Batteriekapazität).
    Steht als Aufgabe in `vault/Bereiche/Elektrik.md`, es gibt keinen Befehl.
14. Blocker-Übersicht über `@braucht:` als Ablaufplan statt nur Hinweistext.

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
