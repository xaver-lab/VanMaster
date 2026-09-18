<script lang="ts">
  // Mehrzeiliges Textfeld. `wachsen` passt die Höhe dem Inhalt an.
  import type { HTMLTextareaAttributes } from 'svelte/elements';
  import './formular.css';

  interface Props extends Omit<HTMLTextareaAttributes, 'value'> {
    wert?: string | null;
    label?: string;
    hinweis?: string;
    fehler?: string;
    zeilen?: number;
    wachsen?: boolean;
    mono?: boolean;
    optional?: boolean;
  }

  let {
    wert = $bindable(''),
    label,
    hinweis,
    fehler,
    zeilen = 4,
    wachsen = true,
    mono = false,
    optional = false,
    id,
    disabled,
    class: klasse = '',
    ...rest
  }: Props = $props();

  const eigeneId = `text-${Math.random().toString(36).slice(2, 8)}`;
  let feldId = $derived(id ?? eigeneId);
  let el = $state<HTMLTextAreaElement>();

  $effect(() => {
    void wert;
    if (!wachsen || !el) return;
    el.style.height = 'auto';
    el.style.height = `${el.scrollHeight + 2}px`;
  });
</script>

<div class="ui-feld {klasse}">
  {#if label}
    <label class="ui-feld-label" for={feldId}>
      {label}{#if optional}<span class="optional">optional</span>{/if}
    </label>
  {/if}
  <div class="ui-eingabe" class:mono class:fehlerhaft={!!fehler} class:gesperrt={disabled}>
    <textarea
      id={feldId}
      bind:this={el}
      bind:value={wert}
      rows={zeilen}
      {disabled}
      aria-invalid={fehler ? true : undefined}
      {...rest}
    ></textarea>
  </div>
  {#if fehler}
    <span class="ui-feld-fehler">{fehler}</span>
  {:else if hinweis}
    <span class="ui-feld-hinweis">{hinweis}</span>
  {/if}
</div>
