<script lang="ts">
  // Modaler Dialog auf Basis von <dialog>.showModal(): Hintergrund ist inert,
  // Esc schließt, Tab bleibt im Dialog, Fokus kehrt danach zurück.
  // Klick auf den abgedunkelten Rand schließt (außer `festhalten`).
  //   <Dialog bind:offen titel="Teil anlegen">…{#snippet fuss()}…{/snippet}</Dialog>
  import type { Snippet } from 'svelte';
  import { IconSchliessen } from './icons';
  import IconKnopf from './IconKnopf.svelte';

  interface Props {
    offen?: boolean;
    titel: string;
    beschreibung?: string;
    breite?: 's' | 'm' | 'l';
    festhalten?: boolean;
    onschliessen?: () => void;
    children?: Snippet;
    fuss?: Snippet;
  }

  let {
    offen = $bindable(false),
    titel,
    beschreibung,
    breite = 'm',
    festhalten = false,
    onschliessen,
    children,
    fuss,
  }: Props = $props();

  let el = $state<HTMLDialogElement>();
  let vorher: HTMLElement | null = null;
  const titelId = `dlg-${Math.random().toString(36).slice(2, 8)}`;

  $effect(() => {
    if (!el) return;
    if (offen && !el.open) {
      vorher = document.activeElement as HTMLElement | null;
      el.showModal();
      // [data-fokus] gewinnt, dann erstes Eingabefeld, dann Hauptknopf — nie das X
      const ziel =
        el.querySelector<HTMLElement>('[data-fokus]') ??
        el.querySelector<HTMLElement>('.rumpf input, .rumpf textarea, .rumpf select, .fuss button:last-child');
      ziel?.focus();
    } else if (!offen && el.open) {
      el.close();
    }
  });

  function beiClose(): void {
    offen = false;
    onschliessen?.();
    vorher?.focus?.();
    vorher = null;
  }

  function fokusFalle(e: KeyboardEvent): void {
    if (e.key !== 'Tab' || !el) return;
    const fokussierbar = [
      ...el.querySelectorAll<HTMLElement>(
        'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
      ),
    ];
    if (!fokussierbar.length) return;
    const erstes = fokussierbar[0];
    const letztes = fokussierbar[fokussierbar.length - 1];
    if (e.shiftKey && document.activeElement === erstes) {
      e.preventDefault();
      letztes.focus();
    } else if (!e.shiftKey && document.activeElement === letztes) {
      e.preventDefault();
      erstes.focus();
    }
  }

  function randKlick(e: MouseEvent): void {
    if (e.target === el && !festhalten) offen = false;
  }
</script>

<dialog
  bind:this={el}
  class="ui-dialog b-{breite}"
  aria-labelledby={titelId}
  onclose={beiClose}
  oncancel={(e) => {
    if (festhalten) e.preventDefault();
  }}
  onclick={randKlick}
  onkeydown={fokusFalle}
>
  {#if offen}
    <div class="blatt">
      <header>
        <div>
          <h2 id={titelId}>{titel}</h2>
          {#if beschreibung}<p>{beschreibung}</p>{/if}
        </div>
        <IconKnopf icon={IconSchliessen} label="Schließen (Esc)" groesse="s" onclick={() => (offen = false)} />
      </header>
      {#if children}<div class="rumpf">{@render children()}</div>{/if}
      {#if fuss}<footer class="fuss">{@render fuss()}</footer>{/if}
    </div>
  {/if}
</dialog>

<style>
  .ui-dialog {
    padding: 0;
    border: 0;
    background: transparent;
    color: var(--farbe-text);
    max-width: calc(100vw - 32px);
    max-height: calc(100vh - 64px);
    overflow: visible;
  }
  .b-s { width: 420px; }
  .b-m { width: 560px; }
  .b-l { width: 800px; }
  .ui-dialog::backdrop {
    background: var(--abdunkeln);
    backdrop-filter: blur(3px) saturate(0.8);
    animation: rand-ein var(--t-mittel) ease both;
  }
  .ui-dialog[open] .blatt { animation: blatt-ein var(--t-mittel) var(--kurve) both; }

  .blatt {
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 64px);
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie-stark);
    border-top: 3px solid var(--farbe-signal);
    border-radius: var(--r-l);
    box-shadow: var(--schatten-3);
    overflow: hidden;
  }
  header {
    display: flex;
    align-items: flex-start;
    gap: var(--a-3);
    padding: var(--a-5) var(--a-5) var(--a-3);
  }
  header > div { flex: 1; min-width: 0; }
  h2 {
    font-size: var(--text-l);
    font-weight: 700;
    font-stretch: var(--breit);
    letter-spacing: -0.01em;
    text-transform: none;
    color: var(--farbe-text);
  }
  header p { margin-top: 4px; color: var(--farbe-text-2); font-size: var(--text-s); }
  .rumpf { padding: var(--a-2) var(--a-5) var(--a-5); overflow: auto; display: flex; flex-direction: column; gap: var(--a-4); }
  .fuss {
    display: flex;
    justify-content: flex-end;
    gap: var(--a-2);
    padding: var(--a-3) var(--a-5);
    background: var(--farbe-flaeche-hoch);
    border-top: 1px solid var(--farbe-linie);
  }

  @keyframes rand-ein { from { opacity: 0; } }
  @keyframes blatt-ein { from { opacity: 0; transform: translateY(10px) scale(0.985); } }
</style>
