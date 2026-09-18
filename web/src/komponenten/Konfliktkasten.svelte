<script lang="ts">
  // Wird gezeigt, sobald `daten.konflikt` gesetzt ist: eine Datei wurde
  // zwischenzeitlich anderswo (Claude, Sync) geändert, bevor unser Schreiben
  // ankam. Einzige Auswege: neu laden oder den Hinweis vorerst wegklicken.
  import { laden, konfliktSchliessen } from '../lib/daten.svelte';
  import type { Konflikt } from '../lib/daten.svelte';

  let { konflikt }: { konflikt: Konflikt } = $props();
</script>

<div class="konflikt-hintergrund">
  <div class="konflikt-kasten">
    <h2>Zwischenzeitlich geändert</h2>
    <p>{konflikt.meldung}</p>
    <p class="konflikt-datei">{konflikt.datei}</p>
    <div class="konflikt-knoepfe">
      <button class="knopf" onclick={() => konfliktSchliessen()}>Schließen</button>
      <button class="knopf knopf--akzent" onclick={() => laden()}>Neu laden</button>
    </div>
  </div>
</div>

<style>
  .konflikt-hintergrund {
    position: fixed;
    inset: 0;
    z-index: 60;
    background: rgba(6, 8, 12, 0.6);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }
  .konflikt-kasten {
    width: min(480px, 100%);
    background: var(--flaeche);
    border: 1px solid var(--linie-hell);
    border-radius: var(--radius);
    box-shadow: var(--schatten);
    padding: 1.4rem;
  }
  .konflikt-datei {
    color: var(--gedaempft);
    font-size: 0.85rem;
  }
  .konflikt-knoepfe {
    display: flex;
    justify-content: flex-end;
    gap: 0.6rem;
    margin-top: 1rem;
  }
  .knopf {
    border: 1px solid var(--linie-hell);
    background: var(--flaeche-hoch);
    border-radius: var(--radius-klein);
    padding: 0.45rem 0.9rem;
  }
  .knopf--akzent {
    background: var(--akzent-tief);
    border-color: var(--akzent);
    color: var(--akzent);
  }
</style>
