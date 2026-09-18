"""Stückliste: CSV ist die Wahrheit, Excel und Markdown sind Ausleihen.

Lesen läuft über ``tools.kern.lesen.teile_lesen`` (Grammatik/Spalten aus
``tools/kern/format.py``); Feld ändern und Anlegen über
``tools.kern.tabellen`` (Quelle ``claude`` — dieses Modul wird von der
Kommandozeile aus benutzt, das Dashboard schreibt über ``tools/serve.py``
direkt gegen den Kern mit Quelle ``web``). Der Massenschreibweg für den
Excel-Import bleibt hier (der Kern hat keine Massen-Import-Funktion),
schreibt aber über ``tools.kern.datei`` — mit Versionsschutz und atomar.
"""
from __future__ import annotations

import csv
import io
from pathlib import Path

from .common import (
    PARTS_CSV, PARTS_MD_DIR, PARTS_XLSX,
    PART_KATEGORIEN, PART_PRIO, PART_STATUS,
    bar, euro, fail, table, write_text,
)
from .kern import datei as kern_datei
from .kern import tabellen as kern_tabellen
from .kern.format import TEIL_BERECHNET as COMPUTED, TEIL_FELDER as FIELDS
from .kern.lesen import teile_lesen

# FIELDS: Spaltenreihenfolge von data/parts.csv. COMPUTED: Zusatzspalte nur
# in der Excel-Ausleihe, wird beim Import ignoriert. Beide aus
# tools/kern/format.py — einzige Stelle, die das Format kennt.


def load() -> list[dict]:
    return [{f: getattr(t, f) for f in FIELDS} for t in teile_lesen()]


def new_id(titel: str, rows: list[dict]) -> str:
    from .common import slug
    base = slug(titel) or "teil"
    existing = {r.get("id", "") for r in rows}
    if base not in existing:
        return base
    i = 2
    while f"{base}-{i}" in existing:
        i += 1
    return f"{base}-{i}"


