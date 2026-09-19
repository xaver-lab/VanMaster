<script lang="ts">
  import { flip } from 'svelte/animate';
  import { fly } from 'svelte/transition';
  import { toasts, type ToastArt } from './toasts.svelte';
  import { IconFehler, IconInfo, IconSchliessen, IconWarnung, type IconKomponente } from './ui/icons';

  // Spiegelt die Standzeiten aus toasts.svelte.ts für die Ablaufleiste.
  const DAUER: Record<ToastArt, number> = { info: 3500, fehler: 6000, konflikt: 7000 };
  // Spiegelt DAUER_MIT_AKTION aus toasts.svelte.ts.
  const DAUER_MIT_AKTION = 9000;
  const ICON: Record<ToastArt, IconKomponente> = { info: IconInfo, fehler: IconFehler, konflikt: IconWarnung };
  const TITEL: Record<ToastArt, string> = { info: 'Hinweis', fehler: 'Fehler', konflikt: 'Konflikt' };
</script>

<div class="toasts" role="status" aria-live="polite">
  {#each toasts.liste as t (t.id)}
    {@const Icon = ICON[t.art]}
    <div
      class="toast {t.art}"
      style:--dauer="{t.aktion ? DAUER_MIT_AKTION : DAUER[t.art]}ms"
      animate:flip={{ duration: 200 }}
      in:fly={{ y: 12, duration: 220 }}
      out:fly={{ x: 24, duration: 160 }}
    >
      <span class="icon"><Icon size={17} strokeWidth={2} aria-hidden="true" /></span>
      <div class="inhalt">
        <strong>{TITEL[t.art]}</strong>
        <span>{t.text}</span>
      </div>
      {#if t.aktion}
        <button
          type="button"
          class="aktion"
          onclick={() => {
            const tun = t.aktion!.tun;
            toasts.entfernen(t.id);
            void tun();
          }}
        >
          {t.aktion.label}
        </button>
      {/if}
      <button type="button" aria-label="Schließen" onclick={() => toasts.entfernen(t.id)}>
        <IconSchliessen size={15} strokeWidth={2} />
      </button>
      <span class="ablauf" aria-hidden="true"></span>
    </div>
  {/each}
</div>

<style>
  .toasts {
    position: fixed;
    right: var(--a-5);
    bottom: var(--a-5);
    z-index: 60;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: var(--a-2);
    pointer-events: none;
  }
  .toast {
    --c: var(--farbe-info);
    position: relative;
    pointer-events: auto;
    display: flex;
    align-items: flex-start;
    gap: var(--a-3);
    width: min(420px, calc(100vw - 32px));
    padding: var(--a-3) var(--a-2) var(--a-3) var(--a-4);
    background: var(--farbe-flaeche);
    border: 1px solid var(--farbe-linie-stark);
    border-left: 3px solid var(--c);
    border-radius: var(--r-m);
    box-shadow: var(--schatten-3);
    overflow: hidden;
    font-size: var(--text-s);
  }
  .fehler { --c: var(--farbe-warn); }
  .konflikt { --c: var(--farbe-signal); }
  .icon { color: var(--c); display: inline-flex; padding-top: 1px; }
  .inhalt { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 1px; overflow-wrap: anywhere; }
  strong {
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    font-stretch: var(--schmal);
    color: var(--c);
  }
  button {
    flex: none;
    display: grid;
    place-items: center;
    width: 26px;
    height: 26px;
    border: 0;
    border-radius: var(--r-s);
    background: none;
    color: var(--farbe-text-2);
  }
  button:hover { background: var(--farbe-flaeche-hoch); color: var(--farbe-text); }
  /* Der Aktionsknopf trägt Text statt eines Icons und ist die Hauptsache
     im Toast — der Schließen-Knopf bleibt daneben leise. */
  button.aktion {
    width: auto;
    height: 26px;
    padding: 0 10px;
    font: inherit;
    font-size: var(--text-s);
    font-weight: 600;
    color: var(--farbe-text);
    box-shadow: inset 0 0 0 1px var(--farbe-linie-stark);
  }
  button.aktion:hover { background: var(--farbe-tinte-fuellung); color: var(--farbe-auf-tinte); }
  .ablauf {
    position: absolute;
    left: 0;
    bottom: 0;
    height: 2px;
    width: 100%;
    background: var(--c);
    opacity: 0.5;
    transform-origin: left;
    animation: ablauf var(--dauer) linear forwards;
  }
  @keyframes ablauf { to { transform: scaleX(0); } }
</style>
