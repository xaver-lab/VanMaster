<script lang="ts">
  // Quadratischer Knopf nur mit Icon. `label` ist Pflicht (Tooltip + Vorlesetext).
  import type { HTMLButtonAttributes } from 'svelte/elements';
  import type { IconKomponente } from './icons';
  import Knopf from './Knopf.svelte';

  interface Props extends Omit<HTMLButtonAttributes, 'children'> {
    icon: IconKomponente;
    label: string;
    variante?: 'primaer' | 'sekundaer' | 'leise' | 'gefaehrlich';
    groesse?: 's' | 'm';
    aktiv?: boolean;
  }

  let { icon, label, variante = 'leise', groesse = 'm', aktiv = false, ...rest }: Props = $props();
</script>

<Knopf {icon} {label} {variante} {groesse} {aktiv} nurIcon {...rest} />
