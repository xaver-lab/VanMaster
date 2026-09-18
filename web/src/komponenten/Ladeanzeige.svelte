<script lang="ts">
  // Kleine, wiederverwendbare Lade-/Fehleranzeige.
  let { text = 'lädt …' }: { text?: string } = $props();
</script>

<div class="ladeanzeige">
  <span class="dreher" aria-hidden="true"></span>
  <span>{text}</span>
</div>

<style>
  .ladeanzeige {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: var(--gedaempft);
    padding: 2rem 0;
    justify-content: center;
    font-size: 0.9rem;
  }
  .dreher {
    width: 1rem;
    height: 1rem;
    border-radius: 50%;
    border: 2px solid var(--linie-hell);
    border-top-color: var(--akzent);
    animation: drehen 0.7s linear infinite;
  }
  @keyframes drehen {
    to {
      transform: rotate(360deg);
    }
  }
</style>
