# VanMaster — Designsystem „Werkstattheft“

**Leitidee.** Ein Werkstattheft, kein Admin-Dashboard: warmes Papier (hell) bzw. Graphit (dunkel),
schwarze Tinte, genau eine Signalfarbe (Warnorange) für das, was jetzt Aufmerksamkeit braucht.
Zahlen stehen in Mono wie auf einer Maßzeichnung; Linien, Maßstriche und Raster ersetzen Deko.

Alle Bausteine in beiden Themen: `#/muster`. Stil global in `src/app.css`, Bausteine in `src/lib/ui/`.

## Tokens (CSS-Variablen)

| Gruppe | Namen | Einsatz |
|---|---|---|
| Flächen | `--farbe-grund` · `-flaeche` · `-flaeche-hoch` (Hover, Spur) · `-flaeche-tief` (Schiene) | Grund < Fläche = Karten |
| Linien | `--farbe-linie` (Trenner) · `--farbe-linie-stark` (Ränder von Eingaben, Maßlinien) | |
| Text | `--farbe-text` · `-text-2` (Nebentext, AA) · `-text-3` (nur Deko/Platzhalter, **nicht AA**) | |
| Signal | `--farbe-signal` · `-signal-grund` · `-auf-signal` | Hauptaktion, „läuft“, Fokus, offene Entscheidungen |
| Status | `--farbe-gut`/`-gut-grund` · `--farbe-info`/`-info-grund` · `--farbe-warn`/`-warn-grund` | erledigt · Info/Links · Fehler/blockiert |
| Tinte | `--farbe-tinte-fuellung` · `--farbe-auf-tinte` | aktive Chips, dunkle Etiketten |
| Schrift | `--schrift` (Archivo, variable Breite) · `--schrift-mono` (JetBrains Mono) | |
| Größen | `--text-xs` 12 · `-s` 13 · `-m` 15 · `-l` 18 · `-xl` 26 · `-2xl` 40 · `-3xl` 72 | |
| Breite | `--breit` (112 %, Überschriften) · `--schmal` (82 %, Versal-Etiketten) | `font-stretch` |
| Abstand | `--a-1`…`--a-8` = 4 8 12 16 24 32 48 64 px | nur diese Stufen |
| Radius | `--r-s` 3 · `--r-m` 6 (Knöpfe, Felder) · `--r-l` 10 (Karten) | keine Pillen |
| Schatten | `--schatten-1` (Karte) · `-2` (Hover) · `-3` (Dialog, Toast) | |
| Bewegung | `--t-kurz` 120 · `--t-mittel` 220 · `--t-lang` 480 ms · `--kurve` · `--kurve-feder` | |

Alte Namen (`--bg`, `--flaeche`, `--akzent`, `--gut`, `--wartet`, `--warn`, `--radius` …) sind Aliase
und funktionieren weiter; neuer Code nimmt die `--farbe-*`-Namen. `data-thema="hell|dunkel"` auf einem
Element erzwingt dort ein Thema.

## Bausteine (`import { Knopf, … } from '../lib/ui'`)

