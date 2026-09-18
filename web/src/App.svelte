<script lang="ts">
  // Rahmen: Kopfleiste, aktive Ansicht per Hash-Route, Toasts, Lade-/
  // Fehleranzeige, Konfliktkasten. Inhalt der Ansichten kommt in Phase 6–8.
  import { onMount } from 'svelte';
  import { daten, laden } from './lib/daten.svelte';
  import { verbinden } from './lib/live';
  import { routing } from './lib/routing.svelte';
  import { tastenAnmelden } from './lib/tasten';
  import Kopfleiste from './komponenten/Kopfleiste.svelte';
  import Toasts from './komponenten/Toasts.svelte';
  import Konfliktkasten from './komponenten/Konfliktkasten.svelte';
  import Ladeanzeige from './komponenten/Ladeanzeige.svelte';
  import Start from './komponenten/ansichten/Start.svelte';
  import Themen from './komponenten/ansichten/Themen.svelte';
  import Aufgaben from './komponenten/ansichten/Aufgaben.svelte';
  import Teile from './komponenten/ansichten/Teile.svelte';
  import Zuschnitt from './komponenten/ansichten/Zuschnitt.svelte';
  import Medien from './komponenten/ansichten/Medien.svelte';

  const ANSICHT_KOMPONENTE = {
    start: Start,
    themen: Themen,
    aufgaben: Aufgaben,
    teile: Teile,
    zuschnitt: Zuschnitt,
    medien: Medien,
  } as const;

  let aktiveAnsicht = $derived(ANSICHT_KOMPONENTE[routing.route.ansicht]);

  onMount(() => {
    const tastenAbmelden = tastenAnmelden({});
    // SSE erst nach dem ersten Laden — vorher steht der Modus nicht fest.
    // Im Lesemodus bricht verbinden() von selbst ab.
    let liveAbmelden: (() => void) | null = null;
    laden().then(() => {
      liveAbmelden = verbinden();
    });
    return () => {
      tastenAbmelden();
      liveAbmelden?.();
    };
  });
</script>

<div class="app">
  <Kopfleiste />

  <main class="buehne">
    {#if daten.laedt && !daten.wert}
      <Ladeanzeige />
    {:else if daten.fehler}
      <p class="fehlermeldung">{daten.fehler}</p>
    {:else}
      <svelte:component this={aktiveAnsicht} />
    {/if}
  </main>

  <Toasts />

  {#if daten.konflikt}
    <Konfliktkasten konflikt={daten.konflikt} />
  {/if}
</div>

<style>
  .app {
    display: grid;
    grid-template-columns: var(--schiene) 1fr;
    grid-template-rows: auto 1fr;
    grid-template-areas: 'schiene kopf' 'schiene buehne';
    min-height: 100vh;
  }
  :global(.schiene) {
    grid-area: schiene;
  }
  :global(.kopf) {
    grid-area: kopf;
  }
  .buehne {
    grid-area: buehne;
    padding: 1.4rem;
    overflow: auto;
  }
  .fehlermeldung {
    color: var(--warn);
  }
</style>
