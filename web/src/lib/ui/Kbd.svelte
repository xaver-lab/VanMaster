<script lang="ts">
  // Tastenkürzel anzeigen: <Kbd tasten="Strg K" /> — Leerzeichen trennt Tasten.
  let { tasten }: { tasten: string } = $props();
  let liste = $derived(tasten.split(' ').filter(Boolean));
</script>

<span class="ui-kbd">
  {#each liste as t}<kbd>{t}</kbd>{/each}
</span>

<style>
  .ui-kbd { display: inline-flex; gap: 3px; vertical-align: middle; }
  kbd {
    min-width: 20px;
    height: 20px;
    padding: 0 5px;
    display: inline-grid;
    place-items: center;
    font-family: var(--schrift-mono);
    font-size: 0.6875rem;
    font-weight: 500;
    color: var(--farbe-text-2);
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie-stark);
    border-bottom-width: 2px;
    border-radius: var(--r-s);
    line-height: 1;
  }
</style>
