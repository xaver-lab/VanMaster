<script lang="ts">
  import { router } from '../lib/router.svelte';
</script>

<section>
  <h1>Bereiche</h1>
  {#if router.route.parameter[0]}
    <p>Bereich: {router.route.parameter[0]}</p>
  {/if}
  <p>Kommt in Phase 6.</p>
</section>
