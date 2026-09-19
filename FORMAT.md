# FORMAT.md — Format der Wahrheit

Beschreibt, wie `vault/` und `data/` heute tatsächlich gelesen und
geschrieben werden (Quelle: `tools/common.py`, `tools/tasks.py`,
`tools/bereiche.py`, `tools/parts.py`, `tools/bauteile.py`, `tools/media.py`,
`tools/status.py`, `tools/build.py`, sowie der reale Bestand in `vault/` und
`data/`). Jede Aussage ist durch Code oder Bestand gedeckt — Stellen ohne
realen Beleg sind als solche markiert. Grundlage für `tools/kern/` (Phase 2
in `UMBAU.md`).

`data/generated/`, `vault/Stückliste/` und `docs/data.json`/`docs/data.js`
sind **erzeugt** — sie beschreiben kein Format, sie sind Ausgabe. Nie von
Hand ändern, hier nur der Vollständigkeit halber erwähnt.

---

## 1. Ablage

- Kodierung: UTF-8 ohne BOM. Geschrieben wird ausschließlich über
  `common.write_text()`/`write_json()`, die `encoding="utf-8"` fest vorgeben.
- Zeilenenden: LF (`\n`). `write_text()` erzwingt `newline="\n"` und hängt
  bei Bedarf eine abschließende Zeile an. Geprüft an
  `vault/Bereiche/Elektrik.md` und `data/parts.csv` — beide reine LF-Dateien.
- Dateinamen tragen Umlaute direkt (kein Slug): `vault/Bereiche/Möbel.md`,
  `vault/Bereiche/Dämmung.md`, `vault/Bereiche/Küche.md`. `slug()`
  (`tools/common.py:68`) wird nur für erzeugte ID-Werte (Teile-, Bauteil-,
  Medien-Dateinamen) benutzt, nie für Bereichs-Dateinamen selbst.
- Ordner:
  - `vault/Bereiche/*.md` — ein Bereich je Datei.
  - `vault/Entscheidungen/*.md`, `vault/Anleitungen/*.md`,
    `vault/Recherche/*.md` — eine Seite je Datei, Dateiname = Titel.
  - `vault/Medien/<Bereich>/<Datum>-<Slug>.<ext>` — Bilder/Dokumente.
  - `vault/Modelle/<Bereich>/<Datum>-<Slug>.<ext>` — 3D-Dateien.
  - `data/parts.csv`, `data/bauteile.csv` — je eine Tabelle.

---

## 2. Bereichsdatei

Quelle: `tools/bereiche.py` (Docstring + `load()`), `tools/common.py`
(`split_frontmatter`, `abschnitte`).

### YAML-Kopf

```yaml
---
bereich: Möbel
kurz: Bett, Küchenblock, Hängeschränke, Sitzbank, Tisch, Toilette, Stauraum
status: in-arbeit
phase: 6
---
```

| Feld | Pflicht | Typ | Bedeutung |
|---|---|---|---|
| `bereich` | optional* | Text | Name des Bereichs. Fehlt es, tritt der Dateiname (ohne `.md`) an seine Stelle (`bereiche.py:72`: `meta.get("bereich") or datei.stem`). In allen 7 realen Dateien identisch zum Dateinamen. |
| `kurz` | optional | Text | Kurzbeschreibung für Kopfzeilen/Dashboard. Fehlt in keiner realen Datei. |
| `status` | optional | Text | Erwartete Werte `geplant`/`in-arbeit`/`fertig` (`common.py:44`, `BEREICH_STATUS`), **nicht geprüft** — jeder Wert wird übernommen, unbekannte sortieren wie `geplant` (`bereiche.py:92`, `STATUS_RANG.get(..., 1)`). Fehlt das Feld, wird `"geplant"` angenommen (`bereiche.py:74`). |
| `phase` | optional | Ganzzahl | Nummer des Bauabschnitts, 1 = zuerst. Alles Nicht-Ganzzahlige zählt als „nicht gesetzt" (`bereiche.py:97-102`, `phase()`) und sortiert bei `--sortierung phase` ganz hinten (`OHNE_PHASE = 999`). |

*„Pflicht" im Sinn von: ohne das Feld funktioniert das System noch (Fallback
Dateiname), fachlich soll es aber immer gesetzt sein.

