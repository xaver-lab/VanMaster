<script lang="ts">
  // Einzeiliges Eingabefeld mit Beschriftung, Hinweis, Fehler und Einheit
  // (z. B. einheit="mm" oder "€"). `mono` für Maße und Preise.
  import type { HTMLInputAttributes } from 'svelte/elements';
  import type { IconKomponente } from './icons';
  import './formular.css';

  interface Props extends Omit<HTMLInputAttributes, 'value' | 'size'> {
    wert?: string | number | null;
    label?: string;
    hinweis?: string;
    fehler?: string;
    einheit?: string;
    icon?: IconKomponente;
    mono?: boolean;
    klein?: boolean;
    optional?: boolean;
    eingabe?: HTMLInputElement;
  }

  let {
    wert = $bindable(''),
    label,
    hinweis,
    fehler,
    einheit,
    icon: Icon,
    mono = false,
    klein = false,
    optional = false,
    eingabe = $bindable(),
    id,
    disabled,
    class: klasse = '',
    ...rest
  }: Props = $props();

  const eigeneId = `feld-${Math.random().toString(36).slice(2, 8)}`;
  let feldId = $derived(id ?? eigeneId);
</script>

<div class="ui-feld {klasse}">
  {#if label}
    <label class="ui-feld-label" for={feldId}>
      {label}{#if optional}<span class="optional">optional</span>{/if}
    </label>
  {/if}
  <div class="ui-eingabe" class:mono class:klein class:fehlerhaft={!!fehler} class:gesperrt={disabled}>
    {#if Icon}<span class="vorne"><Icon size={16} strokeWidth={1.8} aria-hidden="true" /></span>{/if}
    <input
      id={feldId}
      bind:value={wert}
      bind:this={eingabe}
      {disabled}
      aria-invalid={fehler ? true : undefined}
      aria-describedby={fehler || hinweis ? `${feldId}-info` : undefined}
      {...rest}
    />
    {#if einheit}<span class="einheit">{einheit}</span>{/if}
  </div>
  {#if fehler}
    <span class="ui-feld-fehler" id="{feldId}-info">{fehler}</span>
  {:else if hinweis}
    <span class="ui-feld-hinweis" id="{feldId}-info">{hinweis}</span>
  {/if}
</div>
