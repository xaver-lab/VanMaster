// erzeugt — nicht von Hand ändern, neu mit `python -m tools.server.schema`
// Quelle: tools/server/modelle.py (JSON-Schema der Pydantic-Modelle)

export interface AblaufAntwort {
  stufen?: AblaufStufeAntwort[];
  tiefe: number;
  offen_gesamt: number;
  schluessel?: AblaufAufgabeAntwort[];
  ring?: AblaufAufgabeAntwort[];
}

export interface AblaufAufgabeAntwort {
  id: string;
  titel: string;
  bereich: string;
  status: string;
  prio?: string;
  dauer?: string;
  braucht?: string[];
  haelt_auf?: number;
}

export interface AblaufStufeAntwort {
  stufe: number;
  aufgaben?: AblaufAufgabeAntwort[];
}

export interface AbschnittAnfrage {
  text: string;
  version: string;
}

export interface AbschnittAntwort {
  name: string;
  text: string;
  zeile_von: number;
  zeile_bis: number;
}

export interface AufgabeAnlegenAnfrage {
  bereich: string;
  titel: string;
  version: string;
  status?: string;
  beschreibung?: string;
  prio?: string;
  gruppe?: string | null;
  eltern_id?: string | null;
}

export interface AufgabeAntwort {
  id: string;
  titel: string;
  status: string;
  bereich: string;
  gruppe?: string;
  ebene?: number;
  eltern?: string;
  kinder?: string[];
  braucht?: string[];
  prio?: string;
  dauer?: string;
  beschreibung?: string;
  datei?: string;
  zeile?: number;
}

export interface AufgabePatchAnfrage {
  version: string;
  status?: string | null;
  titel?: string | null;
  beschreibung?: string | null;
  prio?: string | null;
}

export interface BereichAntwort {
  name: string;
  kurz: string;
  status: string;
  phase: number | null;
  datei: string;
  abschnitte?: Record<string, AbschnittAntwort>;
  aufgaben?: AufgabeAntwort[];
}

export interface BudgetAntwort {
  ziel?: number | null;
  bezahlt: number;
  geplant: number;
  prognose: number;
  rest?: number | null;
  differenz_prognose?: number | null;
  kategorien?: BudgetKategorieAntwort[];
}

export interface BudgetKategorieAntwort {
  kategorie: string;
  bezahlt: number;
  geplant: number;
  prognose: number;
  budget?: number | null;
}

export interface DatenAntwort {
  erzeugt: string;
  bereiche: BereichAntwort[];
  aufgaben: AufgabeAntwort[];
  querverweise: QuerverweisAntwort[];
  entscheidungen: SeiteAntwort[];
  anleitungen: SeiteAntwort[];
  recherche: SeiteAntwort[];
  teile: TeilAntwort[];
  einzelteile: EinzelteilAntwort[];
  medien: MediumAntwort[];
  versionen: Record<string, string>;
  kennzahlen: KennzahlenAntwort;
  kategorien: KategorieAntwort[];
  budget: BudgetAntwort;
  gewicht: GewichtAntwort;
  material: MaterialGruppeAntwort[];
  einkauf: EinkaufAntwort;
  ablauf: AblaufAntwort;
  bearbeitbar: Record<string, any>;
  vokabular: Record<string, string[]>;
}

export interface EinkaufAntwort {
  gruppen?: EinkaufGruppeAntwort[];
  teile_gesamt: number;
  summe: number;
}

export interface EinkaufGruppeAntwort {
  haendler: string;
  summe: number;
  teile?: string[];
}

export interface EinzelteilAnlegenAnfrage {
  felder: Record<string, any>;
  version: string;
}

export interface EinzelteilAntwort {
  id: string;
  titel: string;
  bereich: string;
  art: string;
  material: string;
  laenge_mm: string;
  breite_mm: string;
  dicke_mm: string;
  anzahl: string;
  teil_id: string;
  fuer_aufgabe: string;
  massquelle: string;
  status: string;
  notiz: string;
  zeile?: number;
}

export interface EinzelteilPatchAnfrage {
  feld: string;
  wert: string;
  version: string;
}

export interface FehlerAntwort {
  fehler: string;
}

export interface GewichtAntwort {
  teile_kg: number;
  teile_fehlt: number;
  teile_gesamt: number;
  bauteile_kg: number;
  bauteile_fehlt: number;
  bauteile_gesamt: number;
  ausbau_kg: number;
  leergewicht_kg?: number | null;
  zul_gesamtgewicht_kg?: number | null;
  zuladung_erlaubt_kg?: number | null;
}

export interface KategorieAntwort {
  name: string;
  teile: number;
  kosten: number;
  gewicht: number;
  verbaut: number;
}

export interface KennzahlenAntwort {
  aufgaben_fertig: number;
  aufgaben_gesamt: number;
  teile: number;
  kosten: number;
  kosten_bestellt: number;
  gewicht: number;
  offene_entscheidungen: number;
  bauteile: number;
}

export interface KonfliktAntwort {
  fehler: string;
  datei: string;
  version_aktuell: string;
  stand?: any;
}

export interface KopfAnfrage {
  feld: string;
  wert: any;
  version: string;
}

export interface MaterialGruppeAntwort {
  material: string;
  dicke_mm?: string;
  bedarf: string;
  zuschnitte?: string[];
}

export interface MediumAntwort {
  name: string;
  dateiname: string;
  bereich: string;
  art: string;
  datei: string;
  groesse?: number;
}

export interface QuerverweisAntwort {
  ziel: string;
  anzeigetext: string;
  datei: string;
  zeile: number;
  ziel_typ?: string | null;
  ziel_id?: string | null;
}

export interface SchreibErfolg {
  ok?: boolean;
  version: string;
  datei: string;
  id?: string | null;
}

export interface SeiteAntwort {
  titel: string;
  typ: string;
  status: string;
  bereich: string;
  datei: string;
  abschnitte?: Record<string, AbschnittAntwort>;
  text?: string;
}

export interface TeilAnlegenAnfrage {
  felder: Record<string, any>;
  version: string;
}

export interface TeilAntwort {
  id: string;
  titel: string;
  beschreibung: string;
  kategorie: string;
  menge: string;
  einheit: string;
  preis: string;
  status: string;
  prioritaet: string;
  link: string;
  haendler: string;
  fuer_aufgabe: string;
  entscheidung: string;
  kennwerte: string;
  gewicht_kg: string;
  notiz: string;
  gekauft_am: string;
  zeile?: number;
}

export interface TeilPatchAnfrage {
  feld: string;
  wert: string;
  version: string;
}
