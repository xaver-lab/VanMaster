<script lang="ts">
  // Strom — Tagesbedarf der Verbraucher gegen die nutzbare Batteriekapazität.
  // Gleiche Zahlen wie `python camper.py strom` (tools/strom.py); gerechnet
  // wird dort, hier steht die Anzeige.
  //
  // Verbraucher sind die Teile aus der Stückliste, die `watt` und
  // `stunden_pro_tag` gesetzt haben — keine zweite Liste derselben Dinge.
  import { store } from '../daten.svelte';
  import { dezimal } from '../zahlformat';
  import { FortschrittBalken, Karte, Kennzahl, Leerzustand, Rubrik } from '../ui';
  import { IconWarnung } from '../ui/icons';
  import IconStrom from '@lucide/svelte/icons/zap';
  import IconBatterie from '@lucide/svelte/icons/battery-charging';

  // Ab hier warnt auch die Textausgabe (tools/strom.py: SCHWELLE_TAGE).
  const SCHWELLE_TAGE = 1;

  let s = $derived(store.daten?.strom);

  let verbraucher = $derived(s?.verbraucher ?? []);
  let luecken = $derived(s?.unvollstaendig ?? []);
  let knapp = $derived(s?.reichweite_tage != null && s.reichweite_tage < SCHWELLE_TAGE);
  let anteil = $derived(
    s?.nutzbar_ah ? Math.min(s.ah_pro_tag_brutto / s.nutzbar_ah, 1) : 0,
  );
</script>

