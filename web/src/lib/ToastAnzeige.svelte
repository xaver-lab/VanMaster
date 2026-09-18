<script lang="ts">
  import { toasts } from './toasts.svelte';
</script>

<div class="toasts" role="status" aria-live="polite">
  {#each toasts.liste as t (t.id)}
    <div class="toast {t.art}">
      <span>{t.text}</span>
      <button type="button" aria-label="Schließen" onclick={() => toasts.entfernen(t.id)}>×</button>
    </div>
  {/each}
</div>
