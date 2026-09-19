<script lang="ts">
  // Stückliste: Filter (Status als Reiter, Kategorie/Bereich als Auswahl),
  // Suche, Kostensumme, Umschalter Liste/Raster, Anlegen, Detailfenster.
  // Vorbild inhaltlich: docs/js/teile.js. Kategorie doppelt hier als Bereich
  // (PART_KATEGORIEN deckt sich mit den Arbeitsbereichen, siehe
  // lib/bereiche/BereichDetail.svelte: t.kategorie === bereichsname).
  //
  // Mit `kategorie` gesetzt (Reiter „Teile“ im Bereich-Detail) ist die
  // Kategorie fest: die Auswahl entfällt, Neuanlagen landen im Bereich und
  // die Detail-Route läuft über 'bereiche' statt 'teile'.
  import type { TeilAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import { toasts } from '../toasts.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import TeilZeile from './TeilZeile.svelte';
  import TeilKarte from './TeilKarte.svelte';
  import TeilDetail from './TeilDetail.svelte';
  import { Auswahl, Dialog, Feld, Filterleiste, Karte, Kennzahl, Knopf, Leerzustand, Tabs } from '../ui';
  import { vokabular } from '../vokabular.svelte';
  import { dezimal } from '../zahlformat';
  import { IconEuro, IconGewicht, IconPlus, IconSuche } from '../ui/icons';
  import { euro, gesamtpreis, zahl } from './format';
  import IconListe from '@lucide/svelte/icons/list';
  import IconRaster from '@lucide/svelte/icons/layout-grid';

  type Ansicht = 'liste' | 'raster';

  function gemerkt<T extends string>(schluessel: string, standard: T): T {
    try {
      return (localStorage.getItem(schluessel) as T) || standard;
    } catch {
      return standard;
    }
  }
  function merken(schluessel: string, wert: string): void {
    try {
      localStorage.setItem(schluessel, wert);
    } catch {
      /* egal — nur Komfort */
    }
  }

  let { kategorie }: { kategorie?: string } = $props();

  let ansicht = $state<Ansicht>(gemerkt('teileAnsicht', 'liste'));
  let filterStatus = $state(gemerkt<string>('teileFilterStatus', ''));
  let filterKategorie = $state('');
  const wirksameKategorie = $derived(kategorie || filterKategorie);
  let sortierung = $state(gemerkt<string>('teileSortierung', 'titel'));
  let suche = $state('');
  let formOffen = $state(false);
  let offenId = $state<string | null>(null);

  // Eingebettet trägt die Adresse den Bereich, nicht das Teil — dann bleibt
  // das Detail reiner Zustand, sonst folgt es der Route.
  $effect(() => {
    if (kategorie || router.route.ansicht !== 'teile') return;
    const idAusRoute = router.route.parameter[0] ?? null;
    if (idAusRoute !== offenId) offenId = idAusRoute;
  });

  function oeffnen(id: string): void {
    if (kategorie) offenId = id;
    else router.gehe('teile', id);
  }
  function schliessen(): void {
    if (kategorie) offenId = null;
    else router.gehe('teile');
  }

  function ansichtWaehlen(a: Ansicht): void {
    ansicht = a;
    merken('teileAnsicht', a);
  }
  function statusWaehlen(s: string): void {
    filterStatus = s;
    merken('teileFilterStatus', s);
  }
  function sortierungWaehlen(s: string): void {
    sortierung = s;
    merken('teileSortierung', s);
  }

  // Ein „Status-Alter" gibt es nicht: die CSV führt keinen Zeitpunkt des
  // letzten Statuswechsels (nur `gekauft_am`). Sortiert wird deshalb nach
  // dem, was wirklich in den Daten steht.
  const SORTIER_OPTIONEN = [
    { wert: 'titel', label: 'Titel A–Z' },
    { wert: 'preis-ab', label: 'Preis, teuerste zuerst' },
    { wert: 'preis-auf', label: 'Preis, günstigste zuerst' },
    { wert: 'prio', label: 'Priorität' },
    { wert: 'status', label: 'Status' },
    { wert: 'gekauft', label: 'zuletzt gekauft' },
  ];

  function reihung(a: TeilAntwort, b: TeilAntwort): number {
    switch (sortierung) {
      case 'preis-ab':
        return gesamtpreis(b) - gesamtpreis(a) || a.titel.localeCompare(b.titel, 'de');
      case 'preis-auf': {
        // Ohne Preis heißt unbekannt, nicht billig — die kommen ans Ende.
        const p = (t: TeilAntwort) => gesamtpreis(t) || Infinity;
        return p(a) - p(b) || a.titel.localeCompare(b.titel, 'de');
      }
      case 'prio': {
        const reihe = vokabular.teilPrio;
        const i = (t: TeilAntwort) => {
          const n = reihe.indexOf(t.prioritaet);
          return n < 0 ? reihe.length : n;
        };
        return i(a) - i(b) || a.titel.localeCompare(b.titel, 'de');
      }
      case 'status': {
        const reihe = vokabular.teilStatus;
        const i = (t: TeilAntwort) => {
          const n = reihe.indexOf(t.status);
          return n < 0 ? reihe.length : n;
        };
        return i(a) - i(b) || a.titel.localeCompare(b.titel, 'de');
      }
      case 'gekauft':
        // Ohne Datum nach hinten, sonst das jüngste zuerst.
        return (b.gekauft_am || '').localeCompare(a.gekauft_am || '') ||
          a.titel.localeCompare(b.titel, 'de');
      default:
        return a.titel.localeCompare(b.titel, 'de');
    }
  }

  const alleTeile = $derived(store.daten?.teile ?? []);

  const kategorien = $derived([...new Set(alleTeile.map((t) => t.kategorie).filter(Boolean))].sort());

  // Im Bereich zählen die Reiter nur die Teile dieses Bereichs.
  const imBereich = $derived(kategorie ? alleTeile.filter((t) => t.kategorie === kategorie) : alleTeile);
  const statusVorhanden = $derived([...new Set(imBereich.map((t) => t.status).filter(Boolean))]);
  const statusReihenfolge = $derived(vokabular.teilStatus.filter((s) => statusVorhanden.includes(s)));
  const statusTabs = $derived([
    { id: '', label: 'alle', zahl: imBereich.length },
    ...statusReihenfolge.map((s) => ({ id: s, label: s, zahl: imBereich.filter((t) => t.status === s).length })),
  ]);

  const suchtext = $derived(suche.trim().toLowerCase());
  function passtSuche(t: TeilAntwort): boolean {
    if (!suchtext) return true;
    const heuhaufen = `${t.titel} ${t.beschreibung} ${t.kennwerte} ${t.haendler} ${t.notiz}`.toLowerCase();
    return heuhaufen.includes(suchtext);
  }

  // Kopie sortieren, nie die Liste aus dem Store.
  const gefiltert = $derived(
    [
      ...alleTeile.filter(
        (t) =>
          (!wirksameKategorie || t.kategorie === wirksameKategorie) &&
          (!filterStatus || t.status === filterStatus) &&
          passtSuche(t),
      ),
    ].sort(reihung),
  );

  const summe = $derived(gefiltert.reduce((s, t) => s + gesamtpreis(t), 0));
  const gewicht = $derived(gefiltert.reduce((s, t) => s + zahl(t.gewicht_kg), 0));
  const ohnePreis = $derived(gefiltert.filter((t) => !zahl(t.preis)).length);

  const teilAnlegenErlaubt = $derived(!!store.daten?.bearbeitbar?.teil_anlegen);
  const teilLoeschenErlaubt = $derived(!!store.daten?.bearbeitbar?.teil_loeschen);

  // ------------------------------------------------------------- Anlegen

  let neuTitel = $state('');
  let neuKategorie = $state('');
  let neuMenge = $state('1');
  let neuEinheit = $state('Stk');
  let neuPreis = $state('');
  let neuHaendler = $state('');
  let neuLink = $state('');

  $effect(() => {
    if (kategorie) neuKategorie = kategorie;
    else if (!neuKategorie && kategorien.length) neuKategorie = kategorien[0];
  });

  function formOeffnen(): void {
    formOffen = true;
    neuTitel = '';
    neuMenge = '1';
    neuEinheit = 'Stk';
    neuPreis = '';
    neuHaendler = '';
    neuLink = '';
  }
  function formAbbrechen(): void {
    formOffen = false;
  }
  async function anlegen(): Promise<void> {
    const titel = neuTitel.trim();
    if (!titel) {
      toasts.fehler('Titel fehlt.');
      return;
    }
    const id = await store.teilAnlegen({
      titel,
      kategorie: neuKategorie,
      menge: neuMenge || '1',
      einheit: neuEinheit,
      preis: neuPreis,
      haendler: neuHaendler,
      link: neuLink,
      status: 'Idee',
    });
    if (id) {
      formOffen = false;
      toasts.info(`„${titel}“ angelegt.`);
    }
  }

  const offenesTeil = $derived(offenId ? alleTeile.find((t) => t.id === offenId) : undefined);
</script>

<div class="kennzahlen">
  <Kennzahl titel="Teile" wert={gefiltert.length} zusatz={gefiltert.length !== alleTeile.length ? `von ${alleTeile.length}` : undefined} />
  <Kennzahl titel="Kosten" wert={euro.format(summe)} icon={IconEuro} />
  {#if gewicht}<Kennzahl titel="Gewicht" wert="{dezimal(gewicht)} kg" icon={IconGewicht} />{/if}
  {#if ohnePreis}<Kennzahl titel="Ohne Preis" wert={ohnePreis} ton="warn" />{/if}
</div>

<Filterleiste>
  {#snippet reiter()}
    <Tabs tabs={statusTabs} aktiv={filterStatus} onwechsel={statusWaehlen} label="Status" />
  {/snippet}
    <Feld
      bind:wert={suche}
      placeholder="Suche in Titel, Beschreibung, Notiz…"
      aria-label="Teile durchsuchen"
      icon={IconSuche}
      type="search"
      klein
    />
    {#if !kategorie}
    <Auswahl
      class="filter-wahl"
      wert={filterKategorie}
      optionen={kategorien}
      leer="alle Kategorien"
      onchange={(e) => (filterKategorie = (e.target as HTMLSelectElement).value)}
      aria-label="Kategorie/Bereich filtern"
      klein
    />
    {/if}
    <Auswahl
      class="filter-wahl"
      wert={sortierung}
      optionen={SORTIER_OPTIONEN}
      onchange={(e) => sortierungWaehlen((e.target as HTMLSelectElement).value)}
      aria-label="Sortierung"
      klein
    />
    <div class="ansicht-wahl" role="group" aria-label="Ansicht">
      <button type="button" class:aktiv={ansicht === 'liste'} onclick={() => ansichtWaehlen('liste')} aria-label="Liste" title="Liste">
        <IconListe size={15} strokeWidth={1.8} aria-hidden="true" />
      </button>
      <button type="button" class:aktiv={ansicht === 'raster'} onclick={() => ansichtWaehlen('raster')} aria-label="Raster" title="Raster">
        <IconRaster size={15} strokeWidth={1.8} aria-hidden="true" />
      </button>
    </div>
    {#if teilAnlegenErlaubt}
      <Schreibbar>
        {#snippet children()}
          <Knopf variante="primaer" groesse="s" icon={IconPlus} onclick={formOeffnen}>Teil</Knopf>
        {/snippet}
      </Schreibbar>
    {/if}
</Filterleiste>

<Dialog bind:offen={formOffen} titel="Teil anlegen">
  <Feld label="Titel" bind:wert={neuTitel} placeholder="Was wird gekauft?" />
  {#if !kategorie}
    <Auswahl label="Kategorie" bind:wert={neuKategorie} optionen={kategorien} />
  {/if}
  <div class="form-zeile">
    <Feld label="Menge" bind:wert={neuMenge} mono />
    <Feld label="Einheit" bind:wert={neuEinheit} />
    <Feld label="Preis / Stk" bind:wert={neuPreis} einheit="€" mono optional />
  </div>
  <Feld label="Händler" bind:wert={neuHaendler} optional />
  <Feld label="Link" type="url" bind:wert={neuLink} optional />
  {#snippet fuss()}
    <Knopf variante="leise" onclick={formAbbrechen}>Abbrechen</Knopf>
    <Knopf variante="primaer" onclick={anlegen} laedt={store.beschaeftigt}>Anlegen</Knopf>
  {/snippet}
</Dialog>

{#if !gefiltert.length}
  <Leerzustand titel="Kein Teil passt zum Filter" text="Filter lockern oder die Suche anpassen." />
{:else if ansicht === 'liste'}
  <Karte polster="keins">
    <ul class="teilliste">
      {#each gefiltert as t (t.id)}
        <TeilZeile {t} onOeffnen={oeffnen} />
      {/each}
    </ul>
  </Karte>
{:else}
  <div class="teilgitter">
    {#each gefiltert as t (t.id)}
      <TeilKarte {t} onOeffnen={oeffnen} />
    {/each}
  </div>
{/if}

{#if offenesTeil}
  <TeilDetail t={offenesTeil} onClose={schliessen} loeschenErlaubt={teilLoeschenErlaubt} />
{/if}

<style>
  .kennzahlen {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-5);
    margin-bottom: var(--a-5);
  }

  .ansicht-wahl {
    display: flex;
    border: 1px solid var(--farbe-linie-stark);
    border-radius: var(--r-m);
    overflow: hidden;
  }
  .ansicht-wahl button {
    display: grid;
    place-items: center;
    width: 30px;
    height: 30px;
    border: 0;
    background: var(--farbe-flaeche);
    color: var(--farbe-text-2);
    cursor: pointer;
  }
  .ansicht-wahl button + button {
    border-left: 1px solid var(--farbe-linie-stark);
  }
  .ansicht-wahl button:hover {
    color: var(--farbe-text);
  }
  .ansicht-wahl button.aktiv {
    background: var(--farbe-tinte-fuellung);
    color: var(--farbe-auf-tinte);
  }

  .form-zeile {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: var(--a-3);
  }

  ul.teilliste {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .teilgitter {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: var(--a-3);
  }
</style>
