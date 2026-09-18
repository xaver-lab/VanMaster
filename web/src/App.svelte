<script lang="ts">
  import './app.css';
  import { store } from './lib/daten.svelte';
  import { ANSICHTEN, router, TITEL } from './lib/router.svelte';
  import { paletteOeffnen } from './lib/palette.svelte';
  import { theme } from './lib/theme.svelte';
  import Schiene from './lib/Schiene.svelte';
  import ToastAnzeige from './lib/ToastAnzeige.svelte';
  import BestaetigungsHost from './lib/ui/BestaetigungsHost.svelte';
  import IconKnopf from './lib/ui/IconKnopf.svelte';
  import Kbd from './lib/ui/Kbd.svelte';
  import Leerzustand from './lib/ui/Leerzustand.svelte';
  import { IconFehler, IconMond, IconSonne, IconSuche } from './lib/ui/icons';
  import Start from './routen/Start.svelte';
  import Aufgaben from './routen/Aufgaben.svelte';
  import Bereiche from './routen/Bereiche.svelte';
  import Teile from './routen/Teile.svelte';
  import Zuschnitt from './routen/Zuschnitt.svelte';
  import Medien from './routen/Medien.svelte';
  import Muster from './routen/Muster.svelte';

  store.init();

  let unterzeile = $derived(router.route.parameter[0] ?? '');
  let nummer = $derived.by(() => {
    const i = (ANSICHTEN as readonly string[]).indexOf(router.route.ansicht);
    return i >= 0 ? `0${i + 1}` : '';
  });

  let verbindung = $derived.by(() => {
    if (!store.darfSchreiben) return { klasse: 'lesen', text: 'nur lesen', titel: 'Statische Seite — Änderungen sind hier nicht möglich' };
    if (store.verbindung === 'verbunden') return { klasse: 'live', text: 'live', titel: 'Live-Verbindung: Änderungen von Claude erscheinen sofort' };
    if (store.verbindung === 'verbindet') return { klasse: 'verbindet', text: 'verbindet', titel: 'Live-Verbindung wird aufgebaut' };
    return { klasse: 'getrennt', text: 'getrennt', titel: 'Live-Verbindung unterbrochen — versucht es weiter' };
  });

  $effect(() => {
    document.title = `${TITEL[router.route.ansicht]} · VanMaster`;
  });
</script>

