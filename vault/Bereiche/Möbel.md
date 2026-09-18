---
bereich: Möbel
kurz: Bett, Küchenblock, Hängeschränke, Sitzbank, Tisch, Toilette, Stauraum
status: in-arbeit
phase: 6
---

# Möbel

## Beschreibung

Bett, Küchenblock, Schränke, Sitzbank mit Toilette, Tisch, Befestigung an der Karosserie.

## Stand

### Hängeschränke

Korpus und Fronten aus EpicPLY-Multiplex. Die Fronten sind Klappen, die nach
oben schwenken, keine seitlich öffnenden Türen — so steht beim Kochen nichts
auf Kopfhöhe im Weg.

**Beschläge**

- Klappenbeschlag Grass Kinvaro T-57 (Hochschwenk-Automatik, 240 N). Trägt
  Klappen bis 6,2 kg, öffnet auf 75 oder 90°. Ein Paar je Klappe.
- Verschließbares Push-Lock-Schloss statt Griff: sitzt bündig, hakt nicht am
  Kopf und hält die Klappe auf der Fahrt zu.
- Zusätzlich Möbelmagnete an den Klappen.

**Was das für den Zuschnitt heißt**

- Die Klappen müssen **14–16 mm** stark sein, sonst passt das Push-Lock nicht.
  Pro Schloss ein Loch mit 26 mm Durchmesser in der Front.
- Klappengewicht pro Beschlagpaar unter 6,2 kg halten. Bei 15 mm Multiplex
  (rund 10 kg/m²) heißt das: Klappenfläche höchstens etwa 0,6 m².
- Über der Klappe muss der Öffnungsweg frei bleiben — der Beschlag schwenkt
  die Front nach oben vor die Decke.

### Sitzbank, Tisch und Toilette

**Toilette.** Eine Kassettentoilette (Porta-Potti-Bauart) sitzt ausziehbar in
einer Lade neben der Sitzbank — auf einem Rollbrett mit kleinen Lenkrollen,
sodass sie sich beim Entleeren einfach herausziehen lässt. Ein
Klopapierhalter mit zwei Rollen sitzt in derselben Lade daneben.

**Tisch.** Zweiteilige Bambus-Tischplatte auf einem einzelnen Metallbein:
eine kleinere Platte liegt über einer größeren, vermutlich zum Vergrößern der
Fläche verschieb- oder klappbar. Separat dazu ein Wandarm-Tisch, der sich zum
Beifahrersitz hin schwenken lässt und dort als kleine Ablage direkt am
Fahrersitzbereich dient — deckt sich mit der Notiz „Ausklapptisch zum
Beifahrersitz" unter [[Küche]].

**Gewürzregal.** Schmales Auszugregal mit Drahtkörben auf einer
Vollauszugschiene, an eine Schrankseite montiert.

**Maße aus der Konstruktion.** Aus den handschriftlichen Aufmaßen
(`_input/Konstruktion/Maße.txt`): Ausziehlade 162 × 82 cm, Kisten 80 × 40 cm
— letzteres deckt sich mit dem Euro-Stapelbehälter-Format aus dem Ideenbild
in den Notizen unten.

## Auslegung

_(Zahlen, sobald gerechnet)_

## Notizen

- Wabenmuster im CAD-Seitenteil ist eine Idee zur Gewichtsersparnis, noch nicht
  gerechnet.
- Stückzahl der Klappen hängt am Layout, deshalb stehen die Beschlagmengen offen.

Aus `_input/Kühlschrank und Sitzbank/` (Rohnotizen und Ideenbilder, unbewertet):

- Ideenbild eines fertigen Ausbaus zeigt Hängeschränke, Dachfenster und
  Kochstelle im Zusammenspiel — als grober Raumeindruck, keine Maße.
- Toilettenmodell, Rollbrett-Konstruktion und Tischform sind noch offen.

Aus `_input/Konstruktion/` (Rohnotizen und Ideenbilder, unbewertet — die
Anordnung entscheidet der Nutzer, Fahrzeug-Innenmaße dazu stehen unter
[[Karosserie]]):

- Zwei Grundriss-Varianten von Hand skizziert (2D, oben und Seitenansicht):
  Drehsitze vorne, Bett hinten, Küchenblock mit Kühlschrank und Spüle,
  Ausziehlade, Regal. Keine Maße auf der Skizze.
- Eine 3D-Skizze (axonometrisch) zeigt dieselbe Anordnung räumlich, mit
  „Kühlschrank", „Sessel 1/2", „Liegefläche" und „Kiste" beschriftet.
- Ein 3D-Render eines Schrankmoduls mit rot markierten Fächern — offenbar aus
  einem CAD- oder Konfigurator-Tool, Zweck der Markierung nicht klar.
- Ein 3D-Render von vier Euro-Stapelbehältern auf einer Holzplatte —
  Ideenbild für Stauraum in Schubladen- oder Regalform.
- Zwei Fotos mit handschriftlich eingetragenen Maßen an vorhandenen
  Gegenständen: eine zusammengerollte Matte/Zelttasche (Länge ca. 109 cm,
  Ø ca. 30 cm) und ein Camping-Falttisch (Platte ca. 68 × 100 cm,
  Beinhöhe zusammengeklappt 8,5 cm, Plattendicke 2,5–3 cm). Unklar, ob als
  Vorbild für einen zu bauenden Tisch oder als Maß für vorhandenes
  Campingzubehör gedacht.

Aus `_input/Ideas/Notizen.txt` (Rohnotiz, unbewertet):

- Lagerplatz für ein Fernglas über der Fahrerkabine.
- Faltbare Schwerlast-Winkelhalter mit Arretierung — als Beschlag-Idee, wofür
  genau ist offen.
- Frage, ob sich die Matratze aufstellen lässt, um darunter ranzukommen.
- CAD-Referenz für die Inneneinrichtung eines Renault Master Low Loader:
  https://grabcad.com/library/campervan-interior-renault-master-low-loader-1

## Links

- [Klappenbeschlag Grass Kinvaro T-57](https://www.amazon.de/dp/B01AC7CZ58) — Hochschwenk-Automatik, 240 N
- [Push-Lock Schrankschloss](https://www.amazon.de/dp/B0BCVGCT12) — 5er-Set, Türstärke 14–16 mm

## Aufgaben

### Aufbau

- [ ] Layout festlegen (macht der Nutzer) ^layout #kritisch
- [ ] Bettrahmen bauen ^bettrahmen @braucht:layout
- [ ] Küchenblock bauen ^kuechenblock @braucht:layout
- [ ] Stauraum und Schränke ^schraenke @braucht:layout
- [ ] Sitzbank mit Toilettenlade bauen ^sitzbank @braucht:layout
- [ ] Tisch anfertigen ^tisch @braucht:layout
