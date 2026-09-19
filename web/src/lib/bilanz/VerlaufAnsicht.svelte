<script lang="ts">
  // Verlauf — die Zeitreihe aus `data/verlauf.csv`, dieselbe wie
  // `python camper.py verlauf` (tools/verlauf.py: daten()). Gerechnet wird
  // dort, hier steht die Anzeige.
  //
  // Drei Geldreihen in einem Diagramm, weil sie dieselbe Einheit und
  // denselben Maßstab haben. Aufgaben und Gewicht bekommen keine zweite
  // Achse danebengelegt — sie stehen in der Tabelle darunter.
  //
  // Unterschieden werden die Reihen über die Strichart (durchgezogen,
  // gestrichelt, gepunktet), nicht über Farbe: das Designsystem kennt genau
  // eine Signalfarbe, und Strichart trägt auch im Ausdruck und bei
  // Farbsehschwäche.
  import { store } from '../daten.svelte';
  import { dezimal } from '../zahlformat';
  import { Karte, Kennzahl, Leerzustand, Rubrik } from '../ui';
  import { IconEuro, IconInfo } from '../ui/icons';
  import IconVerlauf from '@lucide/svelte/icons/trending-up';

  const B = { x: 1000, y: 260, links: 62, rechts: 92, oben: 16, unten: 34 };
  const REIHEN = [
    { id: 'bezahlt', label: 'Bezahlt', klasse: 'reihe-bezahlt' },
    { id: 'geplant', label: 'Geplant', klasse: 'reihe-geplant' },
    { id: 'prognose', label: 'Prognose', klasse: 'reihe-prognose' },
  ] as const;

  let v = $derived(store.daten?.verlauf);
  let punkte = $derived(v?.punkte ?? []);
  let letzter = $derived(punkte.length ? punkte[punkte.length - 1] : null);

  let tage = $derived(punkte.map((p) => Date.parse(p.datum)));
  let breiteP = $derived(B.x - B.links - B.rechts);
  let hoeheP = $derived(B.y - B.oben - B.unten);

  // Obergrenze auf einen runden Wert aufziehen, damit die Rasterlinien
  // lesbare Beträge tragen statt 3045,53.
  let maxWert = $derived.by(() => {
    const roh = Math.max(1, ...punkte.map((p) => p.prognose));
    const stufe = Math.pow(10, Math.floor(Math.log10(roh))) / 2;
    return Math.ceil(roh / stufe) * stufe;
  });

  function x(i: number): number {
    if (punkte.length < 2) return B.links + breiteP / 2;
    const von = tage[0];
    const spanne = tage[tage.length - 1] - von || 1;
    return B.links + ((tage[i] - von) / spanne) * breiteP;
  }

  function y(wert: number): number {
    return B.oben + hoeheP - (wert / maxWert) * hoeheP;
  }

  function pfad(feld: 'bezahlt' | 'geplant' | 'prognose'): string {
    return punkte.map((p, i) => `${i ? 'L' : 'M'}${x(i).toFixed(1)} ${y(p[feld]).toFixed(1)}`).join(' ');
  }

  let raster = $derived([0, 0.25, 0.5, 0.75, 1].map((a) => ({ wert: maxWert * a, y: y(maxWert * a) })));

  function kurz(datum: string): string {
    const [, m, d] = datum.split('-');
    return d && m ? `${d}.${m}.` : datum;
  }

  // Datumsmarken: erster und letzter immer, dazwischen nur, wenn genug Platz
  // ist — sonst kleben die Beschriftungen aneinander.
  let marken = $derived.by(() => {
    if (punkte.length < 2) return punkte.map((p, i) => ({ i, datum: p.datum }));
    const aus: { i: number; datum: string }[] = [];
    let letzteX = -Infinity;
    punkte.forEach((p, i) => {
      const ist = i === 0 || i === punkte.length - 1;
      if (ist || x(i) - letzteX > 90) {
        aus.push({ i, datum: p.datum });
        letzteX = x(i);
      }
    });
    return aus;
  });

  // Endmarken: liegen zwei Reihen dicht beieinander, überdecken sich ihre
  // Beschriftungen. Deshalb von unten nach oben auf Mindestabstand schieben.
  let endmarken = $derived.by(() => {
    if (!letzter) return [];
    const ABSTAND = 15;
    const sortiert = REIHEN.map((r) => ({ label: r.label, y: y(letzter![r.id]) }))
      .sort((a, b) => b.y - a.y);
    for (let i = 1; i < sortiert.length; i++) {
      if (sortiert[i - 1].y - sortiert[i].y < ABSTAND) sortiert[i].y = sortiert[i - 1].y - ABSTAND;
    }
    return sortiert;
  });

  let aktiv = $state<number | null>(null);

  function zeigen(ev: PointerEvent) {
    if (punkte.length === 0) return;
    const el = ev.currentTarget as SVGSVGElement;
    const rect = el.getBoundingClientRect();
    const ix = ((ev.clientX - rect.left) / rect.width) * B.x;
    let beste = 0;
    for (let i = 1; i < punkte.length; i++) {
      if (Math.abs(x(i) - ix) < Math.abs(x(beste) - ix)) beste = i;
    }
    aktiv = beste;
  }

  let markiert = $derived(aktiv != null ? punkte[aktiv] : null);

  // Am linken und rechten Rand würde ein mittig gesetzter Tooltip aus der
  // Karte laufen; dort hängt er stattdessen an der Kante des Punktes.
  let tooltipAnteil = $derived(aktiv != null ? (x(aktiv) / B.x) * 100 : 50);
  let tooltipSchub = $derived(
    tooltipAnteil > 72 ? 'translateX(-100%)' : tooltipAnteil < 22 ? 'translateX(0)' : 'translateX(-50%)',
  );