Der eigentliche YAML-Parser (`split_frontmatter`, `common.py:98-121`) ist
kein vollständiger YAML-Parser, sondern liest nur flache `schlüssel: wert`-
Zeilen und einfache `- wert`-Listen unter dem zuletzt gesehenen Schlüssel.
Verschachtelte Strukturen, mehrzeilige Werte oder Inline-Kommentare hinter
einem Wert werden nicht unterstützt — kein realer Kopf verletzt das, aber es
ist die tatsächliche Grammatik, nicht „beliebiges YAML".

### Feste Abschnitte

`BEREICH_ABSCHNITTE` (`common.py:41-43`), in dieser Reihenfolge:

```
# <Bereich>

## Beschreibung
## Stand
## Auslegung
## Notizen
## Links
## Aufgaben
```

`abschnitte()` (`common.py:124-141`) zerlegt den Rumpf an `## `-Zeilen
(nicht `### `); Text vor der ersten `## `-Zeile (der `# <Bereich>`-Titel)
landet unter dem Schlüssel `""` und wird ignoriert. `### `-Unterüberschriften
bleiben Teil ihres Abschnitts (z. B. `### Aufbau in Schichten` unter
`## Stand` in `Dämmung.md:19`).

Platzhaltertext der Form `_(...)_ ` zählt als leer (`bereiche.py:41-47`,
`LEER`-Regex) — z. B. `_(noch keine)_` unter `## Links` in `Elektrik.md:42`.

`## Aufgaben` wird **nicht** von `bereiche.py`/`abschnitte()` gelesen,
sondern eigenständig von `tools/tasks.py` zeilenweise verarbeitet (siehe
Abschnitt 3) — eine Checkbox in `## Notizen` ist deshalb keine Aufgabe,
sondern nur Text.

---

## 3. Aufgabenzeile

Quelle: `tools/tasks.py` (Regex `ZEILE`, `BESCHREIBUNG`, `ANKER`, `PRIO`,
`MARKE`, Funktion `load()`).

```
- [ ] Batteriehalterung bauen ^batteriehalterung #hoch @braucht:batteriebank-entscheiden
  > Wie: Winkel aus 3mm Alu, an die Querträger geschraubt.
  - [x] Maße nehmen
```

### Grammatik

- **Einzug**: Leerzeichen oder Tabs vor `- [`. `ebene()` (`tasks.py:43-44`)
  zählt zwei Leerzeichen (Tab wird als zwei Leerzeichen behandelt) = eine
  Verschachtelungsstufe. **Im realen Bestand kommt keine einzige
  verschachtelte Aufgabe vor** (geprüft mit Suche über alle 7
  Bereichsdateien) — die Mechanik ist im Parser vorhanden, aber unbelegt.
- **Kästchen** `[x]`: eines der Zeichen aus `BOX` (`tasks.py:28-29`):
  - ` ` → offen
  - `/` → läuft
  - `x` oder `X` → erledigt
  - `-` → verworfen
  - `!` → blockiert
- **Titel + Marken**: der Rest der Zeile wird nacheinander von drei
  unabhängigen Regex-Suchen bereinigt (Reihenfolge im Code: Anker, dann
  Priorität, dann `@`-Marken) — im Text selbst ist die Reihenfolge egal,
  alle drei werden über den ganzen Rest gesucht, nicht positionsgebunden.
  Was übrig bleibt, ist der Titel.
  - `^kennung` — Anker/ID (`ANKER`, `tasks.py:38`: `[A-Za-z0-9\-_]+`).
    Fehlt er, wird die ID aus `slug(bereich-titel)` erzeugt (`tasks.py:101`)
    — **im realen Bestand hat jede einzige Aufgabe einen expliziten
    Anker**, es gibt keinen Beleg für den Auto-Fallback.
  - `#prio` — eine von `kritisch|hoch|mittel|nice` (`PRIO`, `tasks.py:39`,
    case-insensitiv). Real genutzt: nur `#kritisch` und `#hoch` (12
    Treffer in 7 Dateien); `#mittel`/`#nice` kommen im Bestand nicht vor.
  - `@braucht:id` oder `@braucht:id1,id2` — Abhängigkeit, kommagetrennt
    (`MARKE`, `tasks.py:40`, `92-96`). 22 reale Vorkommen, immer eine
    einzelne ID, keine Kommalisten im Bestand.
  - `@dauer:wert` — Freitext-Dauer. **Kein einziges Vorkommen im
    Bestand.**
