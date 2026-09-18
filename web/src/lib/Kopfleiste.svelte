<script lang="ts">
  import { ANSICHTEN, router, type Ansicht } from './router.svelte';
  import { store } from './daten.svelte';
  import { theme } from './theme.svelte';
  import { toasts } from './toasts.svelte';

  const TITEL: Record<Ansicht, string> = {
    start: 'Start',
    aufgaben: 'Aufgaben',
    bereiche: 'Bereiche',
    teile: 'Teile',
    zuschnitt: 'Zuschnitt',
    medien: 'Medien',
  };

  function paletteOeffnen(): void {
    // Platzhalter — die Befehlspalette kommt in Phase 8.
    toasts.info('Befehlspalette folgt später (Strg+K).');
  }

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
    if (imFeld) return;
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

<header class="kopfleiste">
  <nav aria-label="Hauptnavigation">
    {#each ANSICHTEN as ansicht}
      <button
        type="button"
        class:aktiv={router.route.ansicht === ansicht}
        onclick={() => router.gehe(ansicht)}
      >
        {TITEL[ansicht]}
      </button>
    {/each}
  </nav>
  <div class="status">
    {#if !store.darfSchreiben}
      <span class="marke">nur lesen</span>
    {:else}
      <span
        class="punkt punkt--{store.verbindung}"
        title={`Live-Verbindung: ${store.verbindung}`}
      ></span>
    {/if}
    <button type="button" onclick={paletteOeffnen} aria-label="Befehlspalette (Strg+K)">⌘K</button>
    <button
      type="button"
      onclick={() => theme.umschalten()}
      aria-label="Hell/Dunkel umschalten (t)"
    >
      {theme.aktuell === 'hell' ? '☾' : '☀'}
    </button>
  </div>
</header>

<style>
  .kopfleiste {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.6rem 1rem;
    border-bottom: 1px solid var(--rand);
    background: var(--flaeche);
  }
  nav {
    display: flex;
    gap: 0.25rem;
    flex-wrap: wrap;
  }
  nav button {
    background: none;
    border: none;
    color: var(--schrift-schwach);
    padding: 0.4rem 0.7rem;
    border-radius: 0.4rem;
    cursor: pointer;
    font: inherit;
  }
  nav button.aktiv {
    background: var(--flaeche-2);
    color: var(--schrift);
  }
  .status {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  .status button {
    background: none;
    border: 1px solid var(--rand);
    border-radius: 0.4rem;
    color: var(--schrift);
    cursor: pointer;
    padding: 0.3rem 0.5rem;
  }
  .marke {
    font-size: 0.8rem;
    color: var(--schrift-schwach);
    border: 1px solid var(--rand);
    border-radius: 0.4rem;
    padding: 0.2rem 0.5rem;
  }
  .punkt {
    width: 0.6rem;
    height: 0.6rem;
    border-radius: 50%;
    display: inline-block;
    background: var(--schrift-schwach);
  }
  .punkt--verbunden {
    background: var(--farbe-erfolg);
  }
  .punkt--getrennt,
  .punkt--verbindet {
    background: var(--farbe-warnung);
  }
</style>
