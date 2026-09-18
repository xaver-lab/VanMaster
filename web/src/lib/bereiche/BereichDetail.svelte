<script lang="ts">
  // Bereichsansicht: Kopf, Reiter, bearbeitbare Abschnitte. Reiter „Übersicht“
  // und „Aufgaben“ gibt es immer, die übrigen nur wenn zum Bereich Daten
  // vorliegen (wie früher docs/js/themen.js:themaReiter, hier ohne Zuschnitt
  // — das ist kein Teil dieses Auftrags).
  import { store } from '../daten.svelte';
  import { router } from '../router.svelte';
  import AufgabenListe from '../aufgaben/AufgabenListe.svelte';
  import Markdown from '../Markdown.svelte';
  import Abschnitt from './Abschnitt.svelte';
  import { fortschritt } from './sortierung';

  let { name }: { name: string } = $props();

  const REIHENFOLGE_ABSCHNITTE = ['Beschreibung', 'Stand', 'Auslegung', 'Notizen', 'Links'];
  const STATUS_WORT: Record<string, string> = { 'in-arbeit': 'in Arbeit', geplant: 'geplant', fertig: 'fertig' };

  const euro = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });
  function zahl(wert: string | undefined): number {
    const n = parseFloat((wert ?? '').replace(',', '.'));
    return Number.isFinite(n) ? n : 0;
  }

  const bereich = $derived(store.daten?.bereiche.find((b) => b.name === name));
  const aufgaben = $derived(store.daten?.aufgaben ?? []);
  const f = $derived(fortschritt(aufgaben, name));

  const teile = $derived((store.daten?.teile ?? []).filter((t) => t.kategorie === name));
  const entscheidungen = $derived((store.daten?.entscheidungen ?? []).filter((s) => s.bereich === name));
  const anleitungen = $derived((store.daten?.anleitungen ?? []).filter((s) => s.bereich === name));
  const recherche = $derived((store.daten?.recherche ?? []).filter((s) => s.bereich === name));
  const medien = $derived((store.daten?.medien ?? []).filter((m) => m.bereich === name));

  const kosten = $derived(teile.reduce((s, t) => s + zahl(t.preis), 0));
  const gewicht = $derived(teile.reduce((s, t) => s + zahl(t.gewicht_kg), 0));

  type ReiterId = 'uebersicht' | 'aufgaben' | 'teile' | 'entscheidungen' | 'anleitungen' | 'recherche' | 'medien';

  const reiter = $derived.by((): { id: ReiterId; wort: string; zahl: number }[] => {
    const r: { id: ReiterId; wort: string; zahl: number }[] = [
      { id: 'uebersicht', wort: 'Übersicht', zahl: 0 },
      { id: 'aufgaben', wort: 'Aufgaben', zahl: f.gesamt },
    ];
    if (teile.length) r.push({ id: 'teile', wort: 'Teile', zahl: teile.length });
    if (entscheidungen.length) r.push({ id: 'entscheidungen', wort: 'Entscheidungen', zahl: entscheidungen.length });
    if (anleitungen.length) r.push({ id: 'anleitungen', wort: 'Anleitungen', zahl: anleitungen.length });
    if (recherche.length) r.push({ id: 'recherche', wort: 'Recherche', zahl: recherche.length });
    if (medien.length) r.push({ id: 'medien', wort: 'Medien', zahl: medien.length });
    return r;
  });

  const aktiv = $derived.by((): ReiterId => {
    const gewuenscht = router.route.parameter[1];
    const treffer = reiter.find((r) => r.id === gewuenscht);
    return treffer ? treffer.id : 'uebersicht';
  });

  function reiterWaehlen(id: ReiterId): void {
    router.gehe('bereiche', name, id);
  }

  const matrix = $derived(store.daten?.bearbeitbar?.bereich_abschnitte ?? {});
  const abschnitteAnzeige = $derived(
    REIHENFOLGE_ABSCHNITTE.map((n) => ({
      name: n,
      text: bereich?.abschnitte?.[n]?.text ?? '',
      bearbeitbar: !!matrix[n]?.web,
    })),
  );
</script>