- **Beschreibung**: Blockquote-Zeilen (`>` mit optionalem Leerzeichen)
  direkt unter der Aufgabenzeile, gleicher oder tieferer Einzug
  (`BESCHREIBUNG`, `tasks.py:37`, `73-78`). Mehrere Zeilen werden mit `\n`
  aneinandergehängt. **Kein einziges Vorkommen im Bestand.**
- **Gruppen** (`### Name`): jede Zeile, die mit `#` beginnt (aber nicht auf
  `## ` passt — das wäre ein neuer Bereichsabschnitt), setzt bis zur
  nächsten Gruppe/zum nächsten Abschnitt eine `gruppe` an allen folgenden
  Aufgaben (`tasks.py:67-70`). Real belegt, z. B. `### Auslegung` /
  `### Einbau` in `Elektrik.md:46,51`.

---

## 4. Querverweise `[[…]]`

Obsidian-Syntax `[[Ziel]]` bzw. `[[Ziel|Anzeigetext]]` kommt im Bestand an
zwei Stellen vor:

1. **Erzeugt**: `tools/media.py:97-98` (Medien-Index),
   `tools/parts.py:214,223` (Stücklisten-Seiten) — beides generierte
   Dateien unter `vault/Medien/Medien.md` bzw. `vault/Stückliste/`.
2. **Von Hand geschrieben**, als reiner Fließtext-Querverweis, z. B.
   `Möbel.md:51` „…deckt sich mit der Notiz […] unter [[Küche]]",
   `Karosserie.md:27` „(siehe [[Küche]] zur Gangbreite)",
   `Kühlschrank Modell.md:60` „Bereich: [[Küche]]".

**Kein Werkzeug unter `tools/*.py` liest oder löst `[[…]]` auf** — weder als
Link noch als Graph-Kante. Es ist reine Obsidian-Anzeigehilfe beim Öffnen im
Obsidian-Vault; für `camper`-Befehle und das Dashboard ist es toter Text.
Offene Frage siehe Abschnitt 10.

---

## 5. Entscheidungen, Anleitungen, Recherche

Quelle: `tools/build.py:15-30` (`seiten()`) liest generisch aus allen drei
Ordnern: Kopf (`status`, `bereich` **oder** `system` als Fallback), Rest der
Datei als unstrukturierter Text. `tools/status.py:11-19`
(`offene_entscheidungen`) wertet zusätzlich `status` aus: alles außer dem
Wert `entschieden` (case-insensitiv) gilt als offen.

Nur `vault/Entscheidungen/` enthält reale Dateien (2 Stück); `Anleitungen/`
und `Recherche/` sind **leer** — für sie gibt es keinen belegten
Aufbau, nur die generische Kopf-Auswertung.

Realer Kopf + Aufbau (Entscheidungen):

```yaml
---
status: offen
bereich: Küche
---

# Kühlschrank Modell

## Frage
## Vergleich
## Notizen vom Nutzer
## Wahl
## Verknüpft
```

`status` und `bereich` sind die einzigen vom Code ausgewerteten Felder.
`## Frage` / `## Vergleich` bzw. `## Notizen vom Nutzer` / `## Wahl` /
`## Verknüpft` sind **Konvention aus den zwei realen Dateien**, kein vom
Code erzwungener Aufbau — `seiten()` liefert den Rumpf als einen einzigen
Text-Blob (`build.py:27`, Feld `text`).

Verknüpfung zu einem Teil läuft über das freie Feld `entscheidung` in
`data/parts.csv`, das den Dateinamen (Titel) der Entscheidungsseite als
Text trägt — kein Anker, keine ID (`parts.csv` Zeile mit
`id=kompressorkuehlschrank`, `entscheidung=Kühlschrank Modell`).

---

## 6. CSV

### `data/parts.csv` — was gekauft wird

`FIELDS` in `tools/parts.py:13-18`, in dieser Spaltenreihenfolge:

| Spalte | Bedeutung | Typ | Erlaubte Werte |
|---|---|---|---|
| `id` | Kennung, aus Titel erzeugt (`slug`, ggf. `-2`, `-3`…) | Text | eindeutig, wird nie geprüft/erzwungen validiert |
| `titel` | Name des Teils | Text | frei |
| `beschreibung` | Kurzbeschreibung | Text | frei |
| `kategorie` | Einkaufsgruppe | Text | `PART_KATEGORIEN` (`common.py:35-38`): Dämmung, Elektrik, Wasser, Heizung, Möbel, Küche, Stauraum, Werkzeug, Verbrauchsmaterial — **im Code nicht geprüft** (`parts.py:144-158`, `set_field` validiert nur `status`/`prioritaet`), im Bestand aber ausschließlich diese 8 Werte verwendet |
| `system` | **entfällt** (Entscheidung 7) — heute noch vorhanden, wird mit `kategorie` zusammengelegt | — | — |
| `menge` | Menge | Zahl (Text, Komma oder Punkt) | `num()` akzeptiert beides, leer = 0 |
| `einheit` | Mengeneinheit | Text | frei, z. B. `Stk`, `m²` |
| `preis` | Einzelpreis in € | Zahl (Text) | frei |
| `status` | Baufortschritt | Text | `PART_STATUS` (`common.py:33`): Idee, Recherche, Entschieden, Bestellt, Geliefert, Verbaut — **geprüft** (`parts.py:151-152`) |
| `prioritaet` | Priorität | Text | `PART_PRIO` (`common.py:34`): Kritisch, Hoch, Mittel, Nice-to-have — **geprüft** (`parts.py:153-154`) |
| `link` | Kauflink | URL-Text | frei |
| `haendler` | Händlername | Text | frei, Gruppierung in `buy_next()` |
| `fuer_aufgabe` | Bezug zu einer Aufgaben-ID | Text | freie ID, kein Fremdschlüssel-Zwang |
| `entscheidung` | Bezug zu einer Entscheidungsseite | Text | Dateiname/Titel der Seite, kein Anker |
| `kennwerte` | technische Kennwerte | Text | frei, z. B. „1,5 mm" |
| `gewicht_kg` | Gewicht je Einheit | Zahl (Text) | frei |
| `notiz` | Freitext | Text | frei |
| `gekauft_am` | Kaufdatum | Text | frei, im Bestand durchgehend leer (0 von 67 Zeilen gesetzt) |

`gesamt` (Menge × Preis) ist reine Excel-Formelspalte (`COMPUTED`,
`parts.py:21`), keine echte CSV-Spalte.

### `data/bauteile.csv` — was selbst gebaut/zugeschnitten wird

`FIELDS` in `tools/bauteile.py:20-24`:

| Spalte | Bedeutung | Typ | Erlaubte Werte |
|---|---|---|---|
| `id` | Kennung wie bei parts | Text | eindeutig, ungeprüft |
| `titel` | Name des Einzelteils | Text | frei |
| `bereich` | Bereichszuordnung | Text | frei, sollte einem Bereichsnamen entsprechen |
| `art` | Materialart | Text | `BAUTEIL_ART` (`common.py:58-61`): Platte, Leiste, Kantholz, Blech, Rohr, Kabel, Beschlag, Sonstiges — geprüft (`bauteile.py:174-175`) |
| `material` | konkretes Material | Text | frei, z. B. „EpicPLY-Multiplex" |
| `laenge_mm`, `breite_mm`, `dicke_mm` | Maße | Zahl (Text) | frei, jeweils optional |
| `anzahl` | Stückzahl | Zahl (Text) | Default 1 (`anzahl()`, `bauteile.py:61-62`) |
| `teil_id` | Bezug zu `parts.csv` (Rohmaterial) | Text | optional, ausdrücklich leer erlaubt |
| `fuer_aufgabe` | Bezug zu einer Aufgaben-ID | Text | frei |
| `massquelle` | Herkunft des Maßes | Text | `MASSQUELLE` (`common.py:63`): geschaetzt, gemessen, cad — geprüft (`bauteile.py:176-177`) |
| `status` | Baufortschritt | Text | `BAUTEIL_STATUS` (`common.py:62`): Idee, Geplant, Zugeschnitten, Verbaut — geprüft (`bauteile.py:172-173`) |
| `gewicht_kg` | Gewicht je Stück | Zahl (Text) | frei, optional — leer erlaubt (siehe unten) |
| `notiz` | Freitext | Text | frei |

