---
bereich: Karosserie
kurz: Innenmaße, Fenster- und Dachausschnitte, Rost, Durchführungen
status: geplant
phase: 2
---

# Karosserie

## Beschreibung

Alles am Fahrzeug selbst: Innenmaße und Konstruktionsgrundlagen, Ausschnitte
für Fenster und Dachfenster, Rostbehandlung, Durchführungen und Befestigungs-
punkte am Blech.

## Stand

**Innenraum-Aufmaß.** Der Laderaum ist von Hand komplett aufgemessen: Grundriss
am Boden (mit den beiden Radkasten-Ausschnitten), ein Schnitt auf mittlerer
Höhe, der Dachbereich, der Ausschnitt der Schiebetür sowie die Wandabwicklung
von Fahrer- und Beifahrerseite. Das ist die Grundlage, an der sich Kühlschrank,
Küchenblock und die übrigen Möbel bei Tiefe und Breite messen müssen (siehe
[[Küche]] zur Gangbreite).

**Dachfenster.** Entschieden ist ein Dachfenster mit Lüfter, Fernbedienung,
Insektenschutz und Verdunkelung, 400×400 mm. Der Einbau läuft über einen
selbst gebauten Holzrahmen (Stärke Blechausschnitt +2 mm), der mit Polymax
angeklebt, von innen verschraubt und mit Butyl-Dichtmasse gegen das Fenster
abgedichtet wird; vor dem Einbau wird die geschnittene Blechkante mit
Rostschutz behandelt. Der Arbeitsablauf steht unter Aufgaben.

## Auslegung

Werte aus der handschriftlichen Aufmaß-Skizze (Foto), alle in cm. Ziffern auf
dem Foto teils eng beieinander — bei Zweifeln gegen das Originalblatt prüfen.

| Bereich | Maß | Wert |
|---|---|---|
| Boden, Grundriss | Länge oben (Fahrerseite) | 220 |
| Boden, Grundriss | Gesamtlänge, Variante 1 | 217 |
| Boden, Grundriss | Gesamtlänge, Variante 2 (ca.) | 237 |
| Boden, Grundriss | Breite rechts | 176 |
| Boden, Grundriss | Radkasten-Ausschnitt vorne | 77 |
| Boden, Grundriss | Radkasten-Ausschnitt hinten | 77 / 139 |
| Mittlere Höhe | Innenbreite | 172 |
| Dachbereich | Innenbreite oben | 138 |
| Dachbereich | Türausschnitt oben | 134 |
| Schiebetür-Ausschnitt | Breite oben | 138 |
| Schiebetür-Ausschnitt | Höhe links | 182 |
| Schiebetür-Ausschnitt | Breite bis Türschloss | 149 |
| Schiebetür-Ausschnitt | Breite unten | 157 |
| Fahrerseite, Wand | obere Reihe | 199 |
| Fahrerseite, Wand | Höhenversatz an der Fuge | 8,5 |
| Fahrerseite, Wand | Feld daneben | 140 |
| Beifahrerseite, Wand | Höhe erstes Feld | 145 |
| Beifahrerseite, Wand | Höhe zweites Feld | 134 |
| Beifahrerseite, Wand | Radkasten-Ausschnitt | 39 / 77 |

## Notizen

- Überschneidet sich mit dem Bereich Vorbereitung: Rost prüfen, Entkernen und
  Innenmaße aufnehmen liegen dort als Aufgaben. Beim Aufräumen der Struktur
  klären, ob die beiden Bereiche zusammengehören.
- Die Aufmaß-Skizze (`_input/Konstruktion/`) ist ein Foto von Hand
  beschrifteter Millimeterpapier-Zeichnungen, schräg fotografiert. Einzelne
  Zahlen sind auf dem Foto nicht zweifelsfrei zu lesen (z. B. zwei
  übereinanderstehende Werte am linken Rand des Bodengrundrisses, „175" und
  „157"); diese Stelle ist oben nicht übernommen und sollte am Original
  nachgeprüft werden.

Aus `_input/Fenster und Dachfenster/` (Rohnotiz, unbewertet — ob und wann die
Seitenfenster gebaut werden, entscheidet der Nutzer):

- Seitenfenster Fahrerseite: Notiz „erst einbauen, wenn Tisch fertig ist (dann
  perfekt)". Noch nicht festgelegt.
- Seitenfenster Beifahrerseite: Notiz „bauen wir?? (stört bei Küche!)". Ob es
  überhaupt kommt, ist offen — Konflikt mit der Küchenplanung angemerkt.

## Links

- [Dachfenster Super Fan 400×400](https://belluna.eu/shop/super-fan-dachfenster-mit-luefter-fernbedienung-insektenschutz-und-verdunkelung-400x400-mm-generation-3-1/) — Lüfter, Fernbedienung, Insektenschutz, Verdunkelung
- [Belluna Fenster-Kategorie](https://belluna.eu/kategorie/fenster/) — Übersicht für die noch offenen Seitenfenster

## Aufgaben

### Dachfenster einbauen

- [ ] Position bestimmen ^df-position
- [ ] Holzrahmen bauen, Stärke Blechausschnitt +2 mm ^df-rahmen @braucht:df-position
- [ ] Mit Rahmen anzeichnen, abkleben, schneiden ^df-schneiden @braucht:df-rahmen
- [ ] Testen, feilen, Rostschutz auftragen ^df-rostschutz @braucht:df-schneiden
- [ ] Holzrahmen mit Polymax ankleben ^df-ankleben @braucht:df-rostschutz
- [ ] Butyl-Dichtmasse einsetzen ^df-dichtmasse @braucht:df-ankleben
- [ ] Von innen verschrauben ^df-verschrauben @braucht:df-dichtmasse
