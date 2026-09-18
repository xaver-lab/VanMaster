<script lang="ts">
  import { store } from '../lib/daten.svelte';
</script>

<section>
  <h1>Start</h1>
  {#if store.daten}
    <dl class="zahlen">
      <div><dt>Bereiche</dt><dd>{store.daten.bereiche.length}</dd></div>
      <div><dt>Aufgaben</dt><dd>{store.daten.aufgaben.length}</dd></div>
      <div><dt>Teile</dt><dd>{store.daten.teile.length}</dd></div>
      <div><dt>Erzeugt</dt><dd>{store.daten.erzeugt}</dd></div>
    </dl>
  {/if}
</section>

<style>
  .zahlen {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(8rem, 1fr));
    gap: 1rem;
    margin-top: 1rem;
  }
  .zahlen div {
    background: var(--flaeche-2);
    border-radius: 0.5rem;
    padding: 0.8rem;
  }
  dt {
    font-size: 0.8rem;
    color: var(--schrift-schwach);
  }
  dd {
    margin: 0;
    font-size: 1.3rem;
  }
</style>
