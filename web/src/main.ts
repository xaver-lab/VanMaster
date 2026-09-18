import { mount } from 'svelte';
import App from './App.svelte';
import { themaStarten } from './lib/thema.svelte';
import './lib/routing.svelte'; // meldet den hashchange-Listener an (Seiteneffekt)
import './app.css';

// Thema (hell/dunkel) vor dem ersten Rendern setzen, damit es nicht blitzt.
themaStarten();

const target = document.getElementById('app');
if (!target) {
  throw new Error('#app fehlt in index.html');
}

const app = mount(App, { target });

export default app;