- **Knopf** `variante` primaer|sekundaer|leise|gefaehrlich · `groesse` s|m · `icon` · `iconRechts` · `href` · `laedt` · `kbd` · `voll` · `nurIcon`+`label`
- **IconKnopf** `icon` · `label` (Pflicht) · `variante` (leise) · `groesse` · `aktiv`
- **Feld** `bind:wert` · `label` · `hinweis` · `fehler` · `einheit` („mm“, „€“) · `icon` · `mono` · `klein` · `optional` · alle input-Attribute
- **Textfeld** `bind:wert` · `label` · `zeilen` · `wachsen` · `mono` · **Auswahl** `bind:wert` · `optionen` (string[] oder {wert,label}[]) · `leer`
- **Chip** `bind:aktiv` · `zahl` · `icon` · `onclick` (ersetzt das Umschalten) — für Filter
- **Etikett** `ton` neutral|signal|gut|info|warn|tinte · `mono` · `icon` — reine Beschriftung
- **Statusmarke** `status` offen|laeuft|erledigt|verworfen|blockiert · `kompakt` · `onclick` (wird Knopf). Texte/Typen in `ui/status.ts`
- **Kontrollkaestchen** `bind:checked` · `label`/children · `gemischt` · `durchstreichen` · `onchange(checked)`
- **Karte** `titel` · `zusatz` · `icon` · `aktionen` (Snippet) · `polster` normal|eng|keins · `ton` flaeche|vertieft|signal · `href`
- **Rubrik** `titel` · `zahl` · `aktionen` — Abschnittsüberschrift als Maßlinie, gliedert Seiten ohne Kästen
- **Dialog** `bind:offen` · `titel` · `beschreibung` · `breite` s|m|l · `festhalten` · `fuss` (Snippet). Esc, Fokusfalle, Fokus zurück; `data-fokus` legt den Startfokus fest
- **bestaetigen({ titel, text, ja, nein, gefaehrlich })** → `Promise<boolean>`; bei `gefaehrlich` steht der Fokus auf „Abbrechen“
- **Leerzustand** `titel` · `text` · `icon` · `marke` · `kompakt` · children = Aktion
- **FortschrittRing** `wert` 0..1 · `zusatz` (schraffiert) · `groesse` · `dicke` · `ton` · **FortschrittBalken** dazu `teilung` (ein Strich je Einheit) · `label` · `zahl`
- **Tabs** `tabs` [{id,label,zahl?,icon?}] · `bind:aktiv` · `onwechsel` — Inhalt wählt der Aufrufer
- **Kbd** `tasten="Strg K"` · Icons: `ui/icons.ts` (lucide, einzeln importiert; weitere per `@lucide/svelte/icons/<name>`)

## Regeln

- **Farbe bedeutet etwas.** Signal nur für: Hauptaktion (ein primärer Knopf je Bereich), „läuft“,
  offene Entscheidungen, Fokus. Grün = erledigt, Rot = Fehler/blockiert/gefährlich, Blau = Info/Links.
  Kategorien (Bereich, Händler) bleiben neutral — nie eigene Farben pro Bereich.
- **Status** immer mit Statusmarke (Form + Wort), nie nur Farbe. „läuft“ ist schraffiert/halb gefüllt.
- **Zahlen** (Maße, Preise, Mengen, IDs, Zähler) in `--schrift-mono` bzw. Klasse `.zahl`; Einheit klein
  und gedämpft dahinter. Maße in mm, Preise ohne Nachkommastellen in Übersichten.
- **Überschriften**: Seitentitel `--text-xl`, 750, `font-stretch: 115%`. Abschnitte mit `Rubrik`.
  Versal-Etiketten: `--text-xs`, 650, `letter-spacing: .1em`, `font-stretch: var(--schmal)`.
- **Dichte**: Listenzeilen 36–44 px, Karten innen `--a-5`, Abstand zwischen Abschnitten `--a-7`.
  Tabellen dürfen dichter sein (`--text-s`, Zeilen 32 px). Laptop zuerst (1280–1920 px), Inhalt max. 1480 px.
- **Flächen**: Karte nur für Zusammengehöriges; Listen randlos in `Karte polster="keins"`, Zeilen mit
  `--farbe-linie` getrennt. Kein Kasten im Kasten.
- **Lesemodus**: jede Bearbeitung in `<Schreibbar>` einwickeln — im Lesemodus keine Knöpfe/Felder.
- **Bewegung**: kurz und funktional (`--t-kurz` Hover, `--t-mittel` Auf/Zu). `prefers-reduced-motion` wird global beachtet.
- **Fokus**: nie `outline: none` ohne Ersatz — global gilt ein 2-px-Ring in `--farbe-fokus`.
