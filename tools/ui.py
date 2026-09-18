"""Tkinter-Fenster: die häufigen Befehle als Knöpfe, Ausgabe im Fenster."""
from __future__ import annotations

import io
import threading
import tkinter as tk
from contextlib import redirect_stdout, redirect_stderr
from tkinter import scrolledtext, ttk

from .common import ROOT

KNOEPFE = [
    ("Lage", ["status"]),
    ("Kurzbericht", ["status", "--brief"]),
    ("Nächste Aufgaben", ["tasks", "next"]),
    ("Stückliste", ["parts"]),
    ("Einkauf", ["buy", "next"]),
    ("Excel schreiben", ["parts", "excel"]),
    ("Excel einlesen (Vergleich)", ["parts", "import"]),
    ("Excel übernehmen", ["parts", "import", "--apply"]),
    ("Bilder einsortieren", ["media"]),
    ("Sync", ["sync"]),
]

FARBEN = {"bg": "#14181f", "flaeche": "#1c222c", "text": "#e6ebf2",
          "gedaempft": "#93a0b4", "akzent": "#ffb84d"}


def run() -> None:
    from camper import main as camper_main

    fenster = tk.Tk()
    fenster.title("VanMaster")
    fenster.geometry("900x620")
    fenster.configure(bg=FARBEN["bg"])

    kopf = tk.Label(fenster, text="VanMaster", bg=FARBEN["bg"],
                    fg=FARBEN["text"], font=("Segoe UI", 16, "bold"))
    kopf.pack(anchor="w", padx=14, pady=(12, 0))

    leiste = tk.Frame(fenster, bg=FARBEN["bg"])
    leiste.pack(fill="x", padx=10, pady=8)

    ausgabe = scrolledtext.ScrolledText(
        fenster, bg=FARBEN["flaeche"], fg=FARBEN["text"],
        insertbackground=FARBEN["text"], relief="flat",
        font=("Consolas", 11), wrap="none", padx=10, pady=8,
    )
    ausgabe.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    fuss = tk.Label(fenster, text=str(ROOT), bg=FARBEN["bg"],
                    fg=FARBEN["gedaempft"], font=("Segoe UI", 8))
    fuss.pack(anchor="w", padx=14, pady=(0, 8))

    def zeige(text: str) -> None:
        ausgabe.delete("1.0", "end")
        ausgabe.insert("1.0", text)

    def starte(argv: list[str]) -> None:
        zeige(f"$ camper {' '.join(argv)}\n\n…")

        def arbeit() -> None:
            puffer = io.StringIO()
            try:
                with redirect_stdout(puffer), redirect_stderr(puffer):
                    camper_main(argv)
            except SystemExit:
                pass
            except Exception as fehler:  # im Fenster sichtbar statt in der Konsole
                puffer.write(f"\n{type(fehler).__name__}: {fehler}")
            text = f"$ camper {' '.join(argv)}\n\n{puffer.getvalue()}"
            fenster.after(0, lambda: zeige(text))

        threading.Thread(target=arbeit, daemon=True).start()

    def dashboard() -> None:
        import webbrowser
        # Setzt eine laufende `camper serve` voraus — es gibt keine
        # statische Dashboard-Datei mehr.
        webbrowser.open("http://localhost:8765/")

    alle = KNOEPFE + [("Dashboard", None)]
    for i, (beschriftung, argv) in enumerate(alle):
        reihe, spalte = divmod(i, 6)   # zwei Reihen, sonst läuft es aus dem Fenster
        ttk.Button(
            leiste, text=beschriftung,
            command=dashboard if argv is None else (lambda a=argv: starte(a)),
        ).grid(row=reihe, column=spalte, padx=3, pady=2, sticky="ew")
    for spalte in range(6):
        leiste.columnconfigure(spalte, weight=1)

    starte(["status", "--brief"])
    fenster.mainloop()
