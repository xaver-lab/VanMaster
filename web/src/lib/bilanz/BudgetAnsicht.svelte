<script lang="ts">
  // Budget — Zielbudget gegen bezahlt und geplant, je Kategorie.
  // Gleiche Zahlen wie `python camper.py budget`; gerechnet wird im Kern
  // (tools/budget.py), hier wird nur angezeigt.
  import { store } from '../daten.svelte';
  import { dezimal } from '../zahlformat';
  import { FortschrittBalken, Karte, Kennzahl, Leerzustand, Rubrik } from '../ui';
  import { IconEuro, IconWarnung } from '../ui/icons';

  let b = $derived(store.daten?.budget);

  // Anteil der Prognose am Ziel; ohne Ziel gibt es keinen Balken.
  let anteilBezahlt = $derived(b?.ziel ? b.bezahlt / b.ziel : 0);
  let anteilGeplant = $derived(b?.ziel ? b.geplant / b.ziel : 0);
  let ueberzogen = $derived(!!b?.ziel && b.prognose > b.ziel);

  // Kategorien ohne jede Ausgabe stehen nur im Weg.
  let kategorien = $derived((b?.kategorien ?? []).filter((k) => k.prognose > 0 || k.budget));
</script>

{#if !b}
  <Leerzustand titel="Keine Budgetdaten" />
{:else}
  <div class="kennzahlen">
    <Kennzahl titel="Bezahlt" wert="{dezimal(b.bezahlt, 0)} €" icon={IconEuro} zusatz="bestellt, geliefert, verbaut" />
    <Kennzahl titel="Geplant" wert="{dezimal(b.geplant, 0)} €" zusatz="Idee, Recherche, entschieden" />
    <Kennzahl
      titel="Prognose"
      wert="{dezimal(b.prognose, 0)} €"
      ton={ueberzogen ? 'warn' : 'neutral'}
      zusatz="bezahlt + geplant"
    />
    {#if b.ziel}
      <Kennzahl
        titel="Ziel"
        wert="{dezimal(b.ziel, 0)} €"
        zusatz={b.differenz_prognose !== null && b.differenz_prognose !== undefined
          ? `${b.differenz_prognose <= 0 ? dezimal(-b.differenz_prognose, 0) + ' € frei' : dezimal(b.differenz_prognose, 0) + ' € darüber'}`
          : undefined}
        ton={ueberzogen ? 'warn' : 'gut'}
      />
    {/if}
  </div>

  {#if b.ziel}
    <div class="gesamtbalken">
      <FortschrittBalken
        wert={anteilBezahlt}
        zusatz={anteilGeplant}
        ton={ueberzogen ? 'signal' : 'gut'}
        hoehe={10}
        teilung={10}
        label="Prognose gegen Ziel"
        zahl="{dezimal(b.prognose, 0)} / {dezimal(b.ziel, 0)} €"
      />
      <p class="legende">
        Gefüllt = bezahlt, schraffiert = geplant. Ein Strich je 10 % des Ziels.
      </p>
    </div>
  {:else}
    <Karte ton="signal">
      <p class="hinweis">
        <IconWarnung size={16} strokeWidth={2} aria-hidden="true" />
        Kein Zielbudget gesetzt. <code>budget: 6000</code> in den Kopf von
        <code>vault/Camper.md</code> eintragen — dann steht hier Soll gegen Ist.
      </p>
    </Karte>
  {/if}

  <Rubrik titel="Nach Kategorie" zahl={kategorien.length} />

  {#if kategorien.length === 0}
    <Leerzustand titel="Keine Kosten erfasst" text="Sobald Teile einen Preis haben, steht hier die Aufteilung." kompakt />
  {:else}
    <Karte polster="keins">
      <table class="tabelle">
        <thead>
          <tr>
            <th scope="col">Kategorie</th>
            <th scope="col" class="r">Bezahlt</th>
            <th scope="col" class="r">Geplant</th>
            <th scope="col" class="r">Prognose</th>
            <th scope="col" class="r">Budget</th>
            <th scope="col" class="balkenspalte"><span class="vb">Auslastung</span></th>
          </tr>
        </thead>
        <tbody>
          {#each kategorien as k (k.kategorie)}
            {@const drueber = !!k.budget && k.prognose > k.budget}
            <tr>
              <th scope="row"><a href="#/teile">{k.kategorie}</a></th>
              <td class="r zahl">{dezimal(k.bezahlt, 0)}</td>
              <td class="r zahl">{dezimal(k.geplant, 0)}</td>
              <td class="r zahl" class:drueber>{dezimal(k.prognose, 0)}</td>
              <td class="r zahl schwach">{k.budget ? dezimal(k.budget, 0) : '—'}</td>
              <td class="balkenspalte">
                {#if k.budget}
                  <FortschrittBalken
                    wert={k.bezahlt / k.budget}
                    zusatz={k.geplant / k.budget}
                    ton={drueber ? 'signal' : 'gut'}
                  />
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </Karte>
    <p class="fussnote">
      Kategorie-Budgets sind optional: <code>budget_elektrik: 1800</code> im Kopf von
      <code>vault/Camper.md</code>.
    </p>
  {/if}
{/if}

<style>
  .kennzahlen {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: var(--a-3);
    margin-bottom: var(--a-6);
  }

  .gesamtbalken { margin-bottom: var(--a-7); }
  .legende,
  .fussnote {
    margin: var(--a-2) 0 0;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
  .fussnote { margin-top: var(--a-3); }

  .hinweis {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    margin: 0;
    font-size: var(--text-m);
  }

  code {
    font-family: var(--schrift-mono);
    font-size: 0.9em;
    background: var(--farbe-flaeche-hoch);
    border-radius: var(--r-s);
    padding: 1px 5px;
  }

  .tabelle {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--text-s);
  }
  .tabelle th,
  .tabelle td {
    padding: var(--a-2) var(--a-4);
    text-align: left;
    border-bottom: 1px solid var(--farbe-linie);
  }
  .tabelle tbody tr:last-child th,
  .tabelle tbody tr:last-child td { border-bottom: 0; }
  .tabelle thead th {
    font-size: var(--text-xs);
    font-weight: 650;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--farbe-text-2);
  }
  .tabelle tbody th { font-weight: 550; }
  .tabelle tbody th a { color: inherit; text-decoration: none; }
  .tabelle tbody th a:hover { text-decoration: underline; }
  .tabelle tbody tr:hover { background: var(--farbe-flaeche-hoch); }

  .r { text-align: right; }
  .zahl {
    font-family: var(--schrift-mono);
    font-variant-numeric: tabular-nums;
  }
  .schwach { color: var(--farbe-text-2); }
  .drueber { color: var(--farbe-warn); font-weight: 600; }
  .balkenspalte { width: 180px; }
  .vb { display: inline-block; }
</style>
