---
bereich: Küche
kurz: Kochstelle, Kühlschrank, Spüle, Stauraum
status: in-arbeit
---

# Küche

## Beschreibung

Der Küchenblock an der Schiebetür: Gaskocher, Spüle, Kompressorkühlschrank und
darunter Stauraum. Er ist das Möbel mit den meisten Anschlüssen — Frisch- und
Abwasser, 12 V für den Kühlschrank, Gas für den Kocher — und gleichzeitig das
Stück, das die Gangbreite bestimmt.

## Stand

**Kühlschrank.** Drei Belluna-Modelle sind durchgerechnet (80 L, 85 L, 92 L),
Ergebnis in [[Kühlschrank Modell]]. Feststehende Punkte:

- Alle drei liegen bei 45–50 W Spitze, also rund 4,2 A bei 12 V. Die
  6-A-Sicherung der Küchenzone reicht. Tagesverbrauch etwa 390 Wh, das sind
  13–15 % der 300 Ah LiFePO4.
- Die Einbautiefe steuert den Gang: 44–45 cm lassen bei 171 cm Innenbreite
  etwa 81–82 cm Gang, 54 cm nur noch 72 cm.
- Türanschlag soll links sitzen, Griff rechts, damit die Tür zur
  Fahrerseitenwand aufschwingt und den Gang frei lässt.

**Wasser in der Küche.** Frischwasser kommt aus Weithalskanistern DIN 96 im
Küchenschacht (siehe [[Wasser]]). Der Abwassertank soll nicht mehr in der Tür
sitzen.

**Klappen.** Für Waschbecken-, Kocher- und Wassertankklappe ist ein
EasyConnect-Scharnier-Set von Camping Wagner vorgesehen. Die Klappenstärke
liegt durch das Push-Lock-Schloss bei 14–16 mm (siehe [[Möbel]]).

## Auslegung

| | Wert | Quelle |
|---|---|---|
| Innenbreite Laderaum | 171 cm | Fahrzeugmaß |
| Gang bei 44–45 cm Kühlschranktiefe | 81–82 cm | gerechnet |
| Gang bei 54 cm Kühlschranktiefe | 72 cm | gerechnet |
| Kühlschrank Spitzenlast | 45–50 W ≈ 4,2 A bei 12 V | Herstellerangabe |
| Kühlschrank Tagesverbrauch | ~390 Wh ≈ 13–15 % der Bank | gerechnet |
| Sicherung Küchenzone | 6 A | Elektrikplanung, reicht aus |
| Klappenstärke | 14–16 mm | Vorgabe Push-Lock-Schloss |

## Notizen

Rohnotizen aus `_input/Küche/infos.txt`, unbewertet — die Anordnung entscheidet
der Nutzer:

- Neben dem Waschbecken ein Kasten für Geschirr und Kochzeug? Nur falls unten
  in der Küche nichts mehr frei wird.
- Vorne links Schuhkasten unten neben dem Wassertank, darüber Müll oder Lade.
- Müll vielleicht direkt beim Bett statt in der Küche.
- Ausklapptisch zum Beifahrersitz hin, für den geschlossenen Van. Ideenbild
  dazu (Wandarm-Tisch, zum Fahrerbereich geschwenkt) liegt unter [[Möbel]].
- Wasserhahn daneben setzen, damit man auch bei geschlossener Platte Wasser
  holen kann.
- Abwassertank nicht mehr in der Tür (Abblaseventil). Wenn er ausgebaut wird,
  dann gleich zusammen mit dem Frischwasser.
- Aus der Einkaufsliste: „Wasserhahn ohne Hahn" — vermutlich Spüle ohne
  mitgelieferte Armatur, Armatur separat. Noch zu bestätigen.

**Bilder.** Sieben Sammelbilder aus fremden Ausbauten, als Ideenspeicher: ein
Küchenblock an der Schiebetür mit ausziehbarem Kühlschrankfach und Hängeschrank
darüber; ein Müllauszug als schmale Lade neben dem Kühlschrank; ein
Küchensockel mit indirekter Beleuchtung im Türausschnitt; Wasserkanister
stehend in einem schmalen Schacht; eine Edelstahlspüle mit hölzernem
Abdeckbrett; ein Gaskocher hinter einer Klappe mit seitlichem Ausklapptisch;
eine Kocher-Spülen-Kombination mit Klappdeckel und angesetztem Ausklapptisch.
Keine Maße darauf.

## Links

- [Belluna 80 L Kompressorkühlschrank](https://belluna.eu/shop/80-liter-hxbxt-810x475x450-mm-mit-gefrierfach/) — Empfehlung 1, Türanschlag wählbar
- [Belluna 85 L (Alpicool AC85)](https://belluna.eu/shop/85/) — Empfehlung 2, sofort lieferbar
- [Belluna 92 L](https://belluna.eu/shop/92-liter-hxbxt-82x51x54-cm-mit-gefrierfach/) — eigener Favorit, 54 cm tief
- [Scharnierwechsel Kühlschranktür](https://youtu.be/Z-e6uzbQdf4) — Anleitung für den Türanschlag
- [Camping Wagner EasyConnect Scharnier-Set](https://www.campingwagner.at/de/p/camping-wagner-easyconnect-scharnier-komplett-set_146918) — Klappen Waschbecken, Kocher, Wassertank
- [Comet Weithalskanister DIN 96](https://www.comet-pumpen.de/produkte-caravan-freizeit/kanister/kanister-din-96/weithalskanister.html) — Frischwasser als Kanisterlösung

## Aufgaben

### Ausstattung

- [ ] Kochstelle entscheiden ^kochstelle-entscheiden #hoch
- [ ] Kühlschrank entscheiden ^kuehlschrank-entscheiden #hoch @braucht:strombilanz
- [ ] Küche einbauen ^kueche-einbauen @braucht:kuechenblock
