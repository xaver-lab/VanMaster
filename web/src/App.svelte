<script lang="ts">
  import './app.css';
  import { store } from './lib/daten.svelte';
  import { router } from './lib/router.svelte';
  import Kopfleiste from './lib/Kopfleiste.svelte';
  import ToastAnzeige from './lib/ToastAnzeige.svelte';
  import Start from './routen/Start.svelte';
  import Aufgaben from './routen/Aufgaben.svelte';
  import Bereiche from './routen/Bereiche.svelte';
  import Teile from './routen/Teile.svelte';
  import Zuschnitt from './routen/Zuschnitt.svelte';
  import Medien from './routen/Medien.svelte';

  store.init();
</script>

<Kopfleiste />

<main>
  {#if store.laedt}
    <p class="hinweis">Lädt…</p>
  {:else if store.ladeFehler}
    <p class="hinweis hinweis--fehler">{store.ladeFehler}</p>
  {:else if router.route.ansicht === 'start'}
    <Start />
  {:else if router.route.ansicht === 'aufgaben'}
    <Aufgaben />
  {:else if router.route.ansicht === 'bereiche'}
    <Bereiche />
  {:else if router.route.ansicht === 'teile'}
    <Teile />
  {:else if router.route.ansicht === 'zuschnitt'}
    <Zuschnitt />
  {:else if router.route.ansicht === 'medien'}
    <Medien />
  {/if}
</main>

<ToastAnzeige />

<style>
  main {
    max-width: 60rem;
    margin: 0 auto;
    padding: 1.5rem 1rem;
  }
  .hinweis {
    color: var(--schrift-schwach);
  }
  .hinweis--fehler {
    color: var(--farbe-fehler);
  }
</style>
