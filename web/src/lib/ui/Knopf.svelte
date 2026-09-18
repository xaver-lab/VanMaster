<script lang="ts">
  // Knopf — primär (eine Hauptaktion je Bereich), sekundär, leise, gefährlich.
  // Mit `href` wird ein Link daraus. `nurIcon` braucht `label` (Vorlesetext).
  import type { Snippet } from 'svelte';
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconKomponente } from './icons';
  import { IconLaedt } from './icons';

  type Variante = 'primaer' | 'sekundaer' | 'leise' | 'gefaehrlich';

  interface Props extends Omit<HTMLButtonAttributes, 'children'> {
    variante?: Variante;
    groesse?: 's' | 'm';
    icon?: IconKomponente;
    iconRechts?: IconKomponente;
    nurIcon?: boolean;
    label?: string;
    href?: string;
    laedt?: boolean;
    aktiv?: boolean;
    kbd?: string;
    voll?: boolean;
    children?: Snippet;
  }

  let {
    variante = 'sekundaer',
    groesse = 'm',
    icon: Icon,
    iconRechts: IconRechts,
    nurIcon = false,
    label,
    href,
    laedt = false,
    aktiv = false,
    kbd,
    voll = false,
    type = 'button',
    disabled,
    class: klasse = '',
    children,
    ...rest
  }: Props = $props();

  let iconGroesse = $derived(groesse === 's' ? 14 : 16);
</script>

{#snippet inhalt()}
  {#if laedt}
    <IconLaedt size={iconGroesse} strokeWidth={2} class="ui-drehen" />
  {:else if Icon}
    <Icon size={iconGroesse} strokeWidth={1.9} aria-hidden="true" />
  {/if}
  {#if nurIcon}
    <span class="nur-vorlesen">{label}</span>
  {:else if children}
    <span class="beschriftung">{@render children()}</span>
  {/if}
  {#if IconRechts}<IconRechts size={iconGroesse} strokeWidth={1.9} aria-hidden="true" />{/if}
  {#if kbd}<kbd>{kbd}</kbd>{/if}
{/snippet}

{#if href}
  <a
    {href}
    class="ui-knopf {variante} g-{groesse} {klasse}"
    class:nur-icon={nurIcon}
    class:voll
    class:aktiv
    title={nurIcon ? label : undefined}
    aria-label={nurIcon ? label : undefined}
  >
    {@render inhalt()}
  </a>
{:else}
  <button
    {type}
    class="ui-knopf {variante} g-{groesse} {klasse}"
    class:nur-icon={nurIcon}
    class:voll
    class:aktiv
    disabled={disabled || laedt}
    aria-busy={laedt || undefined}
    title={nurIcon ? label : undefined}
    aria-label={nurIcon ? label : undefined}
    {...rest}
  >
    {@render inhalt()}
  </button>
{/if}

<style>
  .ui-knopf {
    --h: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    height: var(--h);
    padding: 0 14px;
    border: 1px solid transparent;
    border-radius: var(--r-m);
    font-size: var(--text-s);
    font-weight: 600;
    line-height: 1;
    white-space: nowrap;
    text-decoration: none;
    color: var(--farbe-text);
    background: none;
    transition:
      background-color var(--t-kurz),
      border-color var(--t-kurz),
      color var(--t-kurz),
      transform var(--t-kurz) var(--kurve),
      box-shadow var(--t-kurz);
    -webkit-user-select: none;
    user-select: none;
  }
  .g-s { --h: 28px; padding: 0 10px; gap: 5px; font-size: var(--text-xs); border-radius: var(--r-s); }
  .voll { width: 100%; }
  .nur-icon { width: var(--h); padding: 0; }

  .ui-knopf:active:not(:disabled) { transform: translateY(1px); }
  .ui-knopf:disabled { opacity: 0.5; }

  .primaer {
    background: var(--farbe-signal);
    color: var(--farbe-auf-signal);
    box-shadow: inset 0 -2px 0 rgb(0 0 0 / 0.16), var(--schatten-1);
  }
  .primaer:hover:not(:disabled) { background: color-mix(in srgb, var(--farbe-signal) 88%, var(--farbe-text)); }

  .sekundaer {
    background: var(--farbe-flaeche);
    border-color: var(--farbe-linie-stark);
    box-shadow: inset 0 -1px 0 var(--farbe-linie);
  }
  .sekundaer:hover:not(:disabled) { background: var(--farbe-flaeche-hoch); border-color: var(--farbe-text-3); }

  .leise { color: var(--farbe-text-2); }
  .leise:hover:not(:disabled),
  .leise.aktiv { background: var(--farbe-flaeche-hoch); color: var(--farbe-text); }

  .gefaehrlich { color: var(--farbe-warn); border-color: color-mix(in srgb, var(--farbe-warn) 45%, transparent); }
  .gefaehrlich:hover:not(:disabled) { background: var(--farbe-warn); border-color: var(--farbe-warn); color: var(--farbe-flaeche); }

  .beschriftung { display: inline-flex; align-items: center; }

  kbd {
    margin-left: 4px;
    font-family: var(--schrift-mono);
    font-size: 0.68rem;
    font-weight: 500;
    padding: 2px 5px;
    border-radius: var(--r-s);
    border: 1px solid currentColor;
    opacity: 0.55;
  }

  :global(.ui-drehen) { animation: ui-drehen 0.9s linear infinite; }
  @keyframes ui-drehen { to { transform: rotate(360deg); } }
</style>
