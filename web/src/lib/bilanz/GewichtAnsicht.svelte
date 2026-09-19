<script lang="ts">
  // Gewicht — Zuladungsbilanz gegen das zulässige Gesamtgewicht.
  // Gleiche Zahlen wie `python camper.py gewicht` (tools/gewicht.py).
  import { store } from '../daten.svelte';
  import { dezimal } from '../zahlformat';
  import { FortschrittBalken, Karte, Kennzahl, Leerzustand, Rubrik } from '../ui';
  import { IconGewicht, IconWarnung } from '../ui/icons';

  // Ab hier warnt auch die Textausgabe (tools/gewicht.py: SCHWELLE_WARNUNG).
  const SCHWELLE_WARNUNG = 0.9;

  let g = $derived(store.daten?.gewicht);

  let fehlt = $derived((g?.teile_fehlt ?? 0) + (g?.bauteile_fehlt ?? 0));
  let zuladung = $derived(g?.zuladung_erlaubt_kg ?? null);
  let anteil = $derived(zuladung && zuladung > 0 ? (g?.ausbau_kg ?? 0) / zuladung : null);
  let ton = $derived(anteil !== null && anteil >= SCHWELLE_WARNUNG ? 'signal' : 'gut');
</script>

{#if !g}
  <Leerzustand titel="Keine Gewichtsdaten" />
{:else}
  <div class="kennzahlen">
    <Kennzahl
      titel="Ausbau gesamt"
      wert="{dezimal(g.ausbau_kg)} kg"
      icon={IconGewicht}
      zusatz="Stückliste + Einzelteile"
      ton={anteil !== null && anteil >= SCHWELLE_WARNUNG ? 'warn' : 'neutral'}
    />
    <Kennzahl
      titel="Stückliste"
      wert="{dezimal(g.teile_kg)} kg"
      zusatz="{g.teile_gesamt - g.teile_fehlt} von {g.teile_gesamt} Teilen gewogen"
      href="#/teile"
    />
    <Kennzahl
      titel="Einzelteile"
      wert="{dezimal(g.bauteile_kg)} kg"
      zusatz="{g.bauteile_gesamt - g.bauteile_fehlt} von {g.bauteile_gesamt} Teilen gewogen"
      href="#/zuschnitt"
    />
    {#if zuladung !== null}
      <Kennzahl
        titel="Zulässige Zuladung"
        wert="{dezimal(zuladung, 0)} kg"
        zusatz="{dezimal(g.zul_gesamtgewicht_kg ?? 0, 0)} kg − {dezimal(g.leergewicht_kg ?? 0, 0)} kg leer"
        ton="info"
      />
    {/if}
  </div>

  {#if fehlt > 0}
    <Karte ton="signal">
      <p class="hinweis">
        <IconWarnung size={16} strokeWidth={2} aria-hidden="true" />
        {fehlt}
        {fehlt === 1 ? 'Teil hat' : 'Teile haben'} keine Gewichtsangabe. Die Bilanz ist
        unvollständig — sie ist zu niedrig, nie zu hoch.
      </p>
    </Karte>
  {/if}

  <Rubrik titel="Zuladung" />

  {#if zuladung === null}
    <Karte>
      <p class="fehlend">
        Keine Zuladungsbilanz möglich:
        {#if g.leergewicht_kg === null && g.zul_gesamtgewicht_kg === null}
          <code>leergewicht_kg</code> und <code>zul_gesamtgewicht_kg</code> fehlen
        {:else if g.leergewicht_kg === null}
          <code>leergewicht_kg</code> fehlt
        {:else}
          <code>zul_gesamtgewicht_kg</code> fehlt
        {/if}
        im Kopf von <code>vault/Camper.md</code>. Die Werte stehen im Fahrzeugschein.
      </p>
    </Karte>
  {:else if zuladung <= 0}
    <Karte ton="signal">
      <p class="hinweis">
        <IconWarnung size={16} strokeWidth={2} aria-hidden="true" />
        Die zulässige Zuladung ist 0 kg oder weniger — Leergewicht und zulässiges
        Gesamtgewicht in <code>vault/Camper.md</code> prüfen.
      </p>
    </Karte>
  {:else}
    <div class="waage">
      <FortschrittBalken
        wert={(anteil ?? 0) > 1 ? 1 : (anteil ?? 0)}
        ton={ton as 'gut' | 'signal'}
        hoehe={12}
        teilung={10}
        label="Ausbau gegen zulässige Zuladung"
        zahl="{dezimal(g.ausbau_kg, 0)} / {dezimal(zuladung, 0)} kg"
      />
      <p class="legende">
        {Math.round((anteil ?? 0) * 100)} % der Zuladung belegt, noch
        <strong class="zahl">{dezimal(Math.max(0, zuladung - g.ausbau_kg), 0)} kg</strong> frei.
        Ein Strich je 10 %.
      </p>
      {#if anteil !== null && anteil >= SCHWELLE_WARNUNG}
        <p class="warnung">
          <IconWarnung size={15} strokeWidth={2} aria-hidden="true" />
          Der Ausbau liegt {anteil > 1 ? 'über' : 'nahe an'} der zulässigen Zuladung — und
          Wasser, Gas, Gepäck und Personen sind darin noch nicht enthalten.
        </p>
      {/if}
    </div>
  {/if}
{/if}

<style>
  .kennzahlen {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: var(--a-3);
    margin-bottom: var(--a-5);
  }

  .waage { margin-top: var(--a-2); }

  .hinweis,
  .warnung {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    margin: 0;
    font-size: var(--text-m);
  }
  .warnung { margin-top: var(--a-3); color: var(--farbe-warn); font-size: var(--text-s); }

  .legende,
  .fehlend {
    margin: var(--a-2) 0 0;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
  .fehlend { margin: 0; font-size: var(--text-m); }

  .zahl {
    font-family: var(--schrift-mono);
    font-variant-numeric: tabular-nums;
    color: var(--farbe-text);
  }

  code {
    font-family: var(--schrift-mono);
    font-size: 0.9em;
    background: var(--farbe-flaeche-hoch);
    border-radius: var(--r-s);
    padding: 1px 5px;
  }
</style>
