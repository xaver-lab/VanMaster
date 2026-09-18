<script lang="ts">
  // Auswahlliste. optionen: ['a', 'b'] oder [{ wert: 'a', label: 'A' }].
  import type { HTMLSelectAttributes } from 'svelte/elements';
  import { IconAufklappen } from './icons';
  import './formular.css';

  type Option = string | { wert: string; label: string };

  interface Props extends Omit<HTMLSelectAttributes, 'value'> {
    wert?: string;
    optionen: Option[];
    label?: string;
    hinweis?: string;
    leer?: string;
    klein?: boolean;
  }

  let {
    wert = $bindable(''),
    optionen,
    label,
    hinweis,
    leer,
    klein = false,
    id,
    disabled,
    class: klasse = '',
    ...rest
  }: Props = $props();

  const eigeneId = `wahl-${Math.random().toString(36).slice(2, 8)}`;
  let feldId = $derived(id ?? eigeneId);
  let liste = $derived(optionen.map((o) => (typeof o === 'string' ? { wert: o, label: o } : o)));
</script>

<div class="ui-feld {klasse}">
  {#if label}<label class="ui-feld-label" for={feldId}>{label}</label>{/if}
  <div class="ui-eingabe" class:klein class:gesperrt={disabled}>
    <select id={feldId} bind:value={wert} {disabled} {...rest}>
      {#if leer !== undefined}<option value="">{leer}</option>{/if}
      {#each liste as o (o.wert)}
        <option value={o.wert}>{o.label}</option>
      {/each}
    </select>
    <span class="pfeil"><IconAufklappen size={15} strokeWidth={2} aria-hidden="true" /></span>
  </div>
  {#if hinweis}<span class="ui-feld-hinweis">{hinweis}</span>{/if}
</div>
