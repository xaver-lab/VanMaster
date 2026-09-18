<script lang="ts">
  import './app.css';
  import { store } from './lib/daten.svelte';
  import { router, TITEL } from './lib/router.svelte';
  import { paletteOeffnen } from './lib/palette.svelte';
  import Schiene from './lib/Schiene.svelte';
  import ToastAnzeige from './lib/ToastAnzeige.svelte';
  import Start from './routen/Start.svelte';
  import Aufgaben from './routen/Aufgaben.svelte';
  import Bereiche from './routen/Bereiche.svelte';
  import Teile from './routen/Teile.svelte';
  import Zuschnitt from './routen/Zuschnitt.svelte';
  import Medien from './routen/Medien.svelte';

  store.init();

  let unterzeile = $derived(router.route.parameter[0] ?? '');

  let verbindung = $derived.by(() => {
    if (!store.darfSchreiben) return { klasse: '', text: 'nur lesen', titel: 'Statisch — keine Änderungen möglich' };
    if (store.verbindung === 'verbunden') return { klasse: 'live', text: 'live', titel: 'Live-Verbindung zum Server' };
    return { klasse: 'getrennt', text: 'getrennt', titel: `Live-Verbindung: ${store.verbindung}` };
  });

  $effect(() => {
    document.title = `${TITEL[router.route.ansicht]} · VanMaster`;
  });
</script>

<div class="app">
  <Schiene />

  <div class="rahmen">
    <header class="kopf">
      <div class="kopf-titel">
        <h1>{TITEL[router.route.ansicht]}</h1>
        {#if unterzeile}<p>{unterzeile}</p>{/if}
      </div>
      <div class="kopf-werkzeuge">
        <button type="button" class="suchknopf" onclick={paletteOeffnen}>
          <span>⌕</span><span class="text">Suchen</span><kbd>Strg K</kbd>
        </button>
        <span class="verbindung {verbindung.klasse}" title={verbindung.titel}>
          <span class="punkt"></span>{verbindung.text}
        </span>
      </div>
    </header>

    <main>
      {#if store.laedt}
        <p class="leer">Lädt …</p>
      {:else if store.ladeFehler}
        <p class="leer fehler">{store.ladeFehler}</p>
      {:else if router.route.ansicht === 'start'}
        <Start />
      {:else if router.route.ansicht === 'bereiche'}
        <Bereiche />
      {:else if router.route.ansicht === 'aufgaben'}
        <Aufgaben />
      {:else if router.route.ansicht === 'teile'}
        <Teile />
      {:else if router.route.ansicht === 'zuschnitt'}
        <Zuschnitt />
      {:else if router.route.ansicht === 'medien'}
        <Medien />
      {/if}
    </main>
  </div>
</div>

<ToastAnzeige />
