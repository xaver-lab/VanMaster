<script lang="ts">
  import { router } from '../lib/router.svelte';
  import Leerzustand from '../lib/ui/Leerzustand.svelte';
  import Knopf from '../lib/ui/Knopf.svelte';
  import { IconBereiche, IconPfeil } from '../lib/ui/icons';

  let name = $derived(router.route.parameter[0]);
</script>

<Leerzustand
  icon={IconBereiche}
  marke="Phase 6"
  titel={name ? `Arbeitsraum „${name}“ entsteht gerade` : 'Bereiche entstehen gerade'}
  text="Hier stehen bald Beschreibung, Stand, Auslegung, Notizen und Aufgaben eines Bereichs — direkt bearbeitbar."
>
  <Knopf href="#/start" variante="sekundaer" iconRechts={IconPfeil}>Zur Übersicht</Knopf>
</Leerzustand>
