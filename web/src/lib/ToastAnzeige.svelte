<script lang="ts">
  import { toasts } from './toasts.svelte';
</script>

<div class="toasts" role="status" aria-live="polite">
  {#each toasts.liste as t (t.id)}
    <div class="toast toast--{t.art}">
      <span>{t.text}</span>
      <button type="button" aria-label="Schließen" onclick={() => toasts.entfernen(t.id)}
        >×</button
      >
    </div>
  {/each}
</div>

<style>
  .toasts {
    position: fixed;
    right: 1rem;
    bottom: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    z-index: 100;
    max-width: 22rem;
  }
  .toast {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.6rem 0.8rem;
    border-radius: 0.4rem;
    background: var(--flaeche-2);
    color: var(--schrift);
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25);
    font-size: 0.9rem;
  }
  .toast--fehler {
    border-left: 4px solid var(--farbe-fehler);
  }
  .toast--konflikt {
    border-left: 4px solid var(--farbe-warnung);
  }
  .toast--info {
    border-left: 4px solid var(--farbe-akzent);
  }
  .toast button {
    background: none;
    border: none;
    color: inherit;
    cursor: pointer;
    font-size: 1rem;
    line-height: 1;
    padding: 0;
    margin-left: auto;
  }
</style>