def save(rows: list[dict]) -> None:
    """Schreibt die ganze Datei neu — für den Excel-Import (Massenschreiben,
    dafür hat der Kern keine eigene Funktion). Über ``kern.datei``, damit
    Hash-Versionsschutz und atomares Schreiben auch hier gelten."""
    PARTS_CSV.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(rows, key=lambda r: (kat_index(r), r.get("titel", "")))
    puffer = io.StringIO()
    writer = csv.DictWriter(puffer, fieldnames=FIELDS, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({f: row.get(f, "") for f in FIELDS})
    kern_datei.schreiben(PARTS_CSV, puffer.getvalue(), None)


def kat_index(row: dict) -> int:
    kat = row.get("kategorie", "")
    return PART_KATEGORIEN.index(kat) if kat in PART_KATEGORIEN else len(PART_KATEGORIEN)


def num(value, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", ".").strip() or default)
    except ValueError:
        return default


def gesamt(row: dict) -> float:
    return num(row.get("menge"), 1) * num(row.get("preis"))


def gewicht(row: dict) -> float:
    return num(row.get("menge"), 1) * num(row.get("gewicht_kg"))


def summe(rows: list[dict]) -> float:
    return sum(gesamt(r) for r in rows)


def gewicht_summe(rows: list[dict]) -> float:
    return sum(gewicht(r) for r in rows)


def find(part_id: str, rows: list[dict] | None = None) -> dict | None:
    rows = load() if rows is None else rows
    part_id = part_id.strip().lower()
    for row in rows:
        if row["id"].lower() == part_id:
            return row
    return None


# ---------------------------------------------------------------- Abfragen

def filtered(rows: list[dict], **f) -> list[dict]:
    def keep(row: dict) -> bool:
        for key, value in f.items():
            if not value:
                continue
            if key == "text":
                if str(value).lower() not in " ".join(row.values()).lower():
                    return False
            elif row.get(key, "").lower() != str(value).lower():
                return False
        return True
    return [r for r in rows if keep(r)]


def query_text(rows: list[dict]) -> str:
    if not rows:
        return "Keine Teile gefunden."
    body = [[
        r["id"], r["titel"][:34], r["kategorie"], r["status"],
        f"{num(r['menge'], 1):g} {r['einheit']}".strip(), euro(gesamt(r)),
    ] for r in rows]
    head = ["id", "titel", "kategorie", "status", "menge", "gesamt"]
    foot = f"\n{len(rows)} Teile · {euro(summe(rows))}"
    kg = gewicht_summe(rows)
    if kg:
        foot += f" · {kg:.1f} kg"
    return table(body, head) + foot


def overview_text() -> str:
    rows = load()
    if not rows:
        return "Stückliste ist leer."
    lines = []
    for kat in PART_KATEGORIEN:
        krows = [r for r in rows if r["kategorie"] == kat]
        if not krows:
            continue
        verbaut = len([r for r in krows if r["status"] == "Verbaut"])
        lines.append([kat, str(len(krows)), bar(verbaut, len(krows), 8),
                      euro(summe(krows))])
    body = table(lines, ["kategorie", "teile", "verbaut", "kosten"])
    offen = [r for r in rows if r["status"] in ("Idee", "Recherche")]
    return (f"{body}\n\nGesamt: {euro(summe(rows))} · "
            f"{gewicht_summe(rows):.1f} kg · "
            f"{len(offen)} Teile noch nicht entschieden")


def set_field(part_id: str, field: str, value: str) -> str:
    if field not in FIELDS or field == "id":
        fail(f"Unbekanntes Feld '{field}'. Erlaubt: {', '.join(FIELDS[1:])}")
    row = find(part_id)
    if row is None:
        fail(f"Kein Teil mit der Kennung '{part_id}'.")
    if field == "status" and value not in PART_STATUS:
        fail(f"Status muss einer von {', '.join(PART_STATUS)} sein.")
    if field == "prioritaet" and value not in PART_PRIO:
        fail(f"Priorität muss eine von {', '.join(PART_PRIO)} sein.")
    alt = row[field]
    try:
        kern_tabellen.teil_feld_setzen(row["id"], field, value, None, quelle="claude")
    except kern_tabellen.Ungueltig as fehler:
        fail(str(fehler))
    return f"{row['titel']}: {field} {alt or '—'} → {value}"


def add(titel: str, kategorie: str, **extra) -> str:
    felder = {"titel": titel, "kategorie": kategorie}
    felder.update({k: str(v) for k, v in extra.items() if v})
    try:
        neue_id, _ = kern_tabellen.teil_anlegen(felder, None, quelle="claude")
    except kern_tabellen.Ungueltig as fehler:
        fail(str(fehler))
    return f"Aufgenommen: {titel} ({neue_id}, {kategorie})"


# ------------------------------------------------------------ Einkaufszettel

def buy_next(limit: int = 0) -> str:
    rows = [r for r in load() if r["status"] == "Entschieden"]
    if not rows:
        return "Nichts zu bestellen — kein Teil steht auf 'Entschieden'."
    order = {p: i for i, p in enumerate(PART_PRIO)}
    rows.sort(key=lambda r: (order.get(r["prioritaet"], 9), -gesamt(r)))
    if limit:
        rows = rows[:limit]
    haendler: dict[str, list[dict]] = {}
    for row in rows:
        haendler.setdefault(row["haendler"] or "ohne Händler", []).append(row)
    blocks = []
    for name, hrows in sorted(haendler.items(), key=lambda kv: -summe(kv[1])):
        lines = [f"{name} — {euro(summe(hrows))}"]
        for r in hrows:
            menge = f"{num(r['menge'], 1):g}x " if num(r["menge"], 1) != 1 else ""
            link = f"  {r['link']}" if r["link"] else ""
            lines.append(f"  - {menge}{r['titel']} · {r['prioritaet']} · "
                         f"{euro(gesamt(r))}{link}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks) + f"\n\nSumme: {euro(summe(rows))}"


# ------------------------------------------------------------------- Markdown

def to_markdown() -> str:
    rows = load()
    PARTS_MD_DIR.mkdir(parents=True, exist_ok=True)
    for old in PARTS_MD_DIR.glob("*.md"):
        old.unlink()
    index = ["---", "typ: stückliste", "erzeugt: true", "---", "",
             "# Stückliste", "",
             "> Erzeugt aus data/parts.csv — nicht von Hand ändern.", ""]
    geschrieben = 0
    for kat in PART_KATEGORIEN:
        krows = [r for r in rows if r["kategorie"] == kat]
        if not krows:
            continue
        index.append(f"- [[{kat}]] — {len(krows)} Teile, {euro(summe(krows))}")
        lines = ["---", f"kategorie: {kat}", "erzeugt: true", "---", "",
                 f"# Stückliste — {kat}", "",
                 "> Erzeugt aus data/parts.csv — nicht von Hand ändern.", "",
                 "| Teil | Menge | Einzel | Gesamt | Status | Priorität | "
                 "Händler | Aufgabe |",
                 "|---|---|---|---|---|---|---|---|"]
        for r in sorted(krows, key=lambda r: r["titel"]):
            titel = f"[{r['titel']}]({r['link']})" if r["link"] else r["titel"]
            aufgabe = f"[[{r['fuer_aufgabe']}]]" if r["fuer_aufgabe"] else ""
            lines.append(
                f"| {titel} | {num(r['menge'], 1):g} {r['einheit']} | "
                f"{euro(num(r['preis']))} | {euro(gesamt(r))} | {r['status']} | "
                f"{r['prioritaet']} | {r['haendler']} | {aufgabe} |"
            )
        lines += ["", f"**Summe {kat}:** {euro(summe(krows))} · "
                      f"{gewicht_summe(krows):.1f} kg"]
        write_text(PARTS_MD_DIR / f"{kat}.md", "\n".join(lines))
        geschrieben += 1
    index += ["", f"**Gesamt:** {euro(summe(rows))}"]
    write_text(PARTS_MD_DIR / "Stückliste.md", "\n".join(index))
    return f"{geschrieben} Kategorieseiten + Übersicht nach vault/Stückliste/"


# ---------------------------------------------------------------------- Excel

KAT_FARBEN = {
    "Elektrik": "FFF4CE", "Wasser": "D6E9F8", "Heizung": "F8D7D3",
    "Möbel": "E2DCF0", "Küche": "D8EFD8", "Stauraum": "EDEDED",
    "Werkzeug": "FBE3F0", "Verbrauchsmaterial": "FFF0E0",
}

SPALTENBREITEN = {"id": 22, "titel": 34, "beschreibung": 40, "link": 30,
                  "notiz": 30, "kennwerte": 22, "fuer_aufgabe": 22,
                  "entscheidung": 20}


def to_excel(path: Path | None = None) -> str:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    path = path or PARTS_XLSX
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(load(), key=lambda r: (kat_index(r), r["titel"]))

    wb = Workbook()
    ws = wb.active
    ws.title = "Stückliste"
    header = FIELDS + COMPUTED
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="333A45")
        cell.alignment = Alignment(vertical="center")
    ws.freeze_panes = "C2"

    menge_col = get_column_letter(FIELDS.index("menge") + 1)
    preis_col = get_column_letter(FIELDS.index("preis") + 1)
    for i, row in enumerate(rows, start=2):
        ws.append([row.get(f, "") for f in FIELDS])
        ws.cell(row=i, column=len(header)).value = (
            f"=IFERROR(N({menge_col}{i})*N({preis_col}{i}),0)"
        )
        farbe = KAT_FARBEN.get(row.get("kategorie", ""))
        if farbe:
            for cell in ws[i]:
                cell.fill = PatternFill("solid", fgColor=farbe)

    letzte = max(ws.max_row, 2)
    for spalte, werte in (("status", PART_STATUS), ("prioritaet", PART_PRIO),
                          ("kategorie", PART_KATEGORIEN)):
        col = get_column_letter(FIELDS.index(spalte) + 1)
        dv = DataValidation(type="list",
                            formula1='"' + ",".join(werte) + '"',
                            allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{letzte + 200}")

    for i, name in enumerate(header, start=1):
        ws.column_dimensions[get_column_letter(i)].width = SPALTENBREITEN.get(name, 14)
    ws.auto_filter.ref = f"A1:{get_column_letter(len(header))}{letzte}"

    ws2 = wb.create_sheet("Summen")
    ws2.append(["Kategorie", "Teile", "Kosten", "Gewicht kg"])
    for cell in ws2[1]:
        cell.font = Font(bold=True)
    kat_col = get_column_letter(FIELDS.index("kategorie") + 1)
    ges_col = get_column_letter(len(header))
    for i, kat in enumerate(PART_KATEGORIEN, start=2):
        krows = [r for r in rows if r["kategorie"] == kat]
        ws2.append([
            kat,
            f"=COUNTIF(Stückliste!{kat_col}:{kat_col},A{i})",
            f"=SUMIF(Stückliste!{kat_col}:{kat_col},A{i},"
            f"Stückliste!{ges_col}:{ges_col})",
            round(gewicht_summe(krows), 2),
        ])
    letzte2 = ws2.max_row
    ws2.append(["Gesamt", f"=SUM(B2:B{letzte2})", f"=SUM(C2:C{letzte2})",
                f"=SUM(D2:D{letzte2})"])
    for cell in ws2[ws2.max_row]:
        cell.font = Font(bold=True)
    for col, width in zip("ABCD", (24, 10, 14, 12)):
        ws2.column_dimensions[col].width = width

    wb.save(path)
    return f"{len(rows)} Teile → {path}"


def read_excel(path: Path | None = None) -> list[dict]:
    from openpyxl import load_workbook

    path = path or PARTS_XLSX
    if not path.exists():
        fail(f"Keine Excel-Datei unter {path}. Erst 'parts excel' laufen lassen.")
    wb = load_workbook(path, data_only=False)
    ws = wb["Stückliste"] if "Stückliste" in wb.sheetnames else wb.active
    header = [str(c.value or "").strip() for c in ws[1]]
    rows = []
    for values in ws.iter_rows(min_row=2, values_only=True):
        raw = {h: values[i] for i, h in enumerate(header) if h in FIELDS}
        if not str(raw.get("titel") or "").strip():
            continue
        rows.append({f: ("" if raw.get(f) is None else str(raw.get(f, "")).strip())
                     for f in FIELDS})
    return rows


def diff(neu: list[dict], alt: list[dict] | None = None) -> dict:
    alt = load() if alt is None else alt
    alt_map = {r["id"]: r for r in alt if r["id"]}
    neu_map: dict[str, dict] = {}
    for row in neu:
        if not row["id"]:
            row["id"] = new_id(row["titel"], list(alt) + list(neu_map.values()))
        neu_map[row["id"]] = row
    geaendert = []
    for pid, row in neu_map.items():
        vorher = alt_map.get(pid)
        if not vorher:
            continue
        felder = [f for f in FIELDS if (vorher.get(f) or "") != (row.get(f) or "")]
        if felder:
            geaendert.append((row["titel"], felder, vorher, row))
    return {
        "neu": [r for pid, r in neu_map.items() if pid not in alt_map],
        "entfernt": [r for pid, r in alt_map.items() if pid not in neu_map],
        "geaendert": geaendert,
        "kosten_alt": summe(alt),
        "kosten_neu": summe(list(neu_map.values())),
        "rows": list(neu_map.values()),
    }


def diff_text(d: dict) -> str:
    lines = []
    for row in d["neu"]:
        lines.append(f"  + {row['titel']} ({row['kategorie']}, {euro(gesamt(row))})")
    for row in d["entfernt"]:
        lines.append(f"  - {row['titel']} ({row['kategorie']})")
    for titel, felder, vorher, nachher in d["geaendert"]:
        aend = ", ".join(f"{f}: {vorher.get(f) or '—'} → {nachher.get(f) or '—'}"
                         for f in felder)
        lines.append(f"  ~ {titel}: {aend}")
    if not lines:
        return "Keine Unterschiede — die Excel-Datei entspricht der CSV."
    delta = d["kosten_neu"] - d["kosten_alt"]
    kopf = (f"{len(d['geaendert'])} geändert, {len(d['neu'])} neu, "
            f"{len(d['entfernt'])} entfernt · Kosten {delta:+.2f} € "
            f"auf {euro(d['kosten_neu'])}")
    return kopf + "\n" + "\n".join(lines)


def import_excel(path: Path | None = None, apply: bool = False) -> str:
    d = diff(read_excel(path))
    text = diff_text(d)
    if not d["neu"] and not d["entfernt"] and not d["geaendert"]:
        return text
    if not apply:
        return text + "\n\nNichts geschrieben. Mit --apply übernehmen."
    save(d["rows"])
    return text + "\n\nÜbernommen nach data/parts.csv."
