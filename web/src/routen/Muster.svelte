<script lang="ts">
  // Musterseite (#/muster): alle Bausteine, hell und dunkel nebeneinander.
  // Referenz für neue Ansichten — was hier nicht vorkommt, gibt es noch nicht.
  import { toasts } from '../lib/toasts.svelte';
  import {
    Auswahl,
    bestaetigen,
    Chip,
    Dialog,
    Etikett,
    Feld,
    FortschrittBalken,
    FortschrittRing,
    IconKnopf,
    Karte,
    Kbd,
    Kennzahl,
    Knopf,
    Kontrollkaestchen,
    Leerzustand,
    Rubrik,
    STATUS,
    Statusmarke,
    Tabs,
    Filterleiste,
    Textfeld,
  } from '../lib/ui';
  import {
    IconEuro,
    IconGewicht,
    IconLoeschen,
    IconPlus,
    IconStift,
    IconSuche,
    IconTeile,
    IconWerkzeug,
    IconZuschnitt,
  } from '../lib/ui/icons';

  let modus = $state<'beide' | 'hell' | 'dunkel'>('beide');
  let themen = $derived(modus === 'beide' ? (['hell', 'dunkel'] as const) : ([modus] as const));

  let filter = $state({ offen: true, laeuft: false, erledigt: false });
  let erledigt = $state(true);
  let offen = $state(false);
  let tab = $state('beschreibung');
  let dialogOffen = $state(false);
  let laenge = $state('1240');
  let titel = $state('Bettrahmen zuschneiden');
  let notiz = $state('Multiplex Birke, 15 mm.\nKanten brechen, zweimal ölen.');
  let material = $state('Birke Multiplex');
  let antwort = $state('');

  const FARBEN = [
    ['grund', '--farbe-grund'],
    ['fläche', '--farbe-flaeche'],
    ['fläche hoch', '--farbe-flaeche-hoch'],
    ['fläche tief', '--farbe-flaeche-tief'],
    ['linie', '--farbe-linie'],
    ['linie stark', '--farbe-linie-stark'],
    ['text', '--farbe-text'],
    ['text 2', '--farbe-text-2'],
    ['text 3', '--farbe-text-3'],
    ['signal', '--farbe-signal'],
    ['gut', '--farbe-gut'],
    ['info', '--farbe-info'],
    ['warn', '--farbe-warn'],
  ];

  async function loeschenFragen(): Promise<void> {
    const ja = await bestaetigen({
      titel: 'Zuschnitt löschen?',
      text: '„Bettrahmen Seite links“ wird aus bauteile.csv entfernt. Das lässt sich nur über Git zurückholen.',
      ja: 'Löschen',
      gefaehrlich: true,
    });
    antwort = ja ? 'bestätigt' : 'abgebrochen';
  }
</script>

<div class="muster-kopf">
  <p>
    Alle Grundbausteine aus <code>web/src/lib/ui/</code>. Regeln und Props stehen in <code>web/DESIGN.md</code>.
  </p>
  <div class="umschalter">
    <Chip aktiv={modus === 'beide'} onclick={() => (modus = 'beide')}>Nebeneinander</Chip>
    <Chip aktiv={modus === 'hell'} onclick={() => (modus = 'hell')}>Hell</Chip>
    <Chip aktiv={modus === 'dunkel'} onclick={() => (modus = 'dunkel')}>Dunkel</Chip>
  </div>
</div>