<div class="app">
  <Schiene />

  <div class="rahmen">
    <header class="kopf">
      <div class="titelblock">
        {#if nummer}<span class="nummer" aria-hidden="true">{nummer}</span>{/if}
        <div class="titel">
          <h1>{TITEL[router.route.ansicht]}</h1>
          {#if unterzeile}<p><span class="trenner">/</span>{unterzeile}</p>{/if}
        </div>
      </div>

      <div class="werkzeuge">
        <button type="button" class="suche" onclick={paletteOeffnen}>
          <IconSuche size={16} strokeWidth={1.9} aria-hidden="true" />
          <span class="suche-text">Suchen oder springen …</span>
          <Kbd tasten="Strg K" />
        </button>

        <span class="verbindung {verbindung.klasse}" title={verbindung.titel} role="status">
          <span class="punkt" aria-hidden="true"></span>{verbindung.text}
        </span>

        <IconKnopf
          icon={theme.aktuell === 'hell' ? IconMond : IconSonne}
          label={theme.aktuell === 'hell' ? 'Dunkel (T)' : 'Hell (T)'}
          onclick={() => theme.umschalten()}
        />
      </div>

      {#if store.beschaeftigt}<span class="arbeitet" aria-hidden="true"></span>{/if}
    </header>

    <main>
      {#if store.laedt}
        <div class="laden" aria-label="Lädt">
          <span></span><span></span><span></span>
        </div>
      {:else if store.ladeFehler}
        <Leerzustand icon={IconFehler} titel="Keine Daten" text={store.ladeFehler} />
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
      {:else if router.route.ansicht === 'muster'}
        <Muster />
      {/if}
    </main>
  </div>
</div>

<ToastAnzeige />
<BestaetigungsHost />

<style>
  .app { display: flex; min-height: 100vh; }

  .rahmen {
    position: relative;
    flex: 1 1 auto;
    min-width: 0;
    display: flex;
    flex-direction: column;
    isolation: isolate;
  }
  /* Karopapier oben, läuft nach unten aus */
  .rahmen::before {
    content: '';
    position: absolute;
    inset: 0 0 auto 0;
    height: 560px;
    z-index: -1;
    pointer-events: none;
    background-image:
      linear-gradient(var(--farbe-raster) 1px, transparent 1px),
      linear-gradient(90deg, var(--farbe-raster) 1px, transparent 1px);
    background-size: 24px 24px;
    background-position: -1px -1px;
    mask-image: linear-gradient(to bottom, #000 0%, transparent 100%);
  }

  .kopf {
    position: sticky;
    top: 0;
    z-index: 20;
    display: flex;
    align-items: center;
    gap: var(--a-5);
    height: var(--kopfhoehe);
    padding: 0 var(--a-6);
    background: color-mix(in srgb, var(--farbe-grund) 82%, transparent);
    backdrop-filter: blur(12px) saturate(1.2);
    border-bottom: 1px solid var(--farbe-linie);
  }

  .titelblock { display: flex; align-items: center; gap: var(--a-3); min-width: 0; }
  .nummer {
    font-family: var(--schrift-mono);
    font-size: var(--text-xs);
    color: var(--farbe-signal);
    padding: 3px 6px;
    border: 1px solid color-mix(in srgb, var(--farbe-signal) 40%, transparent);
    border-radius: var(--r-s);
    line-height: 1;
  }
  .titel { display: flex; align-items: baseline; gap: var(--a-2); min-width: 0; }
  h1 {
    font-size: var(--text-xl);
    font-weight: 750;
    font-stretch: 115%;
    letter-spacing: -0.025em;
    line-height: 1;
  }
  .titel p {
    font-size: var(--text-l);
    font-weight: 500;
    color: var(--farbe-text-2);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .trenner { color: var(--farbe-text-3); margin-right: var(--a-2); }

  .werkzeuge { margin-left: auto; display: flex; align-items: center; gap: var(--a-3); }

  .suche {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 300px;
    height: 36px;
    padding: 0 6px 0 12px;
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie);
    border-radius: var(--r-m);
    color: var(--farbe-text-2);
    font-size: var(--text-s);
    text-align: left;
    box-shadow: var(--schatten-1);
    transition: border-color var(--t-kurz), color var(--t-kurz);
  }
  .suche:hover { border-color: var(--farbe-linie-stark); color: var(--farbe-text); }
  .suche-text { flex: 1; }

  .verbindung {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    height: 26px;
    padding: 0 9px;
    border-radius: var(--r-s);
    font-family: var(--schrift-mono);
    font-size: 0.6875rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    white-space: nowrap;
    color: var(--farbe-text-2);
    border: 1px solid var(--farbe-linie);
  }
  .punkt { position: relative; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
  .live { color: var(--farbe-gut); border-color: color-mix(in srgb, var(--farbe-gut) 35%, transparent); }
  .live .punkt::after {
    content: '';
    position: absolute;
    inset: -4px;
    border-radius: 50%;
    border: 1.5px solid currentColor;
    animation: puls 2.4s var(--kurve) infinite;
  }
  .verbindet { color: var(--farbe-signal); }
  .verbindet .punkt { animation: blinken 1s steps(2) infinite; }
  .getrennt { color: var(--farbe-warn); background: var(--farbe-warn-grund); border-color: transparent; }
  .lesen .punkt { border-radius: 1px; width: 6px; height: 6px; background: none; border: 1.5px solid currentColor; }

  @keyframes puls {
    0% { transform: scale(0.5); opacity: 0.9; }
    70%, 100% { transform: scale(1.4); opacity: 0; }
  }
  @keyframes blinken { 50% { opacity: 0.2; } }

  .arbeitet {
    position: absolute;
    left: 0;
    right: 0;
    bottom: -1px;
    height: 2px;
    overflow: hidden;
    background: color-mix(in srgb, var(--farbe-signal) 18%, transparent);
  }
  .arbeitet::after {
    content: '';
    position: absolute;
    top: 0;
    bottom: 0;
    width: 30%;
    background: var(--farbe-signal);
    animation: laufband 0.9s var(--kurve) infinite;
  }
  @keyframes laufband { from { left: -30%; } to { left: 100%; } }

  main {
    width: 100%;
    max-width: var(--inhalt-max);
    padding: var(--a-6) var(--a-6) var(--a-8);
  }

  .laden { display: flex; gap: 6px; justify-content: center; padding: var(--a-8) 0; }
  .laden span {
    width: 8px;
    height: 8px;
    background: var(--farbe-text-3);
    border-radius: 1px;
    animation: hopsen 0.9s var(--kurve) infinite;
  }
  .laden span:nth-child(2) { animation-delay: 0.12s; }
  .laden span:nth-child(3) { animation-delay: 0.24s; }
  @keyframes hopsen { 30% { transform: translateY(-6px); background: var(--farbe-signal); } }

  @media (max-width: 1100px) {
    .suche { width: auto; }
    .suche-text, .suche :global(.ui-kbd) { display: none; }
  }
  @media (max-width: 820px) {
    .kopf { padding: 0 var(--a-4); gap: var(--a-3); }
    .nummer, .titel p { display: none; }
    h1 { font-size: var(--text-l); }
    main { padding: var(--a-5) var(--a-4) var(--a-7); }
  }
</style>
