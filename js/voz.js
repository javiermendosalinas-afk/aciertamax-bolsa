/* inmobiliaria.pro · Voz de Sofía y Diego: hablan (speechSynthesis) y escuchan (SpeechRecognition) con lo que trae el navegador.
   API: Voz.activa(), Voz.decir(quien, html), Voz.escuchar() -> Promise<texto>, Voz.numero(texto), Voz.alCambiar(fn).
   El micrófono lo procesa el navegador; no se guardan audios. */
(function () {
  'use strict';
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const puedeHablar = 'speechSynthesis' in window, puedeOir = !!SR;
  let activa = false, voces = [], oyentes = [];
  try { activa = localStorage.getItem('ipro_voz') === '1'; } catch (e) {}
  function cargarVoces() { voces = puedeHablar ? speechSynthesis.getVoices().filter(v => /^es/i.test(v.lang)) : []; }
  if (puedeHablar) { cargarVoces(); speechSynthesis.onvoiceschanged = cargarVoces; }
  const FEM = /paulina|m[oó]nica|sabina|helena|laura|elvira|dalia|marisol|luciana|ang[eé]lica|esperanza|google espa[nñ]ol(?! de espa)|female|mujer/i;
  const MAS = /juan|jorge|ra[uú]l|diego|pablo|carlos|enrique|alvaro|jos[eé]|male|hombre|reed|eddy|grandpa/i;
  function vozDe(quien) {
    const mx = voces.filter(v => /es[-_]MX/i.test(v.lang)), us = voces.filter(v => /es[-_]US/i.test(v.lang)), base = mx.length ? mx : us.length ? us : voces;
    const re = quien === 'Sofía' ? FEM : MAS, otra = quien === 'Sofía' ? MAS : FEM;
    return base.find(v => re.test(v.name)) || voces.find(v => re.test(v.name) && /es/i.test(v.lang)) || base.find(v => !otra.test(v.name)) || base[0] || null;
  }
  const limpiar = (html) => { const d = document.createElement('div'); d.innerHTML = html; return (d.textContent || '').replace(/[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/gu, '').replace(/\s+/g, ' ').replace(/\$([\d,]+)/g, (m, n) => n.replace(/,/g, '') + ' pesos').trim(); };
  function decir(quien, html) {
    if (!activa || !puedeHablar) return;
    const u = new SpeechSynthesisUtterance(limpiar(html)), v = vozDe(quien);
    if (v) { u.voice = v; u.lang = v.lang; } else u.lang = 'es-MX';
    const misma = v && vozDe(quien === 'Sofía' ? 'Diego' : 'Sofía') === v;                  // si solo hay una voz, se distinguen por el tono
    u.pitch = quien === 'Sofía' ? (misma ? 1.25 : 1.05) : (misma ? .8 : .95); u.rate = quien === 'Sofía' ? 1.05 : 1.0;
    u.onstart = () => window.Juego && Juego.bajar && Juego.bajar(true);
    u.onend = u.onerror = () => { if (!speechSynthesis.pending && window.Juego && Juego.bajar) Juego.bajar(false); };
    speechSynthesis.speak(u);
  }
  function escuchar() {
    return new Promise((ok, mal) => {
      if (!puedeOir) return mal(new Error('sin-reconocimiento'));
      if (puedeHablar) speechSynthesis.cancel();
      const r = new SR(); r.lang = 'es-MX'; r.interimResults = false; r.maxAlternatives = 3; let dado = false;
      r.onresult = (e) => { dado = true; ok(Array.from(e.results[0]).map(a => a.transcript).join(' | ')); };
      r.onerror = (e) => { if (!dado) mal(new Error(e.error || 'error')); };
      r.onend = () => { if (!dado) mal(new Error('sin-voz')); };
      try { r.start(); } catch (e) { mal(e); }
    });
  }
  // "cuatro millones y medio", "45 mil", "1.5 millones", "cuarenta y cinco mil quinientos" -> número
  const U = { cero: 0, un: 1, uno: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7, ocho: 8, nueve: 9, diez: 10, once: 11, doce: 12, trece: 13, catorce: 14, quince: 15,
    dieciseis: 16, diecisiete: 17, dieciocho: 18, diecinueve: 19, veinte: 20, veintiun: 21, veintiuno: 21, veintidos: 22, veintitres: 23, veinticuatro: 24, veinticinco: 25, veintiseis: 26, veintisiete: 27, veintiocho: 28, veintinueve: 29,
    treinta: 30, cuarenta: 40, cincuenta: 50, sesenta: 60, setenta: 70, ochenta: 80, noventa: 90, cien: 100, ciento: 100, doscientos: 200, doscientas: 200, trescientos: 300, cuatrocientos: 400,
    quinientos: 500, seiscientos: 600, setecientos: 700, ochocientos: 800, novecientos: 900 };
  const norm = (s) => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase();
  function numero(texto) {
    let s = norm(texto).split('|')[0].replace(/(\d)[.,](\d{3})\b/g, '$1$2').replace(/(\d),(\d)/g, '$1.$2');
    let total = 0, actual = 0, hay = false;
    for (const w of s.match(/\d+(?:\.\d+)?|[a-z]+/g) || []) {
      if (/^\d/.test(w)) { actual += parseFloat(w); hay = true; }
      else if (w in U) { actual += U[w]; hay = true; }
      else if (w === 'mil') { total += (actual || 1) * 1000; actual = 0; hay = true; }
      else if (w === 'millon' || w === 'millones') { total = (total + (actual || 1)) * 1e6; actual = 0; hay = true; }
      else if (w === 'medio' && hay) { actual += (total >= 1e6 && actual === 0) ? 500000 : (total >= 1000 && actual === 0 ? 500 : .5); }
      else if (w === 'k') { total += actual * 1000; actual = 0; }
    }
    return hay ? Math.round(total + actual) : 0;
  }
  function alCambiar(fn) { oyentes.push(fn); }
  function poner(v) { activa = v; try { localStorage.setItem('ipro_voz', v ? '1' : '0'); } catch (e) {} if (!v && puedeHablar) speechSynthesis.cancel(); oyentes.forEach(f => f(v)); }
  window.Voz = { activa: () => activa, poner, decir, escuchar, numero, norm, puedeHablar, puedeOir, alCambiar };
})();
