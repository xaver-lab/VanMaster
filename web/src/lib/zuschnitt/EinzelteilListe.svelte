<script lang="ts">
  // Einzelteilliste (data/bauteile.csv): Bretter, Leisten, Zuschnitte mit
  // Maßen in mm — was aus den gekauften Teilen (parts.csv) gebaut wird.
  // Filter nach Bereich/Material, Suche, Gruppierung nach Bereich, Anlegen,
  // Detailfenster. Aufbau nach dem Muster von lib/aufgaben/AufgabenListe:
  // mit `bereich` gesetzt (Reiter „Zuschnitt“ im Bereich-Detail) ist die
  // Liste auf den Bereich vorgefiltert und die Bereichsauswahl entfällt.
  import { untrack } from 'svelte';
  import type { EinzelteilAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { toasts } from '../toasts.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import EinzelteilZeile from './EinzelteilZeile.svelte';
  import EinzelteilDetail from './EinzelteilDetail.svelte';
  import { Auswahl, Dialog, Feld, Karte, Kennzahl, Knopf, Leerzustand } from '../ui';
  import { vokabular } from '../vokabular.svelte';
  import { dezimal } from '../zahlformat';
  import { IconPlus, IconSuche, IconZuschnitt } from '../ui/icons';
  import { flaeche, laufmeter, zahl } from './mass';

  let { bereich }: { bereich?: string } = $props();

  let bereichFilter = $state('');
  let materialFilter = $state('');
  type Gruppierung = 'bereich' | 'material' | 'art';
  const GRUPPIER_OPTIONEN = $derived(
    bereich
      ? [
          { wert: 'material', label: 'nach Material' },
          { wert: 'art', label: 'nach Art' },
        ]
      : [
          { wert: 'bereich', label: 'nach Bereich' },
          { wert: 'material', label: 'nach Material' },
          { wert: 'art', label: 'nach Art' },
        ],
  );
  let gruppierung = $state<Gruppierung>(untrack(() => gemerkteGruppierung(bereich)));
  function gemerkteGruppierung(vorBereich?: string): Gruppierung {
    if (vorBereich) return 'material';
    try {
      const g = localStorage.getItem('zuschnittGruppierung');
      return g === 'material' || g === 'art' ? g : 'bereich';
    } catch {
      return 'bereich';
    }
  }
  $effect(() => {
    if (bereich) return;
    try {
      localStorage.setItem('zuschnittGruppierung', gruppierung);
    } catch {
      /* nur Komfort */
    }
  });
  let suche = $state('');
  let offenId = $state<string | null>(null);
  let formOffen = $state(false);

  const alleEinzelteile = $derived(store.daten?.einzelteile ?? []);
  const einzelteileImBereich = $derived(
    bereich ? alleEinzelteile.filter((e) => e.bereich === bereich) : alleEinzelteile,
  );
  const teile = $derived(store.daten?.teile ?? []);
  const teileNachId = $derived(new Map(teile.map((t) => [t.id, t] as const)));
  const nachId = $derived(new Map(alleEinzelteile.map((e) => [e.id, e] as const)));
  const bereiche = $derived(store.daten?.bereiche.map((b) => b.name) ?? []);
  const anlegenErlaubt = $derived(!!store.daten?.bearbeitbar?.einzelteil_anlegen);

  const wirksamerBereich = $derived(bereich || bereichFilter);

  // Materialliste folgt dem Bereichsfilter; ein nicht mehr passendes
  // Material fällt aus dem Filter.
  const materialien = $derived.by(() => {
    const imBereich = alleEinzelteile.filter((e) => !wirksamerBereich || e.bereich === wirksamerBereich);
    const menge = new Set(imBereich.map((e) => e.material).filter((m): m is string => !!m));
    return [...menge].sort((a, b) => a.localeCompare(b, 'de'));
  });

  $effect(() => {
    if (materialFilter && !materialien.includes(materialFilter)) materialFilter = '';
  });

  const suchtext = $derived(suche.trim().toLowerCase());
  function passtSuche(e: EinzelteilAntwort): boolean {
    if (!suchtext) return true;
    const heuhaufen = `${e.titel} ${e.bereich} ${e.art} ${e.material} ${e.notiz}`.toLowerCase();
    return heuhaufen.includes(suchtext);
  }

  const gefiltert = $derived(
    alleEinzelteile
      .filter((e) => !wirksamerBereich || e.bereich === wirksamerBereich)
      .filter((e) => !materialFilter || e.material === materialFilter)
      .filter(passtSuche),
  );

  interface Gruppe {
    name: string;
    eintraege: EinzelteilAntwort[];
  }
  const gruppen = $derived.by((): Gruppe[] => {
    const eimer = new Map<string, EinzelteilAntwort[]>();
    const schluessel = (e: EinzelteilAntwort): string =>
      gruppierung === 'material' ? e.material || 'Ohne Material'
      : gruppierung === 'art' ? e.art || 'Ohne Art'
      : e.bereich || 'Ohne Bereich';
    for (const e of gefiltert) {
      const name = schluessel(e);
      if (!eimer.has(name)) eimer.set(name, []);
      eimer.get(name)!.push(e);
    }
    const reihenfolge = gruppierung === 'bereich' ? bereiche : gruppierung === 'art' ? vokabular.einzelteilArt : [];
    const namen = [...eimer.keys()].sort(
      (a, b) =>
        (reihenfolge.indexOf(a) + 1 || 999) - (reihenfolge.indexOf(b) + 1 || 999) || a.localeCompare(b, 'de'),
    );
    return namen.map((name) => ({ name, eintraege: eimer.get(name)! }));
  });

  const summeFlaeche = $derived(gefiltert.reduce((s, e) => s + flaeche(e), 0));
  const summeStueck = $derived(gefiltert.reduce((s, e) => s + zahl(e.anzahl, 1), 0));
  const summeLaufmeter = $derived(gefiltert.reduce((s, e) => s + laufmeter(e), 0));

  function oeffnen(id: string): void {
    offenId = id;
  }
  function schliessen(): void {
    offenId = null;
  }

  // -------------------------------------------------------------- Anlegen

  let neuTitel = $state('');
  let neuBereich = $state('');
  let neuArt = $state('');
  let neuMaterial = $state('');
  let neuLaenge = $state('');
  let neuBreite = $state('');
  let neuDicke = $state('');
  let neuAnzahl = $state('1');
  let neuTeil = $state('');

  $effect(() => {
    if (bereich) neuBereich = bereich;
    else if (!neuBereich && bereiche.length) neuBereich = bereiche[0];
  });

  function formOeffnen(): void {
    neuTitel = '';
    neuArt = '';
    neuMaterial = '';
    neuLaenge = '';
    neuBreite = '';
    neuDicke = '';
    neuAnzahl = '1';
    neuTeil = '';
    formOffen = true;
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
    if (!neuBereich) {
      toasts.fehler('Bereich fehlt.');
      return;
    }
    const id = await store.einzelteilAnlegen({
      titel,
      bereich: neuBereich,
      art: neuArt,
      material: neuMaterial,
      laenge_mm: neuLaenge,
      breite_mm: neuBreite,
      dicke_mm: neuDicke,
      anzahl: neuAnzahl || '1',
      teil_id: neuTeil,
    });
    if (id) {
      formOffen = false;
      toasts.info(`„${titel}“ angelegt.`);
    }
  }
</script>

<div class="kennzahlen">
  <Kennzahl titel="Einzelteile" wert={summeStueck} zusatz="{gefiltert.length} Zeilen" icon={IconZuschnitt} />
  {#if summeFlaeche}<Kennzahl titel="Fläche" wert="{dezimal(summeFlaeche, 2)} m²" />{/if}
  {#if summeLaufmeter}<Kennzahl titel="Laufmeter" wert="{dezimal(summeLaufmeter, 2)} lfm" />{/if}
</div>

<div class="leiste">
  <Feld
    bind:wert={suche}
    placeholder="Suche in Titel, Material, Notiz…"
    aria-label="Einzelteile durchsuchen"
    icon={IconSuche}
    type="search"
    klein
  />
  {#if !bereich}
    <Auswahl
      class="bereich-wahl"
      bind:wert={bereichFilter}
      optionen={bereiche}
      leer="alle Bereiche"
      aria-label="Bereich filtern"
      klein
    />
  {/if}
  <Auswahl
    class="material-wahl"
    bind:wert={materialFilter}
    optionen={materialien}
    leer="alle Materialien"
    aria-label="Material filtern"
    klein
  />
  <Auswahl bind:wert={gruppierung} optionen={GRUPPIER_OPTIONEN} aria-label="Gruppierung" klein />
  {#if anlegenErlaubt}
    <Schreibbar>
      {#snippet children()}
        <Knopf variante="primaer" groesse="s" icon={IconPlus} onclick={formOeffnen}>Einzelteil</Knopf>
      {/snippet}
    </Schreibbar>
  {/if}
</div>

<Dialog bind:offen={formOffen} titel="Einzelteil anlegen" beschreibung="Wird in bauteile.csv eingetragen.">
  <Feld label="Titel" bind:wert={neuTitel} placeholder="z. B. Bettrahmen Seite links" />
  <div class="zwei">
    {#if bereich}
      <Feld label="Bereich" wert={bereich} readonly mono />
    {:else}
      <Auswahl label="Bereich" bind:wert={neuBereich} optionen={bereiche} />
    {/if}
    <Auswahl label="Art" bind:wert={neuArt} optionen={vokabular.einzelteilArt} leer="—" />
  </div>
  <Feld label="Material" bind:wert={neuMaterial} optional placeholder="z. B. Siebdruckplatte 15 mm" />
  <div class="drei">
    <Feld label="Länge" type="number" mono einheit="mm" bind:wert={neuLaenge} />
    <Feld label="Breite" type="number" mono einheit="mm" bind:wert={neuBreite} />
    <Feld label="Dicke" type="number" mono einheit="mm" bind:wert={neuDicke} />
  </div>
  <div class="zwei">
    <Feld label="Anzahl" type="number" mono bind:wert={neuAnzahl} />
    <Auswahl
      label="Aus Teil"
      bind:wert={neuTeil}
      optionen={teile.map((t) => ({ wert: t.id, label: t.titel }))}
      leer="— kein Bezug —"
    />
  </div>
  {#snippet fuss()}
    <Knopf variante="leise" onclick={formAbbrechen}>Abbrechen</Knopf>
    <Knopf variante="primaer" onclick={anlegen} laedt={store.beschaeftigt}>Anlegen</Knopf>
  {/snippet}
</Dialog>

{#if !gefiltert.length}
  <Leerzustand
    icon={IconZuschnitt}
    titel={einzelteileImBereich.length ? 'Kein Einzelteil passt zum Filter' : 'Noch keine Einzelteile'}
    text={einzelteileImBereich.length
      ? 'Filter lockern oder die Suche anpassen.'
      : 'Bretter, Leisten und Platten mit Maßen in mm — was aus den gekauften Teilen gebaut wird.'}
  >
    {#if anlegenErlaubt}
      <Schreibbar>
        {#snippet children()}
          <Knopf variante="primaer" groesse="s" icon={IconPlus} onclick={formOeffnen}>Einzelteil anlegen</Knopf>
        {/snippet}
      </Schreibbar>
    {/if}
  </Leerzustand>
{:else}
  {#each gruppen as g (g.name)}
    <details class="sammelblock" open>
      <summary>
        <span class="name">{g.name}</span>
        <span class="zahl">{g.eintraege.length}</span>
      </summary>
      <Karte polster="keins">
        <ul class="einzelteile">
          {#each g.eintraege as e (e.id)}
            <EinzelteilZeile {e} mitBereich={!wirksamerBereich} {teileNachId} onOeffnen={oeffnen} />
          {/each}
        </ul>
      </Karte>
    </details>
  {/each}
{/if}

{#if offenId && nachId.get(offenId)}
  <EinzelteilDetail e={nachId.get(offenId)!} {teile} {bereiche} onClose={schliessen} />
{/if}

<style>
  .kennzahlen {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-6);
    margin-bottom: var(--a-5);
  }

  .leiste {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
    margin-bottom: var(--a-5);
  }
  .leiste :global(.ui-feld) {
    width: 15rem;
  }
  :global(.bereich-wahl),
  :global(.material-wahl) {
    width: 11rem;
    flex: none;
  }
  .leiste :global(.ui-knopf) {
    margin-left: auto;
  }

  .zwei {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--a-3);
  }
  .drei {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--a-3);
  }

  ul.einzelteile {
    list-style: none;
    margin: 0;
    padding: var(--a-2);
  }

  .sammelblock {
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie);
    border-radius: var(--r-l);
    margin-bottom: var(--a-2);
    overflow: hidden;
  }
  .sammelblock > summary {
    list-style: none;
    display: flex;
    align-items: center;
    gap: var(--a-3);
    padding: var(--a-3) var(--a-4);
    cursor: pointer;
  }
  .sammelblock > summary::-webkit-details-marker {
    display: none;
  }
  .sammelblock > summary::before {
    content: '▸';
    color: var(--farbe-text-2);
    font-size: var(--text-s);
    transition: transform var(--t-kurz);
  }
  .sammelblock[open] > summary::before {
    transform: rotate(90deg);
  }
  .sammelblock > summary .name {
    font-weight: 650;
  }
  .sammelblock > summary .zahl {
    font-family: var(--schrift-mono);
    font-size: var(--text-xs);
    color: var(--farbe-text-2);
  }
  .sammelblock > :global(.ui-karte) {
    border: 0;
    border-top: 1px solid var(--farbe-linie);
    border-radius: 0;
    box-shadow: none;
  }
</style>
