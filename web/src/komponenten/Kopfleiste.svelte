<script lang="ts">
  // Seitenschiene (Navigation) und Kopfzeile in einem — wie `aside.schiene`
  // + `header.kopf` im alten Dashboard (docs/index.html).
  import { routing, ANSICHTEN, TITEL, zu } from '../lib/routing.svelte';
  import { themaZustand, umschalten } from '../lib/thema.svelte';
  import { daten } from '../lib/daten.svelte';

  const ICON: Record<string, string> = {
    start: '◉',
    themen: '▤',
    aufgaben: '✓',
    teile: '◫',
    zuschnitt: '▭',
    medien: '▦',
  };

  let titelZeile = $derived(TITEL[routing.route.ansicht]);
  let standText = $derived(
    daten.modus === 'statisch' ? 'nur lesend' : daten.schreibt ? 'speichert …' : 'bereit',
  );
</script>

<aside class="schiene">
  <div class="marke">
    <span class="zeichen">🚐</span>
    <span class="wort">VanMaster</span>
  </div>

  <nav class="hauptnav">
    {#each ANSICHTEN as a, i (a)}
      <button
        class:aktiv={routing.route.ansicht === a}
        onclick={() => zu(a)}
        title={`${TITEL[a][0]} (${i + 1})`}
      >
        <span class="icon">{ICON[a]}</span>
        <span class="text">{TITEL[a][0]}</span>
      </button>
    {/each}
  </nav>

  <div class="schienenfuss">
    <button class="flachknopf" title="Hell / dunkel (T)" onclick={() => umschalten()}>
      {themaZustand.wert === 'hell' ? '◑' : '◐'}<span class="text">Ansicht</span>
    </button>
    <p class="stand">{standText}</p>
  </div>
</aside>

<header class="kopf">
  <div class="kopf-titel">
    <h1>{titelZeile[0]}</h1>
    <p>{titelZeile[1]}</p>
  </div>
</header>

<style>
  .schiene {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    width: var(--schiene);
    flex: 0 0 auto;
    background: var(--flaeche-tief);
    border-right: 1px solid var(--linie);
    padding: 1rem 0.7rem;
  }
  .marke {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.3rem 0.5rem;
    font-weight: 600;
  }
  .hauptnav {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }
  .hauptnav button {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    background: none;
    border: none;
    border-radius: var(--radius-klein);
    padding: 0.55rem 0.6rem;
    color: var(--gedaempft);
    text-align: left;
  }
  .hauptnav button.aktiv {
    background: var(--flaeche-hoch);
    color: var(--text);
  }
  .schienenfuss {
    margin-top: auto;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .flachknopf {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: 1px solid var(--linie);
    border-radius: var(--radius-klein);
    padding: 0.4rem 0.6rem;
  }
  .stand {
    color: var(--gedaempft);
    font-size: 0.78rem;
    margin: 0;
    padding: 0 0.6rem;
  }
  .kopf {
    grid-area: kopf;
    padding: 1rem 1.4rem;
    border-bottom: 1px solid var(--linie);
  }
  .kopf-titel h1 {
    margin: 0;
    font-size: 1.3rem;
  }
  .kopf-titel p {
    margin: 0.2rem 0 0;
    color: var(--gedaempft);
    font-size: 0.85rem;
  }
</style>
