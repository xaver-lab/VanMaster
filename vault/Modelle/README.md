---
typ: modelle
---

# 3D-Modelle

Je Bereich ein Unterordner, gleich benannt wie in `vault/Bereiche/`:
`vault/Modelle/Möbel/`, `vault/Modelle/Küche/` …

Erkannte Dateien: `.glb` `.gltf` `.stl` `.step` `.stp` `.3mf` `.f3d` `.skp` `.dxf`.
Einsortiert wird wie bei den Bildern:

    python camper.py media --ordner "Konstruktion" --bereich "Möbel"

Im Dashboard steht jede Datei beim zugehörigen Bereich. `.glb`, `.gltf` und
`.stl` sind für die Anzeige im Browser vorgesehen — der Betrachter kommt,
sobald die erste Datei da ist. Alles andere ist vorerst nur zum Herunterladen.
