<script lang="ts">
  import { ANSICHTEN, TITEL, router, type Ansicht } from './router.svelte';
  import { store } from './daten.svelte';
  import { theme } from './theme.svelte';
  import { toasts } from './toasts.svelte';
  import { paletteOeffnen } from './palette.svelte';
  import {
    IconAufgaben,
    IconBereiche,
    IconMedien,
    IconStart,
    IconTeile,
    IconZuschnitt,
    type IconKomponente,
  } from './ui/icons';
  import Kbd from './ui/Kbd.svelte';

  const ICON: Record<(typeof ANSICHTEN)[number], IconKomponente> = {
    start: IconStart,
    bereiche: IconBereiche,
    aufgaben: IconAufgaben,
    teile: IconTeile,
    zuschnitt: IconZuschnitt,
    medien: IconMedien,
  };

  let k = $derived(store.daten?.kennzahlen);

  let zaehler = $derived.by((): Partial<Record<Ansicht, number>> => {
    const d = store.daten;
    if (!d || !k) return {};
    return {
      bereiche: d.bereiche.length,
      aufgaben: k.aufgaben_gesamt - k.aufgaben_fertig,
      teile: k.teile,
      zuschnitt: k.bauteile || undefined,
      medien: d.medien.length,
    };
  });

  let anteil = $derived(k && k.aufgaben_gesamt ? k.aufgaben_fertig / k.aufgaben_gesamt : 0);

  let stand = $derived.by(() => {
    const roh = store.daten?.erzeugt;
    if (!roh) return '—';
    const d = new Date(roh);
    if (isNaN(d.getTime())) return roh;
    return `${d.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit' })} · ${d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
  });

  window.addEventListener('keydown', (e: KeyboardEvent) => {
    const aktiv = document.activeElement as HTMLElement | null;
    const imFeld = /^(INPUT|SELECT|TEXTAREA)$/.test(aktiv?.tagName ?? '') || !!aktiv?.isContentEditable;
    // Offener Dialog: der kümmert sich selbst um Esc und Tastatur.
    if (document.querySelector('dialog[open]')) return;
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      paletteOeffnen();
      return;
    }
    if (e.key === 'Escape') {
      toasts.liste = [];
      if (imFeld) aktiv?.blur();
      return;
    }
    if (imFeld || e.ctrlKey || e.metaKey || e.altKey) return;
    if (e.key === '/') {
      e.preventDefault();
      paletteOeffnen();
      return;
    }
    if (e.key.toLowerCase() === 't') {
      theme.umschalten();
      return;
    }
    const nummer = Number(e.key);
    if (nummer >= 1 && nummer <= ANSICHTEN.length) router.gehe(ANSICHTEN[nummer - 1]);
  });
</script>

<aside class="schiene">
  <a class="marke" href="#/start" aria-label="VanMaster — Start">
    <svg class="van" viewBox="0 0 44 26" width="44" height="26" aria-hidden="true">
      <path
        d="M3 19.5V9.2C3 7.4 4.4 6 6.2 6H27.5c.9 0 1.7.4 2.3 1l5.6 6.1 4.1 1.2c.9.3 1.5 1.1 1.5 2v3.2H3Z"
        class="karosse"
      />
      <path d="M29 8.4h-3.6v5h8.2L29 8.4Z" class="fenster" />
      <path d="M8 10h14" class="naht" />
      <circle cx="11" cy="20" r="3.4" class="rad" />
      <circle cx="33" cy="20" r="3.4" class="rad" />
    </svg>
    <span class="wortmarke">
      <span class="wort">VanMaster</span>
      <span class="unter">Renault Master · 2013</span>
    </span>
  </a>

  <div class="tacho" title="{Math.round(anteil * 100)} % der Aufgaben erledigt">
    <div class="tacho-kopf">
      <span>Ausbau</span>
      <span class="wert">{Math.round(anteil * 100)}<small>%</small></span>
    </div>
    <div class="tacho-skala" aria-hidden="true">
      <span class="fuellung" style:width="{anteil * 100}%"></span>
    </div>
  </div>

  <nav class="hauptnav" aria-label="Hauptnavigation">
    {#each ANSICHTEN as ansicht, i}
      {@const Icon = ICON[ansicht]}
      {@const zahl = zaehler[ansicht]}
      <a
        href="#/{ansicht}"
        class:aktiv={router.route.ansicht === ansicht}
        aria-current={router.route.ansicht === ansicht ? 'page' : undefined}
        title="{TITEL[ansicht]} ({i + 1})"
      >
        <span class="nr">0{i + 1}</span>
        <Icon size={17} strokeWidth={1.8} aria-hidden="true" />
        <span class="text">{TITEL[ansicht]}</span>
        {#if zahl}<span class="anzahl">{zahl}</span>{/if}
      </a>
    {/each}
  </nav>

  <div class="fuss">
    <div class="kuerzel">
      <span><Kbd tasten="1–6" /> Ansicht</span>
      <span><Kbd tasten="T" /> Thema</span>
      <span><Kbd tasten="/" /> Suchen</span>
    </div>
    <p class="stand"><span>Stand</span> {stand}</p>
  </div>
</aside>

<style>
  .schiene {
    position: sticky;
    top: 0;
    flex: 0 0 var(--schiene);
    width: var(--schiene);
    height: 100vh;
    display: flex;
    flex-direction: column;
    gap: var(--a-5);
    padding: var(--a-5) var(--a-3) var(--a-4);
    background: var(--farbe-flaeche-tief);
    border-right: 1px solid var(--farbe-linie);
    overflow-y: auto;
    scrollbar-width: none;
  }

  /* Marke */
  .marke {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 var(--a-2);
    color: var(--farbe-text);
    text-decoration: none;
  }
  .van { flex: none; }
  .karosse { fill: var(--farbe-text); }
  .fenster { fill: var(--farbe-flaeche-tief); }
  .naht { stroke: var(--farbe-signal); stroke-width: 2; stroke-linecap: round; }
  .rad { fill: var(--farbe-flaeche-tief); stroke: var(--farbe-text); stroke-width: 2.2; }
  .wortmarke { display: flex; flex-direction: column; line-height: 1.05; min-width: 0; }
  .wort { font-size: 1.12rem; font-weight: 800; font-stretch: 118%; letter-spacing: -0.02em; }
  .unter {
    margin-top: 3px;
    font-family: var(--schrift-mono);
    font-size: 0.625rem;
    color: var(--farbe-text-2);
    letter-spacing: 0.02em;
    white-space: nowrap;
  }

  /* Tacho — Gesamtfortschritt, immer sichtbar */
  .tacho { padding: 0 var(--a-2); }
  .tacho-kopf {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 6px;
    font-size: var(--text-xs);
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }
  .tacho-kopf .wert {
    font-family: var(--schrift-mono);
    font-size: var(--text-s);
    font-weight: 600;
    letter-spacing: 0;
    color: var(--farbe-text);
  }
  .tacho-kopf small { font-size: 0.7em; color: var(--farbe-text-2); margin-left: 1px; }
  .tacho-skala {
    position: relative;
    height: 10px;
    border-bottom: 1px solid var(--farbe-linie-stark);
    background-image:
      linear-gradient(to right, var(--farbe-linie-stark) 1px, transparent 1px),
      linear-gradient(to right, var(--farbe-text-3) 1px, transparent 1px);
    background-size: 10% 4px, 50% 9px;
    background-position: left bottom, left bottom;
    background-repeat: repeat-x;
  }
  .fuellung {
    position: absolute;
    left: 0;
    bottom: -1px;
    height: 3px;
    background: var(--farbe-signal);
    transition: width var(--t-lang) var(--kurve);
  }

  /* Navigation */
  .hauptnav { display: flex; flex-direction: column; gap: 2px; }
  .hauptnav a {
    position: relative;
    display: flex;
    align-items: center;
    gap: 10px;
    height: 38px;
    padding: 0 var(--a-2);
    border-radius: var(--r-m);
    color: var(--farbe-text-2);
    text-decoration: none;
    font-size: var(--text-m);
    font-weight: 550;
    transition: background-color var(--t-kurz), color var(--t-kurz);
  }
  .hauptnav a:hover { background: color-mix(in srgb, var(--farbe-flaeche) 60%, transparent); color: var(--farbe-text); }
  .hauptnav a.aktiv {
    background: var(--farbe-flaeche);
    color: var(--farbe-text);
    box-shadow: var(--schatten-1), inset 0 0 0 1px var(--farbe-linie);
  }
  .hauptnav a.aktiv::before {
    content: '';
    position: absolute;
    left: -12px;
    top: 9px;
    bottom: 9px;
    width: 3px;
    border-radius: 0 2px 2px 0;
    background: var(--farbe-signal);
  }
  .nr {
    width: 18px;
    font-family: var(--schrift-mono);
    font-size: 0.6875rem;
    color: var(--farbe-text-3);
  }
  .aktiv .nr { color: var(--farbe-signal); }
  .text { flex: 1; min-width: 0; }
  .anzahl {
    font-family: var(--schrift-mono);
    font-size: 0.6875rem;
    color: var(--farbe-text-2);
    font-variant-numeric: tabular-nums;
  }

  /* Fuß */
  .fuss {
    margin-top: auto;
    display: flex;
    flex-direction: column;
    gap: var(--a-3);
    padding: var(--a-3) var(--a-2) 0;
    border-top: 1px solid var(--farbe-linie);
  }
  .kuerzel { display: flex; flex-direction: column; gap: 6px; font-size: var(--text-xs); color: var(--farbe-text-2); }
  .kuerzel span { display: flex; align-items: center; gap: 8px; }
  .kuerzel :global(.ui-kbd) { min-width: 34px; }
  .stand { font-family: var(--schrift-mono); font-size: 0.6875rem; color: var(--farbe-text-2); }
  .stand span { color: var(--farbe-text-3); }

  @media (max-width: 820px) {
    .schiene { --schiene: 64px; padding: var(--a-4) var(--a-2); align-items: center; }
    .wortmarke, .tacho, .nr, .text, .anzahl, .fuss { display: none; }
    .marke { padding: 0; }
    .van { width: 36px; }
    .hauptnav a { width: 44px; justify-content: center; padding: 0; }
    .hauptnav a.aktiv::before { left: -8px; }
  }
</style>
