<script lang="ts">
  // Wiederverwendbare Aufgabenliste: Filter (Tabs), Gruppierung, Suche,
  // Anlegen, Detailfenster. Die Ansicht Aufgaben.svelte bettet sie ohne
  // Bereichs-Einschränkung ein; die Bereichsansicht (anderer Agent) mit
  // `bereich` gesetzt.
  import type { AufgabeAntwort } from '../api-typen';
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import { toasts } from '../toasts.svelte';
  import Schreibbar from '../Schreibbar.svelte';
  import AufgabeZeile from './AufgabeZeile.svelte';
  import AufgabeDetail from './AufgabeDetail.svelte';
  import {
    Auswahl,
    Chip,
    Dialog,
    Feld,
    FortschrittBalken,
    Karte,
    Knopf,
    Leerzustand,
    Rubrik,
    Tabs,
  } from '../ui';
  import { IconPlus, IconSuche } from '../ui/icons';

  let {
    bereich,
    anlegenErlaubt = true,
  }: {
    bereich?: string;
    anlegenErlaubt?: boolean;
  } = $props();

  const STATUS_WORT: Record<string, string> = {
    offen: 'offen',
    laeuft: 'in Arbeit',
    blockiert: 'blockiert',
    erledigt: 'abgeschlossen',
    alle: 'alle',
  };
  type Filter = 'offen' | 'laeuft' | 'blockiert' | 'erledigt' | 'alle';
  const FILTER: Filter[] = ['offen', 'laeuft', 'blockiert', 'erledigt', 'alle'];
  const RANG: Record<string, number> = { kritisch: 0, hoch: 1, mittel: 2, nice: 3 };
  const PRIO_OPTIONEN = ['kritisch', 'hoch', 'mittel', 'nice'];
  type Gruppierung = 'bereich' | 'status' | 'prio' | 'flach';

  function gemerkt<T extends string>(schluessel: string, standard: T): T {
    try {
      const wert = localStorage.getItem(schluessel);
      return (wert as T) || standard;
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

  let filter = $state<Filter>(gemerkt('aufgabenFilter', 'offen'));
  let gruppierung = $state<Gruppierung>(gemerkt('aufgabenGruppierung', bereich ? 'status' : 'bereich'));
  let suche = $state('');
  let formOffen = $state(false);
  let offenId = $state<string | null>(null);

  // Top-Ansicht (kein `bereich`-Prop = die eigenständige Aufgaben-Route):
  // geöffnete Aufgabe mit dem Hash synchron halten, damit sie verlinkbar
  // bleibt (#/aufgaben/<id>).
  const istTopRoute = !bereich;
  $effect(() => {
    if (!istTopRoute) return;
    if (router.route.ansicht !== 'aufgaben') return;
    const idAusRoute = router.route.parameter[0] ?? null;
    if (idAusRoute !== offenId) offenId = idAusRoute;
  });

  function oeffnen(id: string): void {
    if (istTopRoute) {
      router.gehe('aufgaben', id);
    } else {
      offenId = id;
    }
  }
  function schliessen(): void {
    if (istTopRoute) {
      router.gehe('aufgaben');
    } else {
      offenId = null;
    }
  }

  function filterWaehlen(f: string): void {
    filter = f as Filter;
    merken('aufgabenFilter', f);
  }
  function gruppierungWaehlen(g: string): void {
    gruppierung = g as Gruppierung;
    merken('aufgabenGruppierung', g);
  }

  const alleAufgaben = $derived(store.daten?.aufgaben ?? []);
  const nachId = $derived(new Map(alleAufgaben.map((a) => [a.id, a] as const)));
  const imBereich = $derived(bereich ? alleAufgaben.filter((a) => a.bereich === bereich) : alleAufgaben);
  const blaetter = $derived(imBereich.filter((a) => !a.kinder?.length));

  const zahlen = $derived({
    offen: blaetter.filter((a) => a.status === 'offen').length,
    laeuft: blaetter.filter((a) => a.status === 'laeuft').length,
    blockiert: blaetter.filter((a) => a.status === 'blockiert').length,
    erledigt: blaetter.filter((a) => a.status === 'erledigt').length,
    alle: blaetter.length,
  });

  const filterTabs = $derived(FILTER.map((f) => ({ id: f, label: STATUS_WORT[f], zahl: zahlen[f] })));

  const gruppierOptionen = $derived([
    ...(bereich ? [] : [{ wert: 'bereich', label: 'nach Thema' }]),
    { wert: 'status', label: 'nach Status' },
    { wert: 'prio', label: 'nach Priorität' },
    { wert: 'flach', label: 'keine Gruppierung' },
  ]);

  const suchtext = $derived(suche.trim().toLowerCase());
  function passtSuche(a: AufgabeAntwort): boolean {
    if (!suchtext) return true;
    const heuhaufen = `${a.titel} ${a.bereich} ${a.gruppe ?? ''} ${a.beschreibung ?? ''}`.toLowerCase();
    return heuhaufen.includes(suchtext);
  }

  const gefiltert = $derived.by(() => {
    const basis = imBereich.filter(passtSuche);
    if (filter === 'alle') return basis;
    return basis.filter((a) => !a.kinder?.length && a.status === filter);
  });

  interface Gruppe {
    name: string;
    anzeigename: string;
    eintraege: AufgabeAntwort[];
    alle: AufgabeAntwort[];
  }

  const gruppen = $derived.by((): Gruppe[] => {
    if (!gefiltert.length) return [];
    if (gruppierung === 'flach') {
      const sortiert = [...gefiltert].sort((a, b) => (RANG[a.prio ?? ''] ?? 2) - (RANG[b.prio ?? ''] ?? 2));
      return [{ name: '__alle__', anzeigename: 'Alle Treffer', eintraege: sortiert, alle: sortiert }];
    }
    const eigeneGruppe = gruppierung === 'prio' || gruppierung === 'status';
    const schluessel = (a: AufgabeAntwort): string =>
      gruppierung === 'prio' ? a.prio || 'mittel' : gruppierung === 'status' ? a.status : a.bereich || 'Ohne Thema';
    const reihenfolge =
      gruppierung === 'prio'
        ? ['kritisch', 'hoch', 'mittel', 'nice']
        : gruppierung === 'status'
          ? ['laeuft', 'blockiert', 'offen', 'erledigt', 'verworfen']
          : (store.daten?.bereiche.map((b) => b.name) ?? []);
    const anzeigename = (s: string): string => (gruppierung === 'status' ? STATUS_WORT[s] || s : s);

    const eimer = new Map<string, AufgabeAntwort[]>();
    for (const a of gefiltert) {
      const s = schluessel(a);
      if (!eimer.has(s)) eimer.set(s, []);
      eimer.get(s)!.push(a);
    }
    const namen = [...eimer.keys()].sort(
      (a, b) => (reihenfolge.indexOf(a) + 1 || 99) - (reihenfolge.indexOf(b) + 1 || 99),
    );
    return namen.map((name) => {
      const eintraege = eimer.get(name)!;
      const alle = eigeneGruppe
        ? eintraege
        : imBereich.filter((a) => (a.bereich || 'Ohne Thema') === name && !a.kinder?.length);
      return { name, anzeigename: anzeigename(name), eintraege, alle };
    });
  });

  interface Reihe {
    art: 'gruppe' | 'aufgabe';
    name?: string;
    a?: AufgabeAntwort;
  }
  function reihenFuer(eintraege: AufgabeAntwort[]): Reihe[] {
    const aus: Reihe[] = [];
    let letzteGruppe: string | null = null;
    for (const a of eintraege) {
      if (a.gruppe && a.gruppe !== letzteGruppe && a.gruppe !== a.bereich) {
        letzteGruppe = a.gruppe;
        aus.push({ art: 'gruppe', name: a.gruppe });
      }
      aus.push({ art: 'aufgabe', a });
    }
    return aus;
  }

  const laufend = $derived(blaetter.filter((a) => a.status === 'laeuft'));

  // ------------------------------------------------------------- Anlegen

  let neuTitel = $state('');
  let neuBereich = $state(bereich ?? '');
  let neuPrio = $state('');
  let neuEltern = $state('');

  $effect(() => {
    if (bereich) neuBereich = bereich;
    else if (!neuBereich && store.daten?.bereiche.length) neuBereich = store.daten.bereiche[0].name;
  });

  const moeglicheEltern = $derived(imBereich.filter((a) => a.bereich === neuBereich));

  function formOeffnen(): void {
    formOffen = true;
    neuTitel = '';
    neuPrio = '';
    neuEltern = '';
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
    const id = await store.aufgabeAnlegen({
      bereich: neuBereich,
      titel,
      prio: neuPrio || undefined,
      eltern_id: neuEltern || undefined,
    });
    if (id) {
      formOffen = false;
      toasts.info(`„${titel}“ angelegt.`);
    }
  }
</script>

{#if laufend.length}
  <div class="aufgaben-uebersicht">
    <Rubrik titel="In Arbeit" zahl={laufend.length} />
    <div class="uebersicht-reihe">
      {#each laufend as a (a.id)}
        <Chip onclick={() => oeffnen(a.id)}>{a.titel}{#if !bereich && a.bereich} · {a.bereich}{/if}</Chip>
      {/each}
    </div>
  </div>
{/if}

<div class="leiste">
  <Tabs tabs={filterTabs} aktiv={filter} onwechsel={filterWaehlen} label="Status" />
  <div class="leiste-werkzeug">
    <Feld
      bind:wert={suche}
      placeholder="Suche in Titel und Beschreibung…"
      aria-label="Aufgaben durchsuchen"
      icon={IconSuche}
      type="search"
      klein
    />
    <Auswahl
      class="gruppen-wahl"
      wert={gruppierung}
      optionen={gruppierOptionen}
      onchange={(e) => gruppierungWaehlen((e.target as HTMLSelectElement).value)}
      aria-label="Gruppierung"
      klein
    />
    {#if anlegenErlaubt}
      <Schreibbar>
        {#snippet children()}
          <Knopf variante="primaer" groesse="s" icon={IconPlus} onclick={formOeffnen}>Aufgabe</Knopf>
        {/snippet}
      </Schreibbar>
    {/if}
  </div>
</div>

<Dialog bind:offen={formOffen} titel="Aufgabe anlegen">
  <Feld label="Titel" bind:wert={neuTitel} placeholder="Was ist zu tun?" />
  {#if !bereich}
    <Auswahl label="Bereich" bind:wert={neuBereich} optionen={store.daten?.bereiche.map((b) => b.name) ?? []} />
  {/if}
  <Auswahl label="Priorität" bind:wert={neuPrio} optionen={PRIO_OPTIONEN} leer="— keine —" />
  <Auswahl
    label="Unterpunkt von"
    bind:wert={neuEltern}
    optionen={moeglicheEltern.map((e) => ({ wert: e.id, label: e.titel }))}
    leer="— eigenständig —"
  />
  {#snippet fuss()}
    <Knopf variante="leise" onclick={formAbbrechen}>Abbrechen</Knopf>
    <Knopf variante="primaer" onclick={anlegen} laedt={store.beschaeftigt}>Anlegen</Knopf>
  {/snippet}
</Dialog>

{#if !gruppen.length}
  <Leerzustand titel="Keine Aufgabe passt zum Filter" text="Filter lockern oder die Suche anpassen." />
{:else if gruppierung === 'flach'}
  <Karte titel={gruppen[0].anzeigename} zusatz={gruppen[0].eintraege.length} polster="keins">
    <ul class="aufgaben">
      {#each reihenFuer(gruppen[0].eintraege) as r, i (r.a?.id ?? 'g' + i)}
        {#if r.art === 'gruppe'}
          <li class="gruppe">{r.name}</li>
        {:else if r.a}
          <AufgabeZeile a={r.a} mitThema={!bereich} {nachId} onOeffnen={oeffnen} />
        {/if}
      {/each}
    </ul>
  </Karte>
{:else}
  {#each gruppen as g (g.name)}
    {@const fertig = g.alle.filter((a) => a.status === 'erledigt' || a.status === 'verworfen').length}
    <details class="sammelblock" open>
      <summary>
        <span class="name">{g.anzeigename}</span>
        <FortschrittBalken wert={g.alle.length ? fertig / g.alle.length : 0} zahl="{fertig}/{g.alle.length}" />
      </summary>
      <ul class="aufgaben">
        {#each reihenFuer(g.eintraege) as r, i (r.a?.id ?? g.name + '-g' + i)}
          {#if r.art === 'gruppe'}
            <li class="gruppe">{r.name}</li>
          {:else if r.a}
            <AufgabeZeile a={r.a} mitThema={!bereich && gruppierung !== 'bereich'} {nachId} onOeffnen={oeffnen} />
          {/if}
        {/each}
      </ul>
    </details>
  {/each}
{/if}

{#if offenId && nachId.get(offenId)}
  <AufgabeDetail a={nachId.get(offenId)!} {nachId} onClose={schliessen} onOeffnen={oeffnen} />
{/if}

<style>
  .aufgaben-uebersicht {
    margin-bottom: var(--a-5);
  }
  .uebersicht-reihe {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-2);
  }

  .leiste {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: space-between;
    gap: var(--a-3);
    margin-bottom: var(--a-5);
  }
  .leiste-werkzeug {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--a-2);
    margin-left: auto;
  }
  .leiste-werkzeug :global(.ui-feld) {
    width: 15rem;
  }
  :global(.gruppen-wahl) {
    width: 11rem;
    flex: none;
  }

  ul.aufgaben {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  li.gruppe {
    color: var(--farbe-text-2);
    font-size: var(--text-xs);
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin: var(--a-3) 0 var(--a-1);
    padding-left: 2px;
    background: none;
    cursor: default;
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
    flex: 0 0 auto;
  }
  .sammelblock > summary :global(.ui-balken) {
    max-width: 220px;
  }
  .sammelblock > ul.aufgaben {
    padding: 0 var(--a-2) var(--a-2);
  }
</style>