{#if !bereich}
  <p class="leer">Bereich „{name}“ nicht gefunden.</p>
{:else}
  <div class="karte bereich-kopf">
    <div class="obenzeile">
      <h2 class="titel-gross">{bereich.name}</h2>
      {#if bereich.phase != null}<span class="chip">Phase {bereich.phase}</span>{/if}
      <span class="chip status-{bereich.status}">{STATUS_WORT[bereich.status] ?? bereich.status}</span>
    </div>
    {#if bereich.kurz}<p class="kurz">{bereich.kurz}</p>{/if}
    {#if f.gesamt}
      <div class="balken"><span style="width: {(100 * f.fertig) / f.gesamt}%"></span></div>
    {/if}
    <div class="kennzahlen">
      <div class="kachel">
        <div>
          <div class="titel">Aufgaben</div>
          <div class="wert">{f.fertig}/{f.gesamt}</div>
        </div>
      </div>
      {#if teile.length}
        <div class="kachel">
          <div>
            <div class="titel">Teilekosten</div>
            <div class="wert">{euro.format(kosten)}</div>
          </div>
        </div>
        <div class="kachel">
          <div>
            <div class="titel">Gewicht</div>
            <div class="wert">{gewicht.toFixed(1)} kg</div>
          </div>
        </div>
      {/if}
      {#if medien.length}
        <div class="kachel">
          <div>
            <div class="titel">Medien</div>
            <div class="wert">{medien.length}</div>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <nav class="reiternav">
    {#each reiter as r (r.id)}
      <button type="button" class:aktiv={aktiv === r.id} onclick={() => reiterWaehlen(r.id)}>
        <span>{r.wort}</span>
        {#if r.zahl}<span class="zahl">{r.zahl}</span>{/if}
      </button>
    {/each}
  </nav>

  {#if aktiv === 'uebersicht'}
    <div class="karte">
      {#each abschnitteAnzeige as a (a.name)}
        <Abschnitt bereich={name} name={a.name} text={a.text} bearbeitbar={a.bearbeitbar} />
      {/each}
    </div>
  {:else if aktiv === 'aufgaben'}
    <AufgabenListe bereich={name} />
  {:else if aktiv === 'teile'}
    <div class="karte">
      <ul class="liste">
        {#each teile as t (t.id)}
          <li>
            <span class="titel">{t.titel}</span>
            <span class="zusatz">{t.status}{#if t.preis}&nbsp;·&nbsp;{euro.format(zahl(t.preis))}{/if}</span>
          </li>
        {/each}
      </ul>
    </div>
  {:else if aktiv === 'entscheidungen'}
    {#each entscheidungen as s (s.datei)}
      <div class="karte">
        <div class="karten-kopf"><h2>{s.titel}</h2><span class="chip">{s.status}</span></div>
        <Markdown text={s.text} />
      </div>
    {/each}
  {:else if aktiv === 'anleitungen'}
    {#each anleitungen as s (s.datei)}
      <div class="karte">
        <div class="karten-kopf"><h2>{s.titel}</h2></div>
        <Markdown text={s.text} />
      </div>
    {/each}
  {:else if aktiv === 'recherche'}
    {#each recherche as s (s.datei)}
      <div class="karte">
        <div class="karten-kopf"><h2>{s.titel}</h2></div>
        <Markdown text={s.text} />
      </div>
    {/each}
  {:else if aktiv === 'medien'}
    <div class="karte">
      <ul class="liste">
        {#each medien as m (m.datei)}
          <li><span class="titel">{m.name}</span><span class="zusatz">{m.art}</span></li>
        {/each}
      </ul>
    </div>
  {/if}
{/if}

<style>
  .bereich-kopf {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }
  .obenzeile {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    flex-wrap: wrap;
  }
  .titel-gross {
    margin: 0;
    font-size: 1.2rem;
    font-weight: 650;
  }
  .chip {
    margin-left: auto;
    font-size: 0.72rem;
    padding: 0.15rem 0.6rem;
    border-radius: 99px;
    background: var(--flaeche-hoch);
    color: var(--gedaempft);
    border: 1px solid var(--linie);
    white-space: nowrap;
  }
  .chip + .chip {
    margin-left: 0;
  }
  .chip.status-in-arbeit {
    color: var(--wartet);
    border-color: color-mix(in srgb, var(--wartet) 45%, transparent);
    background: var(--wartet-tief);
  }
  .chip.status-fertig {
    color: var(--gut);
    border-color: color-mix(in srgb, var(--gut) 45%, transparent);
    background: var(--gut-tief);
  }
  .kurz {
    margin: 0;
    color: var(--gedaempft);
    font-size: 0.88rem;
  }
  .balken {
    height: 7px;
    background: var(--flaeche-hoch);
    border-radius: 99px;
    overflow: hidden;
  }
  .balken span {
    display: block;
    height: 100%;
    background: var(--gut);
    border-radius: 99px;
    transition: width 0.5s ease;
  }
  .kennzahlen {
    margin: 0.2rem 0 0;
  }

  .reiternav {
    display: flex;
    gap: 0.3rem;
    flex-wrap: wrap;
    margin: 1rem 0 1rem;
    border-bottom: 1px solid var(--linie);
  }
  .reiternav button {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    min-height: 38px;
    padding: 0 0.85rem;
    background: none;
    border: none;
    border-bottom: 2px solid transparent;
    color: var(--gedaempft);
    font-size: 0.88rem;
  }
  .reiternav button:hover {
    color: var(--text);
  }
  .reiternav button.aktiv {
    color: var(--text);
    border-bottom-color: var(--akzent);
    font-weight: 600;
  }
  .reiternav .zahl {
    font-size: 0.72rem;
    color: var(--gedaempft);
    font-variant-numeric: tabular-nums;
  }

  .liste {
    list-style: none;
    margin: 0;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .liste li {
    display: flex;
    align-items: baseline;
    gap: 0.6rem;
    padding: 0.4rem 0;
    border-bottom: 1px solid var(--linie);
  }
  .liste li:last-child {
    border-bottom: none;
  }
  .liste .titel {
    font-weight: 550;
  }
  .liste .zusatz {
    margin-left: auto;
    color: var(--gedaempft);
    font-size: 0.82rem;
    white-space: nowrap;
  }
</style>
