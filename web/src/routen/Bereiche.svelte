<script lang="ts">
  import { router } from '../lib/router.svelte';
  import BereichListe from '../lib/bereiche/BereichListe.svelte';
  import BereichDetail from '../lib/bereiche/BereichDetail.svelte';

  const name = $derived(router.route.parameter[0] ?? null);
</script>

{#if name}
  <BereichDetail {name} />
{:else}
  <BereichListe />
{/if}
