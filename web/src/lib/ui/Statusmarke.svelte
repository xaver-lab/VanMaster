<script lang="ts">
  // Statusmarke: Symbol + Wort. Jede Form ist auch ohne Farbe unterscheidbar
  // (Kreis leer / halb / voll mit Haken / durchgestrichen / Sperrbalken).
  // `kompakt` zeigt nur das Symbol (Wort als Tooltip). Mit `onclick` wird
  // sie zum Knopf (z. B. Status weiterschalten).
  import { STATUS_TEXT, istStatus, type Status } from './status';

  interface Props {
    status: Status | string;
    kompakt?: boolean;
    onclick?: (e: MouseEvent) => void;
    titel?: string;
  }

  let { status, kompakt = false, onclick, titel }: Props = $props();

  let s = $derived<Status>(istStatus(status) ? status : 'offen');
  let text = $derived(STATUS_TEXT[s]);
</script>

{#snippet symbol()}
  <svg class="symbol" viewBox="0 0 14 14" width="13" height="13" aria-hidden="true">
    {#if s === 'offen'}
      <circle cx="7" cy="7" r="5.25" fill="none" stroke="currentColor" stroke-width="1.5" />
    {:else if s === 'laeuft'}
      <circle cx="7" cy="7" r="5.25" fill="none" stroke="currentColor" stroke-width="1.5" />
      <path d="M7 3.5 A3.5 3.5 0 0 1 7 10.5 Z" fill="currentColor" />
    {:else if s === 'erledigt'}
      <circle cx="7" cy="7" r="6" fill="currentColor" />
      <path d="M4.4 7.2 6.2 9 9.7 5.2" fill="none" style="stroke: var(--farbe-flaeche)" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" />
    {:else if s === 'verworfen'}
      <circle cx="7" cy="7" r="5.25" fill="none" stroke="currentColor" stroke-width="1.5" />
      <path d="M3.4 10.6 10.6 3.4" stroke="currentColor" stroke-width="1.5" />
    {:else}
      <circle cx="7" cy="7" r="6" fill="currentColor" />
      <path d="M4.2 7h5.6" style="stroke: var(--farbe-flaeche)" stroke-width="1.8" stroke-linecap="round" />
    {/if}
  </svg>
{/snippet}

{#if onclick}
  <button type="button" class="ui-status {s}" class:kompakt {onclick} title={titel ?? text} aria-label={kompakt ? text : undefined}>
    {@render symbol()}{#if !kompakt}<span>{text}</span>{/if}
  </button>
{:else}
  <span class="ui-status {s}" class:kompakt title={kompakt ? text : titel} role={kompakt ? 'img' : undefined} aria-label={kompakt ? text : undefined}>
    {@render symbol()}{#if !kompakt}<span>{text}</span>{/if}
  </span>
{/if}

<style>
  .ui-status {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    height: 22px;
    padding: 0 8px 0 6px;
    border-radius: var(--r-s);
    border: 1px solid transparent;
    font-size: var(--text-xs);
    font-weight: 600;
    letter-spacing: 0.01em;
    line-height: 1;
    white-space: nowrap;
    vertical-align: middle;
    background: none;
  }
  button.ui-status { cursor: pointer; transition: filter var(--t-kurz), transform var(--t-kurz) var(--kurve); }
  button.ui-status:hover { filter: brightness(0.96) saturate(1.1); }
  button.ui-status:active { transform: scale(0.96); }
  .symbol { flex: none; }
  .kompakt { padding: 0; width: 22px; justify-content: center; }

  .offen { color: var(--farbe-text-2); border-color: var(--farbe-linie-stark); }
  .laeuft { color: var(--farbe-signal); background: var(--farbe-signal-grund); }
  .erledigt { color: var(--farbe-gut); background: var(--farbe-gut-grund); }
  .verworfen { color: var(--farbe-text-2); background: var(--farbe-flaeche-hoch); }
  .verworfen span { text-decoration: line-through; text-decoration-thickness: 1px; }
  .blockiert { color: var(--farbe-warn); background: var(--farbe-warn-grund); }
  .kompakt.offen { border-color: transparent; }
  .kompakt { background: none; }
</style>
