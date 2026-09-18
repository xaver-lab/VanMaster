<script lang="ts">
  // Wiederverwendbare Aufgabenliste: Filter (Chips), Gruppierung, Suche,
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

  function filterWaehlen(f: Filter): void {
    filter = f;
    merken('aufgabenFilter', f);
  }
  function gruppierungWaehlen(g: Gruppierung): void {
    gruppierung = g;
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
    <h4>In Arbeit ({laufend.length})</h4>
    <div class="uebersicht-reihe">
      {#each laufend as a (a.id)}
        <button type="button" class="uebersicht-eintrag" onclick={() => oeffnen(a.id)}>
          <span class="titel">{a.titel}</span>
          {#if !bereich && a.bereich}<span class="zusatz">{a.bereich}</span>{/if}
        </button>
      {/each}
    </div>
  </div>
{/if}

<div class="leiste">
  <div class="chips">
    {#each FILTER as f (f)}
      <button type="button" class="chip" class:aktiv={filter === f} onclick={() => filterWaehlen(f)}>
        <span>{STATUS_WORT[f]}</span>
        <span class="zahl">{zahlen[f]}</span>
      </button>
    {/each}
  </div>
  <input
    type="search"
    placeholder="Suche in Titel und Beschreibung…"
    bind:value={suche}
    aria-label="Aufgaben durchsuchen"
  />
  <select class="wahl" bind:value={gruppierung} onchange={() => gruppierungWaehlen(gruppierung)} aria-label="Gruppierung">
    {#if !bereich}<option value="bereich">nach Thema</option>{/if}
    <option value="status">nach Status</option>
    <option value="prio">nach Priorität</option>
    <option value="flach">keine Gruppierung</option>
  </select>
  {#if anlegenErlaubt}
    <Schreibbar>
      {#snippet children()}
        <button type="button" class="flachknopf" onclick={formOeffnen}>+ Aufgabe</button>
      {/snippet}
    </Schreibbar>
  {/if}
</div>

{#if formOffen}
  <div class="karte anlegen-form">
    <label>
      Titel
      <input type="text" bind:value={neuTitel} placeholder="Was ist zu tun?" autofocus />
    </label>
    {#if !bereich}
      <label>
        Bereich
        <select class="wahl" bind:value={neuBereich}>
          {#each store.daten?.bereiche ?? [] as b (b.name)}
            <option value={b.name}>{b.name}</option>
          {/each}
        </select>
      </label>
    {/if}
    <label>
      Priorität
      <select class="wahl" bind:value={neuPrio}>
        <option value="">— keine —</option>
        <option value="kritisch">kritisch</option>
        <option value="hoch">hoch</option>
        <option value="mittel">mittel</option>
        <option value="nice">nice</option>
      </select>
    </label>
    <label>
      Unterpunkt von
      <select class="wahl" bind:value={neuEltern}>
        <option value="">— eigenständig —</option>
        {#each moeglicheEltern as e (e.id)}
          <option value={e.id}>{e.titel}</option>
        {/each}
      </select>
    </label>
    <div class="anlegen-form-leiste">
      <button type="button" class="flachknopf" onclick={anlegen} disabled={store.beschaeftigt}>Anlegen</button>
      <button type="button" class="flachknopf" onclick={formAbbrechen}>Abbrechen</button>
    </div>
  </div>
{/if}

{#if !gruppen.length}
  <p class="leer">Keine Aufgabe passt zum Filter.</p>
{:else if gruppierung === 'flach'}
  <div class="karte">
    <div class="karten-kopf">
      <h2>Alle Treffer</h2>
      <span class="zaehler">{gruppen[0].eintraege.length}</span>
    </div>
    <ul class="aufgaben">
      {#each reihenFuer(gruppen[0].eintraege) as r, i (r.a?.id ?? 'g' + i)}
        {#if r.art === 'gruppe'}
          <li class="gruppe">{r.name}</li>
        {:else if r.a}
          <AufgabeZeile a={r.a} mitThema={!bereich} {nachId} onOeffnen={oeffnen} />
        {/if}
      {/each}
    </ul>
  </div>
{:else}
  {#each gruppen as g (g.name)}
    {@const fertig = g.alle.filter((a) => a.status === 'erledigt' || a.status === 'verworfen').length}
    <details class="sammelblock nach-status-{g.name}" open>
      <summary>
        <span class="name">{g.anzeigename}</span>
        <div class="balken">
          <span style="width: {g.alle.length ? (100 * fertig) / g.alle.length : 0}%"></span>
        </div>
        <span class="zaehler">{fertig}/{g.alle.length}</span>
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
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: var(--radius);
    padding: 0.7rem 0.9rem;
    margin-bottom: 1rem;
  }
  .aufgaben-uebersicht h4 {
    margin: 0 0 0.5rem;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--gedaempft);
  }
  .uebersicht-reihe {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  .uebersicht-eintrag {
    display: flex;
    align-items: baseline;
    gap: 0.4rem;
    background: var(--akzent-tief);
    border: 1px solid transparent;
    border-radius: 99px;
    padding: 0.3rem 0.75rem;
    font-size: 0.85rem;
    color: var(--text);
  }
  .uebersicht-eintrag:hover {
    border-color: var(--akzent);
  }
  .uebersicht-eintrag .zusatz {
    color: var(--gedaempft);
    font-size: 0.76rem;
  }

  .anlegen-form {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.6rem 1rem;
    margin-bottom: 0.8rem;
    align-items: end;
  }
  .anlegen-form label {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    font-size: 0.78rem;
    color: var(--gedaempft);
  }
  .anlegen-form input,
  .anlegen-form select {
    min-height: 38px;
    padding: 0 0.65rem;
    background: var(--flaeche);
    color: var(--text);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
    font-size: 0.9rem;
  }
  .anlegen-form input:focus,
  .anlegen-form select:focus {
    outline: none;
    border-color: var(--akzent);
  }
  .anlegen-form-leiste {
    display: flex;
    gap: 0.5rem;
    grid-column: 1 / -1;
  }

  /* -------------------------------------------------------- Leiste/Filter */
  .leiste {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
  }
  .leiste input[type='search'] {
    flex: 1 1 15rem;
    min-width: 0;
    min-height: 38px;
    padding: 0 0.75rem;
    background: var(--flaeche);
    color: var(--text);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
  }
  .leiste input[type='search']:focus {
    outline: none;
    border-color: var(--akzent);
  }
  .wahl {
    min-height: 38px;
    padding: 0 0.75rem;
    background: var(--flaeche);
    color: var(--text);
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
  }
  .wahl:focus {
    outline: none;
    border-color: var(--akzent);
  }
  .chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
  }
  .chip {
    min-height: 32px;
    padding: 0 0.7rem;
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: 99px;
    color: var(--gedaempft);
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
  }
  .chip:hover {
    border-color: var(--linie-hell);
    color: var(--text);
  }
  .chip.aktiv {
    background: var(--akzent);
    border-color: var(--akzent);
    color: #1a1205;
    font-weight: 600;
  }
  :global(html[data-thema='hell']) .chip.aktiv {
    color: #fff;
  }
  .chip .zahl {
    font-size: 0.75rem;
    opacity: 0.75;
    font-variant-numeric: tabular-nums;
  }

  /* ---------------------------------------------------------------- Liste */
  ul.aufgaben {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  li.gruppe {
    color: var(--gedaempft);
    font-size: 0.74rem;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin: 0.9rem 0 0.2rem;
    padding-left: 0.1rem;
    background: none;
    cursor: default;
  }

  .sammelblock {
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: var(--radius);
    margin-bottom: 0.6rem;
    overflow: hidden;
  }
  .sammelblock > summary {
    list-style: none;
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0.9rem;
    cursor: pointer;
  }
  .sammelblock > summary::-webkit-details-marker {
    display: none;
  }
  .sammelblock > summary::before {
    content: '▸';
    color: var(--gedaempft);
    font-size: 0.8rem;
    transition: transform 0.15s;
  }
  .sammelblock[open] > summary::before {
    transform: rotate(90deg);
  }
  .sammelblock > summary .name {
    font-weight: 600;
    flex: 0 0 auto;
  }
  .sammelblock > summary .balken {
    max-width: 220px;
  }
  .sammelblock > ul.aufgaben {
    padding: 0 0.5rem 0.4rem;
  }
</style>
