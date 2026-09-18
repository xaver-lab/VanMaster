<script lang="ts">
  // Wiederverwendbarer Weg für den Lesemodus: alles, was hier verpackt ist,
  // verschwindet vollständig, sobald `daten.lesemodus` gesetzt ist
  // (statischer Build auf GitHub Pages). Von Phase 6 an für jeden
  // Bearbeitungsknopf, jedes Eingabefeld und jedes Formular verwenden.
  import { daten } from '../lib/daten.svelte';

  let { children } = $props<{ children?: () => unknown }>();
</script>

{#if !daten.lesemodus}
  {@render children?.()}
{/if}
