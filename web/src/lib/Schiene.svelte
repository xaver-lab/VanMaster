<script lang="ts">
  import { ANSICHTEN, TITEL, router, type Ansicht } from './router.svelte';
  import { store } from './daten.svelte';
  import { theme } from './theme.svelte';
  import { toasts } from './toasts.svelte';
  import { paletteOeffnen } from './palette.svelte';

  const ICON: Record<Ansicht, string> = {
    start: '◉',
    bereiche: '▤',
    aufgaben: '✓',
    teile: '◫',
    zuschnitt: '▭',
    medien: '▦',
  };

  let offen = $derived.by(() => {
    const k = store.daten?.kennzahlen;
    return k ? k.aufgaben_gesamt - k.aufgaben_fertig : 0;
  });

  let stand = $derived.by(() => {
    const roh = store.daten?.erzeugt;
    if (!roh) return 'lädt …';
    const d = new Date(roh);
    if (isNaN(d.getTime())) return `Stand ${roh}`;
    return `Stand ${d.toLocaleDateString('de-DE')} ${d.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
  });

  window.addEventListener('keydown', (e: KeyboardEvent) => {
    const imFeld = /^(INPUT|SELECT|TEXTAREA)$/.test(
      (document.activeElement?.tagName as string) ?? '',
    );
    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      paletteOeffnen();
      return;
    }
    if (e.key === 'Escape') {
      toasts.liste = [];
      if (imFeld) (document.activeElement as HTMLElement).blur();
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
  <div class="marke">
    <span class="zeichen">🚐</span>
    <span class="wort">VanMaster</span>
  </div>

  <nav class="hauptnav" aria-label="Hauptnavigation">
    {#each ANSICHTEN as ansicht, i}
      <button
        type="button"
        class:aktiv={router.route.ansicht === ansicht}
        title={`${TITEL[ansicht]} (${i + 1})`}
        onclick={() => router.gehe(ansicht)}
      >
        <span class="icon">{ICON[ansicht]}</span>
        <span class="text">{TITEL[ansicht]}</span>
        {#if ansicht === 'aufgaben'}<span class="pille">{offen || ''}</span>{/if}
      </button>
    {/each}
  </nav>

  <div class="schienenfuss">
    <button type="button" class="flachknopf" title="Hell / dunkel (T)" onclick={() => theme.umschalten()}>
      ◐<span class="text">Ansicht</span>
    </button>
    <p class="stand">{stand}</p>
  </div>
</aside>
