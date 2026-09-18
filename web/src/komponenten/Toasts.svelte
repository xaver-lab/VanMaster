<script lang="ts">
  // Toast-Stapel unten mittig — wie bisher in docs/js/grund.js `toast()`.
  import { toasts, entfernen } from '../lib/toast.svelte';
</script>

<div class="toasts">
  {#each toasts.liste as t (t.id)}
    <div class="toast toast--{t.art}">
      <span>{t.text}</span>
      <button class="toast-zu" onclick={() => entfernen(t.id)} aria-label="Schließen">×</button>
    </div>
  {/each}
</div>

<style>
  .toasts {
    position: fixed;
    left: 50%;
    bottom: 1.2rem;
    transform: translateX(-50%);
    z-index: 50;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    align-items: center;
    pointer-events: none;
  }
  .toast {
    pointer-events: auto;
    max-width: min(92vw, 520px);
    display: flex;
    align-items: center;
    gap: 0.7rem;
    background: var(--flaeche-hoch);
    border: 1px solid var(--linie-hell);
    border-radius: 99px;
    padding: 0.5rem 0.6rem 0.5rem 1rem;
    box-shadow: var(--schatten);
    font-size: 0.86rem;
  }
  .toast--fehler {
    border-color: var(--warn);
  }
  .toast--erfolg {
    border-color: var(--gut);
  }
  .toast-zu {
    background: var(--flaeche);
    border: 1px solid var(--linie);
    border-radius: 99px;
    padding: 0.1rem 0.5rem;
    font-size: 0.9rem;
    line-height: 1;
  }
</style>