{#if !s}
  <Leerzustand titel="Keine Stromdaten" />
{:else if !verbraucher.length}
  <Leerzustand
    icon={IconStrom}
    titel="Keine Verbraucher erfasst"
    text="Die Strombilanz rechnet mit den Teilen, die „watt“ und „stunden_pro_tag“ gesetzt haben — beides, eines allein reicht nicht. Gepflegt wird das wie das Gewicht über „camper parts excel“ und „camper parts import“."
  />
  {#if luecken.length}
    <Karte ton="signal">
      <p class="hinweis">
        <IconWarnung size={16} strokeWidth={2} aria-hidden="true" />
        <span>{luecken.length} Teile haben nur einen der beiden Werte:</span>
      </p>
      <ul class="luecken">
        {#each luecken as l (l.id)}
          <li>
            <span>{l.titel}</span>
            <span class="schwach zahl">watt {l.watt || '—'} · h/Tag {l.stunden_pro_tag || '—'}</span>
          </li>
        {/each}
      </ul>
    </Karte>
  {/if}
{:else}
  <div class="kennzahlen">
    <Kennzahl
      titel="Tagesbedarf"
      wert="{dezimal(s.ah_pro_tag, 1)} Ah"
      icon={IconStrom}
      zusatz="{dezimal(s.wh_pro_tag, 0)} Wh bei {dezimal(s.bordspannung_v, 0)} V"
      ton={knapp ? 'warn' : 'neutral'}
    />
    <Kennzahl titel="Verbraucher" wert={verbraucher.length} zusatz="von {s.teile_gesamt} Teilen" href="#/teile" />
    {#if s.batterie_ah != null}
      <Kennzahl
        titel="Batterie"
        wert="{dezimal(s.batterie_ah, 0)} Ah"
        icon={IconBatterie}
        zusatz="nutzbar {dezimal(s.nutzbar_ah ?? 0, 0)} Ah ({dezimal(s.batterie_nutzbar * 100, 0)} %)"
      />
    {/if}
    {#if s.reichweite_tage != null}
      <Kennzahl
        titel="Reichweite"
        wert="{dezimal(s.reichweite_tage, 1)} Tage"
        zusatz="ohne Nachladen"
        ton={knapp ? 'warn' : 'gut'}
      />
    {/if}
  </div>

  {#if luecken.length}
    <Karte ton="signal">
      <p class="hinweis">
        <IconWarnung size={16} strokeWidth={2} aria-hidden="true" />
        <span>
          {luecken.length}
          {luecken.length === 1 ? 'Teil hat' : 'Teile haben'} nur einen der beiden Werte und
          {luecken.length === 1 ? 'fehlt' : 'fehlen'} in der Bilanz —
          {#each luecken as l, i (l.id)}{i ? ', ' : ''}{l.titel}{/each}.
        </span>
      </p>
    </Karte>
  {/if}

  <Rubrik titel="Bedarf gegen Batterie" />

  {#if s.batterie_ah == null}
    <Karte>
      <p class="fehlend">
        Keine Reichweite: <code>batterie_ah</code> fehlt im Kopf von
        <code>vault/Camper.md</code>. Dazu optional <code>bordspannung_v</code>
        (Vorgabe 12) und <code>batterie_nutzbar</code> (Vorgabe 0.8).
      </p>
    </Karte>
  {:else}
    <div class="waage">
      <FortschrittBalken
        wert={anteil}
        ton={knapp ? 'signal' : 'gut'}
        hoehe={12}
        teilung={10}
        label="Tagesbedarf aus der nutzbaren Kapazität"
        zahl="{dezimal(s.ah_pro_tag_brutto, 1)} / {dezimal(s.nutzbar_ah ?? 0, 0)} Ah"
      />
      <p class="legende">
        {dezimal(s.reichweite_tage ?? 0, 1)} Tage ohne Nachladen. Solar und Landstrom sind
        darin nicht enthalten — der Wert ist der schlechteste Fall.
        {#if s.wirkungsgrad !== 1}
          Gerechnet mit {dezimal(s.wirkungsgrad * 100, 0)} % Wirkungsgrad.
        {/if}
      </p>
      {#if knapp}
        <p class="warnung">
          <IconWarnung size={15} strokeWidth={2} aria-hidden="true" />
          Unter einem Tag Reserve — ohne Solar oder Landstrom ist das zu knapp.
        </p>
      {/if}
    </div>
  {/if}

  <Rubrik titel="Verbraucher" zahl={verbraucher.length} />
  <Karte polster="keins">
    <table class="tabelle">
      <thead>
        <tr>
          <th scope="col">Verbraucher</th>
          <th scope="col">Kategorie</th>
          <th scope="col" class="r">Leistung</th>
          <th scope="col" class="r">h/Tag</th>
          <th scope="col" class="r">Wh/Tag</th>
          <th scope="col" class="r">Ah/Tag</th>
          <th scope="col" class="balkenspalte"><span class="vb">Anteil</span></th>
        </tr>
      </thead>
      <tbody>
        {#each verbraucher as v (v.id)}
          <tr>
            <th scope="row"><a href="#/teile/{encodeURIComponent(v.id)}">{v.titel}</a></th>
            <td class="schwach">{v.kategorie}</td>
            <td class="r zahl">{v.menge !== 1 ? `${dezimal(v.menge, 0)}× ` : ''}{dezimal(v.watt, 0)} W</td>
            <td class="r zahl">{dezimal(v.stunden_pro_tag, 1)}</td>
            <td class="r zahl">{dezimal(v.wh_pro_tag, 0)}</td>
            <td class="r zahl">{dezimal(v.ah_pro_tag, 1)}</td>
            <td class="balkenspalte">
              <FortschrittBalken wert={s.wh_pro_tag ? v.wh_pro_tag / s.wh_pro_tag : 0} ton="info" />
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Karte>
  <p class="fussnote">
    Wh/Tag = Menge × Watt × Stunden. Ah/Tag = Wh ÷ Bordspannung. Gepflegt werden
    <code>watt</code> und <code>stunden_pro_tag</code> an den Teilen, wie das Gewicht
    über <code>camper parts excel</code>.
  </p>
{/if}

<style>
  .kennzahlen {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: var(--a-3);
    margin-bottom: var(--a-5);
  }

  .waage { margin-bottom: var(--a-6); }

  .hinweis,
  .warnung {
    display: flex;
    align-items: flex-start;
    gap: var(--a-2);
    margin: 0;
    font-size: var(--text-m);
  }
  .warnung { margin-top: var(--a-3); color: var(--farbe-warn); font-size: var(--text-s); }

  .legende,
  .fehlend,
  .fussnote {
    margin: var(--a-2) 0 0;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
  .fehlend { margin: 0; font-size: var(--text-m); }
  .fussnote { margin-top: var(--a-3); }

  .luecken { list-style: none; margin: var(--a-2) 0 0; padding: 0; display: grid; gap: 4px; }
  .luecken li { display: flex; justify-content: space-between; gap: var(--a-3); font-size: var(--text-s); }

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
  .balkenspalte { width: 140px; }
  .vb { display: inline-block; }
</style>