</script>

{#if !v || punkte.length === 0}
  <Leerzustand
    icon={IconVerlauf}
    titel="Noch kein Verlauf erfasst"
    text="„python camper.py verlauf“ schreibt für heute einen Datensatz nach data/verlauf.csv — Kosten, Aufgabenstand und Gewicht. Ab dem zweiten Datensatz steht hier die Kurve."
  />
{:else}
  <div class="kennzahlen">
    <Kennzahl
      titel="Bezahlt"
      wert="{dezimal(letzter!.bezahlt, 0)} €"
      icon={IconEuro}
      zusatz="Stand {kurz(letzter!.datum)}"
    />
    <Kennzahl
      titel="Prognose"
      wert="{dezimal(letzter!.prognose, 0)} €"
      zusatz="bezahlt und geplant zusammen"
    />
    <Kennzahl
      titel="Seit {kurz(v.von ?? letzter!.datum)}"
      wert="{v.delta_bezahlt >= 0 ? '+' : '−'}{dezimal(Math.abs(v.delta_bezahlt), 0)} €"
      zusatz="{v.anzahl} {v.anzahl === 1 ? 'Datensatz' : 'Datensätze'}"
      ton={v.delta_bezahlt > 0 ? 'signal' : 'neutral'}
    />
    <Kennzahl
      titel="Aufgaben"
      wert="{letzter!.aufgaben_fertig} / {letzter!.aufgaben_gesamt}"
      zusatz="{v.delta_aufgaben_fertig >= 0 ? '+' : '−'}{Math.abs(v.delta_aufgaben_fertig)} seit Beginn"
    />
  </div>

  <Rubrik titel="Kosten über die Zeit" />

  <Karte>
    <div class="diagramm">
      <svg
        viewBox="0 0 {B.x} {B.y}"
        role="img"
        aria-label="Kostenverlauf: bezahlt, geplant und Prognose je erfasstem Tag. Die Werte stehen in der Tabelle darunter."
        onpointermove={zeigen}
        onpointerleave={() => (aktiv = null)}
      >
        {#each raster as r (r.wert)}
          <line class="raster" x1={B.links} x2={B.x - B.rechts} y1={r.y} y2={r.y} />
          <text class="achse" x={B.links - 10} y={r.y + 4} text-anchor="end">{dezimal(r.wert, 0)}</text>
        {/each}

        {#each marken as m (m.i)}
          <text class="achse" x={x(m.i)} y={B.y - 12} text-anchor="middle">{kurz(m.datum)}</text>
        {/each}

        {#if markiert && aktiv != null}
          <line class="fadenkreuz" x1={x(aktiv)} x2={x(aktiv)} y1={B.oben} y2={B.oben + hoeheP} />
        {/if}

        {#each REIHEN as r (r.id)}
          <path class="linie {r.klasse}" d={pfad(r.id)} vector-effect="non-scaling-stroke" />
        {/each}

        {#if punkte.length < 2}
          {#each REIHEN as r (r.id)}
            <circle class="punkt {r.klasse}" cx={x(0)} cy={y(punkte[0][r.id])} r="5" />
          {/each}
        {:else if aktiv != null}
          {#each REIHEN as r (r.id)}
            <circle class="punkt {r.klasse}" cx={x(aktiv)} cy={y(punkte[aktiv][r.id])} r="5" />
          {/each}
        {/if}

        {#each endmarken as e (e.label)}
          <text class="endmarke" x={B.x - B.rechts + 8} y={e.y + 4}>{e.label}</text>
        {/each}
      </svg>

      {#if markiert}
        <div class="tooltip" style="left: {tooltipAnteil}%; transform: {tooltipSchub};">
          <strong>{markiert.datum}</strong>
          {#each REIHEN as r (r.id)}
            <span><i class={r.klasse} aria-hidden="true"></i>{r.label}<b class="zahl">{dezimal(markiert[r.id], 0)} €</b></span>
          {/each}
          <span class="nebensache">{markiert.aufgaben_fertig}/{markiert.aufgaben_gesamt} Aufgaben{markiert.gewicht_kg ? ` · ${dezimal(markiert.gewicht_kg, 1)} kg` : ''}</span>
        </div>
      {/if}
    </div>

    <ul class="legende">
      {#each REIHEN as r (r.id)}
        <li><i class={r.klasse} aria-hidden="true"></i>{r.label}</li>
      {/each}
    </ul>
  </Karte>

  {#if punkte.length < 2}
    <p class="fussnote">
      <IconInfo size={15} strokeWidth={2} aria-hidden="true" />
      Ein einzelner Datensatz ergibt noch keine Kurve. Ab dem zweiten Aufruf von
      <code>camper verlauf</code> an einem anderen Tag wird daraus eine Linie.
    </p>
  {/if}

  <Rubrik titel="Datensätze" zahl={v.anzahl} />

  <Karte polster="keins">
    <table class="tabelle">
      <thead>
        <tr>
          <th scope="col">Datum</th>
          <th scope="col" class="r">Bezahlt</th>
          <th scope="col" class="r">Geplant</th>
          <th scope="col" class="r">Prognose</th>
          <th scope="col" class="r">Aufgaben</th>
          <th scope="col" class="r">Gewicht</th>
        </tr>
      </thead>
      <tbody>
        {#each punkte as p (p.datum)}
          <tr>
            <th scope="row" class="zahl">{p.datum}</th>
            <td class="r zahl">{dezimal(p.bezahlt, 0)}</td>
            <td class="r zahl">{dezimal(p.geplant, 0)}</td>
            <td class="r zahl">{dezimal(p.prognose, 0)}</td>
            <td class="r zahl">{p.aufgaben_fertig} / {p.aufgaben_gesamt}</td>
            <td class="r zahl schwach">{p.gewicht_kg ? `${dezimal(p.gewicht_kg, 1)} kg` : '—'}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </Karte>

  <p class="fussnote">
    Ein Datensatz je Tag, geschrieben von <code>camper verlauf</code>. Mehrfacher Aufruf
    am selben Tag schreibt den heutigen Stand fort, statt eine Dublette anzulegen.
  </p>
{/if}

<style>
  .kennzahlen {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: var(--a-3);
    margin-bottom: var(--a-6);
  }

  .diagramm { position: relative; }
  .diagramm svg { display: block; width: 100%; height: auto; touch-action: none; }

  .raster {
    stroke: var(--farbe-linie);
    stroke-width: 1;
  }
  .fadenkreuz {
    stroke: var(--farbe-linie-stark);
    stroke-width: 1;
    stroke-dasharray: 3 3;
  }
  .achse {
    fill: var(--farbe-text-2);
    font-family: var(--schrift-mono);
    font-size: 12px;
  }
  .endmarke {
    fill: var(--farbe-text-2);
    font-size: 12px;
    font-stretch: var(--schmal);
    letter-spacing: 0.04em;
  }

  .linie { fill: none; stroke-width: 2; stroke-linecap: round; stroke-linejoin: round; }
  .linie.reihe-bezahlt { stroke: var(--farbe-signal); }
  .linie.reihe-geplant { stroke: var(--farbe-text); stroke-dasharray: 7 5; }
  .linie.reihe-prognose { stroke: var(--farbe-text-2); stroke-dasharray: 2 4; }

  .punkt { stroke: var(--farbe-flaeche); stroke-width: 2; }
  .punkt.reihe-bezahlt { fill: var(--farbe-signal); }
  .punkt.reihe-geplant { fill: var(--farbe-text); }
  .punkt.reihe-prognose { fill: var(--farbe-text-2); }

  .legende {
    display: flex;
    flex-wrap: wrap;
    gap: var(--a-2) var(--a-5);
    margin: var(--a-3) 0 0;
    padding: 0;
    list-style: none;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }
  .legende li { display: flex; align-items: center; gap: var(--a-2); }

  /* Strichprobe: dieselbe Strichart wie die Linie, damit die Legende die
     Reihe ohne Farbe benennt. */
  i {
    display: inline-block;
    width: 22px;
    height: 0;
    border-top-width: 2px;
    flex: none;
  }
  i.reihe-bezahlt { border-top: 2px solid var(--farbe-signal); }
  i.reihe-geplant { border-top: 2px dashed var(--farbe-text); }
  i.reihe-prognose { border-top: 2px dotted var(--farbe-text-2); }

  .tooltip {
    position: absolute;
    top: var(--a-1);
    display: flex;
    flex-direction: column;
    gap: 2px;
    padding: var(--a-2) var(--a-3);
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie-stark);
    border-radius: var(--r-m);
    box-shadow: var(--schatten-3);
    font-size: var(--text-s);
    white-space: nowrap;
    pointer-events: none;
  }
  .tooltip strong { font-family: var(--schrift-mono); font-size: var(--text-xs); color: var(--farbe-text-2); }
  .tooltip span { display: flex; align-items: center; gap: var(--a-2); }
  .tooltip b { margin-left: auto; font-weight: 600; }
  .tooltip .nebensache { color: var(--farbe-text-2); font-size: var(--text-xs); margin-top: 2px; }

  .fussnote {
    display: flex;
    align-items: center;
    gap: var(--a-2);
    margin: var(--a-3) 0 0;
    font-size: var(--text-s);
    color: var(--farbe-text-2);
  }

  code {
    font-family: var(--schrift-mono);
    font-size: 0.9em;
    background: var(--farbe-flaeche-hoch);
    border-radius: var(--r-s);
    padding: 1px 5px;
  }

  .tabelle { width: 100%; border-collapse: collapse; font-size: var(--text-s); }
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
  .tabelle tbody tr:hover { background: var(--farbe-flaeche-hoch); }

  .r { text-align: right; }
  .zahl { font-family: var(--schrift-mono); font-variant-numeric: tabular-nums; }
  .schwach { color: var(--farbe-text-2); }
</style>
