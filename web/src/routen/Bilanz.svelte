<script lang="ts">
  // Bilanz — die drei Auswertungen, die es bisher nur auf der Kommandozeile
  // gab: `camper budget`, `camper gewicht`, `camper material`.
  // Alle drei sind reine Auswertungen über den vorhandenen Bestand, deshalb
  // eine Ansicht mit Reitern statt drei Einträgen in der Schiene.
  // Der aktive Reiter steht in der Adresse (#/bilanz/gewicht), damit er
  // teilbar und über den Zurück-Knopf erreichbar bleibt.
  import { router } from '../lib/router.svelte';
  import { Tabs } from '../lib/ui';
  import { IconEuro, IconGewicht, IconZuschnitt } from '../lib/ui/icons';
  import BudgetAnsicht from '../lib/bilanz/BudgetAnsicht.svelte';
  import GewichtAnsicht from '../lib/bilanz/GewichtAnsicht.svelte';
  import MaterialAnsicht from '../lib/bilanz/MaterialAnsicht.svelte';

  const TABS = [
    { id: 'budget', label: 'Budget', icon: IconEuro },
    { id: 'gewicht', label: 'Gewicht', icon: IconGewicht },
    { id: 'material', label: 'Material', icon: IconZuschnitt },
  ];

  let aktiv = $derived.by(() => {
    const p = router.route.parameter[0] ?? '';
    return TABS.some((t) => t.id === p) ? p : 'budget';
  });
</script>

<div class="bilanz">
  <Tabs tabs={TABS} {aktiv} label="Auswertung" onwechsel={(id) => router.gehe('bilanz', id)} />

  <div class="inhalt">
    {#if aktiv === 'gewicht'}
      <GewichtAnsicht />
    {:else if aktiv === 'material'}
      <MaterialAnsicht />
    {:else}
      <BudgetAnsicht />
    {/if}
  </div>
</div>

<style>
  .bilanz { display: flex; flex-direction: column; gap: var(--a-6); }
</style>
