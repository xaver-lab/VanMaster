<script lang="ts">
  import { store } from '../lib/daten.svelte';

  const euro = new Intl.NumberFormat('de-DE', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 });

  let k = $derived(store.daten?.kennzahlen);
  let anteil = $derived(k && k.aufgaben_gesamt ? Math.round((100 * k.aufgaben_fertig) / k.aufgaben_gesamt) : 0);
</script>

{#if store.daten && k}
  <div class="kennzahlen">
    <div class="kachel">
      <div>
        <div class="titel">Aufgaben</div>
        <div class="wert">{anteil} %</div>
        <div class="zusatz">{k.aufgaben_fertig} von {k.aufgaben_gesamt} erledigt</div>
      </div>
    </div>
    <div class="kachel">
      <div>
        <div class="titel">Bereiche</div>
        <div class="wert">{store.daten.bereiche.length}</div>
      </div>
    </div>
    <div class="kachel">
      <div>
        <div class="titel">Teile</div>
        <div class="wert">{k.teile}</div>
        <div class="zusatz">{k.bauteile} Einzelteile</div>
      </div>
    </div>
    <div class="kachel">
      <div>
        <div class="titel">Kosten</div>
        <div class="wert">{euro.format(k.kosten)}</div>
        <div class="zusatz">{euro.format(k.kosten_bestellt)} bestellt</div>
      </div>
    </div>
    <div class="kachel">
      <div>
        <div class="titel">Entscheidungen</div>
        <div class="wert">{k.offene_entscheidungen}</div>
        <div class="zusatz">offen</div>
      </div>
    </div>
  </div>
  <p class="leer">Die vollständige Startseite kommt in Phase 8.</p>
{/if}
