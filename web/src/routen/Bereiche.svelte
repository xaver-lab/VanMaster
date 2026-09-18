<script lang="ts">
  import { router } from '../lib/router.svelte';
</script>

<p class="leer">
  {#if router.route.parameter[0]}Bereich „{router.route.parameter[0]}“ — {/if}Kommt in Phase 6.
</p>