`flaeche_m2`/`laufmeter` sind reine Excel-Formelspalten (`COMPUTED`,
`bauteile.py:27`). **`data/bauteile.csv` enthält aktuell nur die
Kopfzeile, keine einzige Datenzeile** — das Format ist ausschließlich
durch den Code belegt, nicht durch reale Daten.

Im Gegensatz zu `parts.csv` hat `bauteile.csv` kein `preis`-Feld — Einzelteile
werden nicht selbst bepreist, das Rohmaterial dazu steht (falls vorhanden)
über `teil_id` in `parts.csv` (Docstring `bauteile.py:1-9`).

#### `gewicht_kg` — angegeben oder aus Holzdichte berechnet

`gewicht_kg` ist wie bei `parts.csv` das Gewicht je Stück, multipliziert mit
`anzahl` für die Zeilensumme (`bauteile.gewicht()`). Es darf leer bleiben:

- Ist `gewicht_kg` gesetzt, gilt dieser Wert (Quelle „angegeben").
- Ist es leer **und** `art` eine von `Platte`, `Leiste`, `Kantholz`
  (`common.BAUTEIL_ART_MIT_VOLUMENGEWICHT`) **und** `material` per
  Teilstring (klein geschrieben) auf einen Eintrag in `common.MATERIAL_DICHTE`
  passt **und** `laenge_mm`/`breite_mm`/`dicke_mm` alle drei gesetzt sind,
  wird gerechnet: Volumen (m³) × Dichte (kg/m³) × `anzahl` (Quelle
  „berechnet"). `MATERIAL_DICHTE` trägt grobe Richtwerte aus der
  Holzliteratur (Trockenraumdichte), keine Datenblattwerte einzelner Platten.
- Sonst (Blech, Rohr, Kabel, Beschlag, Sonstiges — dort trifft
  Länge×Breite×Dicke keine sinnvolle Form — oder Maße/Material fehlen) bleibt
  das Gewicht unbekannt (Quelle „fehlt"), ohne zu raten.

Für Blech/Rohr/Kabel/Beschlag gibt es keinen Rechenweg — dort muss
`gewicht_kg` von Hand eingetragen werden, sonst zählt die Zeile in
`camper gewicht` als „ohne Gewichtsangabe".

---

## 7. Medien

Quelle: `tools/media.py`.

- **Ablage**: `vault/Medien/<Bereich>/<YYYY-MM-DD>-<slug(Dateiname)><ext>`
  für Bilder/Dokumente, `vault/Modelle/<Bereich>/…` für 3D-Dateien
  (`wurzel()`, `media.py:22-24`). Ordner ohne Bereichsangabe heißen
  `Unsortiert` (`zielname()`, `media.py:29`). Kollisionen bekommen ein
  `-2`, `-3` … angehängt.
- **Erkannte Endungen**: Bilder `.jpg .jpeg .png .webp`; Dokumente
  `.pdf .docx .doc .odt .xlsx`; Modelle
  `.glb .gltf .stl .step .stp .3mf .f3d .skp .dxf` (`media.py:10-15`).
- **Verkleinerung**: Bilder werden beim Einsortieren auf max. 1600 px lange
  Kante verkleinert (`MAX_KANTE`), beim Web-Export zusätzlich auf 1000 px
  (`WEB_KANTE`) — zwei unabhängige Kopien (Vault-Original, Web-Kopie unter
  `docs/medien/`, letztere erzeugt).
- **Verknüpfung zu Aufgaben/Teilen ist eine Heuristik, kein Feld**:
  `fotos_zu_id()` (`build.py:33-47`) vergleicht Wort-für-Wort (≥ 4 Zeichen,
  an `-` getrennt) die ID einer Aufgabe/eines Teils mit dem Dateinamen des
  Bildes — z. B. passt `armaflex-1-5-mm-decke` zu
  `2026-09-17-armaflex.png` über das gemeinsame Wort `armaflex`. Es gibt
  **kein** explizites „gehört zu"-Feld in CSV oder Markdown.
- **Bereichszuordnung** von Bildern läuft ausschließlich über den
  Ordnernamen unter `vault/Medien/`, nicht über ein Feld in der Datei
  selbst.

---

## 8. Matrix: bearbeitbar im Web / nur Claude

Vorgabe wörtlich aus `UMBAU.md`, Abschnitt „Ziel", auf Felder/Abschnitte
abgebildet:

| Bereich | Element | Web-bearbeitbar | Nur Claude (lesend im Web) |
|---|---|---|---|
| Bereichsdatei | `## Beschreibung` | ✓ | |
| Bereichsdatei | `## Stand` | ✓ | |
| Bereichsdatei | `## Auslegung` | | ✓ |
| Bereichsdatei | `## Notizen` | ✓ | |
| Bereichsdatei | `## Links` | ✓ | |
| Bereichsdatei | `## Aufgaben` — anlegen, abhaken, umbenennen, beschreiben, löschen | ✓ | |
| Bereichsdatei | Kopf-Feld `phase` | | ✓ |
| Bereichsdatei | Kopf-Felder `kurz`, `status` | ✓ | |
| Bereichsdatei | Kopf-Feld `bereich` (Name) | | ✓ |
| `parts.csv` | `status`, `preis`, `menge`, `notiz` | ✓ | |
| `parts.csv` | `titel`, `link`, `haendler`, `kategorie`, `prioritaet`, `gekauft_am`; neue Zeile anlegen | ✓ | |
| `parts.csv` | `id`, `beschreibung`, `einheit`, `fuer_aufgabe`, `entscheidung`, `kennwerte`, `gewicht_kg` | | ✓ |
| `bauteile.csv` | „Einzelteile" (laut UMBAU.md pauschal bearbeitbar) | ✓ | |
| `vault/Entscheidungen/` | ganze Seite | | ✓ |
| `vault/Anleitungen/` | ganze Seite | | ✓ |
| `vault/Recherche/` | ganze Seite | | ✓ |
| Alles Berechnete (`gesamt`, `flaeche_m2`, `laufmeter`, Fortschrittsbalken, `docs/data.json` insgesamt) | | ✓ |

Löschen entfernt laut UMBAU.md wirklich aus der Datei (Git sichert den
Verlauf), zusätzlich bleibt bei Aufgaben der Status „verworfen" (`-`)
als Option erhalten.

---

## 9. Abweichungen im Bestand

1. **`data/parts.csv`, Zeilen 64, 66, 67, 68** (`bremsenreiniger`,
   `kleber-fensterrahmen`, `polymax-kleber-holzlatten`,
   `rostschutz-hammerite`): `system` weicht von `kategorie` ab
   (`kategorie=Verbrauchsmaterial`, `system=Dämmung`/`Karosserie`) — bei
   den übrigen 63 Zeilen sind beide Felder identisch. Kein Fehler laut
   Code (beide Felder sind unabhängig und ungeprüft), aber unklar, ob das
   die beabsichtigte Regel ist oder Zufall (siehe offene Frage 7).
2. **`data/bauteile.csv`**: nur Kopfzeile, keine Datenzeile. Das gesamte
   Spaltenformat in Abschnitt 6 ist ausschließlich durch `tools/bauteile.py`
   belegt, durch keine reale Zeile geprüft.
3. **`vault/Anleitungen/` und `vault/Recherche/`**: leer. Der in Abschnitt 5
   beschriebene Aufbau der Entscheidungsseiten (Frage/Vergleich/Wahl/
   Verknüpft) ist dort nicht übertragbar belegt — nur die generische
   Kopf-Auswertung (`status`, `bereich`) ist durch Code gedeckt.
4. **`tools/tasks.py`**: die im Docstring (`tasks.py:1-17`) und per Regex
   (`BESCHREIBUNG` Zeile 37, `MARKE`/`@dauer` Zeile 40, Verschachtelung
   `ebene()` Zeile 43-44) unterstützten Aufgaben-Elemente — eingerückte
   Unteraufgaben, `> `-Beschreibungszeilen, `@dauer:`-Marken — kommen in
   keiner der 7 Bereichsdateien vor. Format-Fähigkeit ohne Beleg im
   Bestand.
5. **`tools/parts.py:144-158`** (`set_field`) prüft nur `status` und
   `prioritaet` gegen ihre festen Listen. `kategorie`, obwohl
   `PART_KATEGORIEN` existiert und für die Sortierung benutzt wird
   (`kat_index`, `parts.py:46-48`), wird beim Schreiben nicht geprüft —
   ein Tippfehler würde die Zeile unbemerkt ans Ende der Sortierung
   schieben, statt einen Fehler zu melden.
6. **`tools/bereiche.py`**: `status` im Bereichskopf wird nirgends gegen
   `BEREICH_STATUS` (`common.py:44`) geprüft — anders als bei Teilen
   (`parts.py`) und Einzelteilen (`bauteile.py`), wo `status` beim
   Schreiben validiert wird. Aktuell im Bestand nur mit den drei
   korrekten Werten belegt (`geplant`/`in-arbeit`/`fertig`), aber ohne
   Prüfmechanismus im Code.
7. **`tools/common.py:98-121`** (`split_frontmatter`): liest nur einen
   flachen Teilbereich von YAML (Schlüssel: Wert, einfache Listen), kein
   vollständiger YAML-Parser — die Bezeichnung „YAML-Kopf" in den
   Docstrings von `bereiche.py` und `tasks.py` ist also enger gemeint, als
   der Name andeutet. Kein realer Kopf verletzt diese Einschränkung
   aktuell.
8. **Querverweise `[[…]]`** kommen in `Möbel.md:51`, `Karosserie.md:27`,
   `Kühlschrank Modell.md:59-60` als handgeschriebener Fließtext vor,
   werden aber von keinem Werkzeug aufgelöst (siehe Abschnitt 4) — im
   erzeugten `vault/Stückliste/` und `vault/Medien/Medien.md` dagegen
   ist dieselbe Syntax funktional gemeint (fürs Obsidian-Backlink-Netz),
   wird aber ebenso wenig vom eigenen Code gelesen. Zwei Verwendungen
   derselben Syntax ohne einheitliche Bedeutung im System.

---

## 10. Entscheidungen (2026-09-18)

Die offenen Fragen des Entwurfs sind entschieden. Sie gelten für den Kern
und für `camper check`.

1. **Querverweise `[[Name]]` bleiben.** Das neue Dashboard löst sie auf
   (Bereich, Entscheidung, Anleitung, Recherche, Teil) und macht sie
   klickbar. Tote Verweise meldet `camper check`.
2. **Aufgaben:** Unterpunkte (Einzug zwei Leerzeichen), `> `-Beschreibung
   und `@dauer:` unterstützt der Kern vollständig, verlangt sie aber nicht.
   Jede Aufgabe trägt einen `^anker`; fehlt er, erzeugt der Kern beim
   Schreiben einen eindeutigen.
3. **Bereichskopf `status`** wird gegen `geplant|in-arbeit|fertig` geprüft.
4. **`kategorie` in `parts.csv`** wird gegen die feste Liste geprüft.
5. **Anleitungen und Recherche bekommen einen festen Aufbau.**
   Anleitung: Kopf, dann `## Material`, `## Werkzeug`, `## Schritte`.
   Recherche: Kopf, dann `## Frage`, `## Quellen`, `## Ergebnis`.
6. **Medien** bleiben über den Namensabgleich verknüpft, kein eigenes Feld.
7. **`kategorie` und `system` werden zusammengelegt.** Es bleibt nur
   `kategorie`; die Spalte `system` entfällt. Wert ist der Bereich, in dem
   das Teil gebraucht wird; `Verbrauchsmaterial` nur für Teile ohne festen
   Bereich. Die vier abweichenden Zeilen (Abweichung 1) bekommen ihren
   bisherigen `system`-Wert als Kategorie.
8. **`bereich:` im Kopf ist Pflicht** und muss zum Dateinamen passen.
9. **Web-bearbeitbar** zusätzlich: Bereichskopf `kurz` und `status`;
   bei Teilen `titel`, `link`, `haendler`, `kategorie`, `prioritaet`,
   `gekauft_am`; Teile im Web neu anlegen (ID wird erzeugt). Nur Claude:
   Bereichsname, `phase`, alle `id`-Spalten und die übrigen Teilefelder
   (`beschreibung`, `einheit`, `fuer_aufgabe`, `entscheidung`, `kennwerte`,
   `gewicht_kg`).

---

## 11. Projektkopf `vault/Camper.md` — Budget

Quelle: `tools/budget.py`. `vault/Camper.md` ist die einzige projektweite
Datei mit YAML-Kopf (`projekt`, `fahrzeug`) — der Ort für weitere
projektweite, von Hand gepflegte Zahlen, statt einer eigenen Ablage nur
dafür.

```yaml
---
projekt: VanMaster
fahrzeug: Renault Master 2013
budget: 25000
budget_elektrik: 4000
---
```

- `budget` — Zielbudget in Euro, das ganze Projekt. **Fehlt im Bestand**,
  solange der Nutzer keins einträgt — `camper budget` erklärt dann nur, wo
  es hingehört, ohne eine Zahl zu erfinden.
- `budget_<kategorie>` — optionales Budget je `PART_KATEGORIEN`-Eintrag
  (`common.py:37-40`), Feldname über `slug()` gebildet (z. B. `Dämmung` →
  `budget_daemmung`, `Küche` → `budget_kueche`).
- Beide Felder werden nur gelesen, nie über `tools/kern/` geschrieben — der
  Nutzer trägt sie selbst im Kopf von `vault/Camper.md` ein, wie `projekt`
  und `fahrzeug` heute schon.
- Zahlen akzeptieren Komma oder Punkt (wie `parts.num()`); ein fehlendes
  oder nicht lesbares Feld ergibt `None`, kein Fehler.

---

## 12. `data/verlauf.csv` — Kostenverlauf

Quelle: `tools/verlauf.py`. Ein Datensatz je Kalendertag, fortgeschrieben von
`camper verlauf`:

| Spalte | Bedeutung |
|---|---|
| `datum` | `JJJJ-MM-TT`, ein Eintrag je Tag (eindeutig) |
| `bezahlt` | Summe der Teile mit Status Bestellt/Geliefert/Verbaut |
| `geplant` | Summe der Teile mit Status Idee/Recherche/Entschieden |
| `prognose` | `bezahlt + geplant` |
| `aufgaben_fertig`, `aufgaben_gesamt` | Aufgaben-Fortschritt zum Zeitpunkt der Erfassung |
| `gewicht_kg` | Gewichtssumme der Stückliste, leer wenn 0 |

Liegt bewusst unter `data/`, **nicht** unter `data/generated/`: Letzteres
wird bei jedem `sync` verworfen und neu geschrieben, die Historie muss aber
über sync-Läufe hinweg erhalten bleiben und in Git nachvollziehbar sein —
wie `data/parts.csv` und `data/bauteile.csv` ist sie von Hand lesbar (CSV,
UTF-8, LF) und wird ausschließlich über `tools/verlauf.py` fortgeschrieben.
Ein erneuter Aufruf am selben Tag ersetzt die Zeile dieses Tages, statt eine
Dublette anzulegen.

---

## 13. Projektkopf `vault/Camper.md` — Fahrzeug-Kenndaten

Quelle: `tools/gewicht.py`. Wie das Zielbudget (§11) stehen die
Fahrzeug-Kenndaten für die Zuladungsbilanz im Kopf von `vault/Camper.md` —
derselbe Grund: einzige projektweite Datei mit YAML-Kopf, statt einer neuen
Ablage nur für zwei Zahlen.

```yaml
---
projekt: VanMaster
fahrzeug: Renault Master 2013
leergewicht_kg: 2100
zul_gesamtgewicht_kg: 3500
---
```

- `leergewicht_kg` — Leergewicht laut Fahrzeugschein (Zulassungsbescheinigung
  Teil I, Feld G). **Fehlt im Bestand**, solange der Nutzer es nicht
  einträgt.
- `zul_gesamtgewicht_kg` — zulässiges Gesamtgewicht laut Fahrzeugschein
  (Feld F.2). **Fehlt im Bestand** ebenso.
- Beide Felder werden nur gelesen, nie über `tools/kern/` geschrieben — der
  Nutzer trägt sie selbst ein, wie `projekt`/`fahrzeug` und die
  Budget-Felder aus §11 schon heute. Zahlen akzeptieren Komma oder Punkt.
- `camper gewicht` rechnet daraus die zulässige Zuladung
  (`zul_gesamtgewicht_kg − leergewicht_kg`) und bilanziert sie gegen die
  Gewichtssumme aus `data/parts.csv` und `data/bauteile.csv`
  (`tools/gewicht.py:bilanz()`). Fehlt eines der beiden Felder, erklärt der
  Befehl nur, wo sie eingetragen werden, statt Werte zu erfinden.