<div class="spalten-muster" class:eine={themen.length === 1}>
  {#each themen as thema (thema)}
    <div class="blatt" data-thema={thema}>
      <p class="thema-name">{thema}</p>

      <section>
        <Rubrik titel="Farben" zahl={FARBEN.length} />
        <div class="farben">
          {#each FARBEN as [name, v]}
            <div class="farbe">
              <span class="probe" style:background="var({v})"></span>
              <span class="f-name">{name}</span>
              <code>{v.replace('--farbe-', '')}</code>
            </div>
          {/each}
        </div>
      </section>

      <section>
        <Rubrik titel="Schrift" />
        <div class="schriften">
          <p class="s-held">1240<span>mm</span></p>
          <p class="s-titel">Bettrahmen & Stauraum</p>
          <p class="s-karte">Kartentitel · Archivo 650</p>
          <p>Fließtext in Archivo: Die Querstreben liegen auf Winkeln, damit das Bett ohne Werkzeug abnehmbar bleibt.</p>
          <p class="s-neben">Nebentext 13 px für Hinweise und Metadaten.</p>
          <p class="zahl">Maße & Preise mono · 1 240 × 600 × 15 mm · 354,30 €</p>
          <p class="etikett-text">Etikett in Versalien, schmal</p>
        </div>
      </section>

      <section>
        <Rubrik titel="Knöpfe" />
        <div class="reihe">
          <Knopf variante="primaer" icon={IconPlus}>Aufgabe anlegen</Knopf>
          <Knopf>Sekundär</Knopf>
          <Knopf variante="leise" icon={IconStift}>Leise</Knopf>
          <Knopf variante="gefaehrlich" icon={IconLoeschen} onclick={loeschenFragen}>Löschen …</Knopf>
        </div>
        <div class="reihe">
          <Knopf variante="primaer" groesse="s">Klein</Knopf>
          <Knopf groesse="s" kbd="N">Mit Kürzel</Knopf>
          <Knopf laedt>Speichert</Knopf>
          <Knopf disabled>Gesperrt</Knopf>
          <IconKnopf icon={IconSuche} label="Suchen" />
          <IconKnopf icon={IconStift} label="Bearbeiten" variante="sekundaer" />
          <IconKnopf icon={IconLoeschen} label="Löschen" variante="gefaehrlich" groesse="s" />
        </div>
        {#if antwort}<p class="s-neben">Bestätigungsdialog: {antwort}</p>{/if}
      </section>

      <section>
        <Rubrik titel="Eingaben" />
        <div class="formular">
          <Feld label="Titel" bind:wert={titel} />
          <div class="zwei">
            <Feld label="Länge" bind:wert={laenge} einheit="mm" mono inputmode="numeric" />
            <Auswahl label="Material" bind:wert={material} optionen={['Birke Multiplex', 'Pappel Sperrholz', 'Kiefer Leiste']} />
          </div>
          <Feld label="Suche" icon={IconSuche} placeholder="Teil, Aufgabe, Bereich …" klein />
          <Feld label="Preis" wert="-12" einheit="€" mono fehler="Preis darf nicht negativ sein." />
          <Textfeld label="Notiz" bind:wert={notiz} optional hinweis="Markdown erlaubt." />
          <Feld label="Datei" wert="vault/Bereiche/Möbel.md" disabled />
        </div>
      </section>

      <section>
        <Rubrik titel="Status, Chips, Etiketten" />
        <div class="reihe">
          {#each STATUS as s}<Statusmarke status={s} />{/each}
        </div>
        <div class="reihe">
          {#each STATUS as s}<Statusmarke status={s} kompakt />{/each}
          <Statusmarke status="offen" onclick={() => toasts.info('Status weiterschalten')} titel="klickbar" />
        </div>
        <div class="reihe">
          <Chip bind:aktiv={filter.offen} zahl={27}>offen</Chip>
          <Chip bind:aktiv={filter.laeuft} zahl={5}>läuft</Chip>
          <Chip bind:aktiv={filter.erledigt} zahl={6}>erledigt</Chip>
          <Chip icon={IconTeile} zahl={67}>Teile</Chip>
          <Chip disabled>leer</Chip>
        </div>
        <div class="reihe">
          <Etikett>Möbel</Etikett>
          <Etikett ton="signal">in Arbeit</Etikett>
          <Etikett ton="warn">kritisch</Etikett>
          <Etikett ton="gut">geliefert</Etikett>
          <Etikett ton="info">bestellt</Etikett>
          <Etikett ton="tinte">neu</Etikett>
          <Etikett mono>strombilanz</Etikett>
          <Kbd tasten="Strg K" />
        </div>
      </section>

      <section>
        <Rubrik titel="Kontrollkästchen" />
        <div class="spalte">
          <Kontrollkaestchen bind:checked={erledigt} durchstreichen label="Dämmstoff festlegen" />
          <Kontrollkaestchen bind:checked={offen} label="Radläufe dämmen" />
          <Kontrollkaestchen gemischt label="Gruppe: Boden, Wand, Decke (teilweise)" />
          <Kontrollkaestchen disabled label="Gesperrt (Lesemodus)" />
        </div>
      </section>

      <section>
        <Rubrik titel="Fortschritt" />
        <div class="reihe mittig">
          <FortschrittRing wert={0.16} zusatz={0.13} label="Ausbau" />
          <FortschrittRing wert={0.62} groesse={56} dicke={5} ton="signal" />
          <FortschrittRing wert={1} groesse={32} dicke={3} />
          <div class="balken-spalte">
            <FortschrittBalken wert={3 / 13} zusatz={1 / 13} teilung={13} hoehe={8} zahl="3/13" />
            <FortschrittBalken wert={0.15} ton="signal" hoehe={10} label="bestellt" zahl="443 €" />
            <FortschrittBalken wert={0.8} ton="info" />
          </div>
        </div>
      </section>

      <section>
        <Rubrik titel="Tabs" />
        <Tabs
          bind:aktiv={tab}
          tabs={[
            { id: 'beschreibung', label: 'Beschreibung' },
            { id: 'aufgaben', label: 'Aufgaben', zahl: 13 },
            { id: 'teile', label: 'Teile', zahl: 9, icon: IconTeile },
            { id: 'zuschnitt', label: 'Zuschnitt', icon: IconZuschnitt },
          ]}
        />
        <p class="s-neben tab-inhalt">Aktiver Reiter: <b>{tab}</b> — Pfeiltasten wechseln.</p>
      </section>

      <section>
        <Rubrik titel="Filterleiste" />
        <p class="s-neben">Mit Reitern: Reiter links, Werkzeuge rechts.</p>
        <Filterleiste>
          {#snippet reiter()}
            <Tabs
              bind:aktiv={tab}
              tabs={[
                { id: 'beschreibung', label: 'alle', zahl: 22 },
                { id: 'aufgaben', label: 'offen', zahl: 13 },
              ]}
            />
          {/snippet}
          <Feld wert="" placeholder="Suche…" icon={IconSuche} type="search" klein aria-label="Suche" />
          <Auswahl class="filter-wahl" wert="" optionen={['Elektrik', 'Küche']} leer="alle Bereiche" klein aria-label="Bereich" />
          <Knopf variante="primaer" groesse="s" icon={IconPlus}>Anlegen</Knopf>
        </Filterleiste>

        <p class="s-neben">Ohne Reiter: alles in einer Reihe, der Knopf rutscht ans Ende.</p>
        <Filterleiste>
          <Feld wert="" placeholder="Suche…" icon={IconSuche} type="search" klein aria-label="Suche" />
          <Auswahl class="filter-wahl" wert="" optionen={['Platte', 'Leiste']} leer="alle Arten" klein aria-label="Art" />
          <Knopf variante="primaer" groesse="s" icon={IconPlus}>Anlegen</Knopf>
        </Filterleiste>
      </section>

      <section>
        <Rubrik titel="Karten" />
        <div class="karten">
          <Karte titel="Budget" icon={IconEuro} zusatz="3 046 €">
            {#snippet aktionen()}<IconKnopf icon={IconStift} label="Bearbeiten" groesse="s" />{/snippet}
            <p class="s-neben">Karte mit Kopf, Icon, Zusatz und Aktion.</p>
          </Karte>
          <Karte ton="vertieft" polster="eng">
            <p class="s-neben">Vertieft, eng — für Nebeninfo.</p>
          </Karte>
          <Karte ton="signal" titel="Hinweis" polster="eng">
            <p class="s-neben">Signal — sparsam, eine pro Seite.</p>
          </Karte>
          <Karte href="#/muster" polster="eng">
            <p class="s-neben">Als Link: hebt sich beim Überfahren.</p>
          </Karte>
        </div>
      </section>

      <section>
        <Rubrik titel="Kennzahlen" />
        <div class="kennzahlen">
          <Kennzahl titel="Aufgaben" wert="3/13" />
          <Kennzahl titel="Teilekosten" wert="3 046 €" icon={IconEuro} />
          <Kennzahl titel="Gewicht" wert="128,4 kg" icon={IconGewicht} ton="signal" zusatz="Zuladung 780 kg" />
          <Kennzahl titel="Medien" wert={9} ton="gut" href="#/muster" />
          <Kennzahl titel="Kritisch" wert={2} ton="warn" onclick={() => toasts.info('Kennzahl geklickt')} />
        </div>
      </section>

      <section>
        <Rubrik titel="Dialog, Toasts, Leerzustand" />
        <div class="reihe">
          <Knopf onclick={() => (dialogOffen = true)}>Dialog öffnen</Knopf>
          <Knopf variante="gefaehrlich" onclick={loeschenFragen}>Bestätigung</Knopf>
          <Knopf variante="leise" onclick={() => toasts.info('Datei wurde außerhalb geändert: vault/Bereiche/Elektrik.md')}>Toast Info</Knopf>
          <Knopf variante="leise" onclick={() => toasts.fehler('Anfrage fehlgeschlagen — keine Verbindung zum Server.')}>Fehler</Knopf>
          <Knopf variante="leise" onclick={() => toasts.konflikt('„data/parts.csv“ wurde inzwischen anderswo geändert. Stand übernommen.')}>Konflikt</Knopf>
        </div>
        <Karte polster="keins">
          <Leerzustand kompakt icon={IconWerkzeug} titel="Keine Aufgaben in diesem Filter" text="Filter lockern oder eine neue Aufgabe anlegen.">
            <Knopf variante="primaer" groesse="s" icon={IconPlus}>Aufgabe anlegen</Knopf>
          </Leerzustand>
        </Karte>
      </section>
    </div>
  {/each}
</div>

<Dialog bind:offen={dialogOffen} titel="Zuschnitt anlegen" beschreibung="Wird in bauteile.csv eingetragen.">
  <Feld label="Bezeichnung" wert="Bettrahmen Seite links" />
  <div class="zwei">
    <Feld label="Länge" wert="1900" einheit="mm" mono />
    <Feld label="Breite" wert="120" einheit="mm" mono />
  </div>
  <Auswahl label="Bereich" wert="Möbel" optionen={['Möbel', 'Küche', 'Elektrik']} />
  {#snippet fuss()}
    <Knopf variante="leise" onclick={() => (dialogOffen = false)}>Abbrechen</Knopf>
    <Knopf variante="primaer" onclick={() => { dialogOffen = false; toasts.info('Zuschnitt angelegt (nur Muster).'); }}>Anlegen</Knopf>
  {/snippet}
</Dialog>

<style>
  .muster-kopf { display: flex; align-items: center; gap: var(--a-4); margin-bottom: var(--a-5); color: var(--farbe-text-2); font-size: var(--text-s); }
  .umschalter { margin-left: auto; display: flex; gap: var(--a-2); }

  .spalten-muster { display: grid; grid-template-columns: 1fr 1fr; gap: var(--a-4); }
  .spalten-muster.eine { grid-template-columns: minmax(0, 760px); }
  .blatt {
    min-width: 0;
    background: var(--farbe-grund);
    color: var(--farbe-text);
    border: 1px solid var(--farbe-linie);
    border-radius: var(--r-l);
    padding: var(--a-5);
    display: flex;
    flex-direction: column;
    gap: var(--a-6);
  }
  .thema-name {
    font-family: var(--schrift-mono);
    font-size: var(--text-xs);
    color: var(--farbe-signal);
    margin-bottom: calc(-1 * var(--a-4));
  }
  section { min-width: 0; }

  .farben { display: grid; grid-template-columns: repeat(auto-fill, minmax(92px, 1fr)); gap: var(--a-2); }
  .farbe { display: flex; flex-direction: column; gap: 2px; font-size: var(--text-xs); }
  .probe { height: 40px; border-radius: var(--r-m); box-shadow: inset 0 0 0 1px rgb(128 128 128 / 0.25); margin-bottom: 4px; }
  .f-name { font-weight: 600; }
  .farbe code { color: var(--farbe-text-2); font-size: 0.625rem; }

  .schriften { display: flex; flex-direction: column; gap: var(--a-2); }
  .s-held { font-size: 3.5rem; font-weight: 800; font-stretch: 125%; letter-spacing: -0.05em; line-height: 1; }
  .s-held span { font-size: 1.25rem; color: var(--farbe-signal); margin-left: 6px; letter-spacing: 0; }
  .s-titel { font-size: var(--text-xl); font-weight: 750; font-stretch: 115%; letter-spacing: -0.025em; }
  .s-karte { font-size: var(--text-l); font-weight: 650; }
  .s-neben { font-size: var(--text-s); color: var(--farbe-text-2); }

  .reihe { display: flex; flex-wrap: wrap; align-items: center; gap: var(--a-2); margin-bottom: var(--a-3); }
  .reihe.mittig { gap: var(--a-5); }
  .spalte { display: flex; flex-direction: column; gap: var(--a-3); }
  .formular { display: flex; flex-direction: column; gap: var(--a-4); }
  .zwei { display: grid; grid-template-columns: 1fr 1fr; gap: var(--a-3); }
  .balken-spalte { flex: 1; min-width: 180px; display: flex; flex-direction: column; gap: var(--a-3); }
  .tab-inhalt { padding-top: var(--a-3); }
  .karten { display: grid; grid-template-columns: 1fr 1fr; gap: var(--a-3); }
  .kennzahlen { display: flex; flex-wrap: wrap; gap: var(--a-5); }

  @media (max-width: 1100px) {
    .spalten-muster { grid-template-columns: 1fr; }
  }
</style>
