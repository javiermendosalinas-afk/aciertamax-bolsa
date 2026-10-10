/* inmobiliaria.pro · Juego: música original tipo videojuego, efectos de sonido, logros y confeti.
   Todo se sintetiza con Web Audio (sin archivos ni derechos de terceros). Preferencias en localStorage.
   API: Juego.sfx('tap'|'select'|'tick'|'pop'|'coin'|'whoosh'|'win'|'lose'|'fanfarria'), Juego.logro(texto, emoji),
        Juego.confeti(), Juego.ganar(texto, emoji) (fanfarria + confeti + logro). */
(function () {
  'use strict';
  const pref = (() => { try { return JSON.parse(localStorage.getItem('ipro_sonido') || '{}'); } catch (e) { return {}; } })();
  const est = { musica: pref.musica !== false, efectos: pref.efectos !== false };
  const guardar = () => { try { localStorage.setItem('ipro_sonido', JSON.stringify(est)); } catch (e) {} };
  const menosMov = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let ctx = null, master = null, sfxBus = null, musBus = null, musTimer = null, paso = 0, siguiente = 0;

  function iniciar() {
    if (ctx) { if (ctx.state === 'suspended') ctx.resume(); return; }
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
    ctx = new AC(); master = ctx.createGain(); master.gain.value = 0.9; master.connect(ctx.destination);
    sfxBus = ctx.createGain(); sfxBus.gain.value = 0.55; sfxBus.connect(master);
    musBus = ctx.createGain(); musBus.gain.value = 0.0; musBus.connect(master);
    if (est.musica) arrancarMusica();
  }
  function nota(f, t0, dur, tipo, vol, bus, glide) {
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = tipo; o.frequency.setValueAtTime(f, t0); if (glide) o.frequency.exponentialRampToValueAtTime(glide, t0 + dur);
    g.gain.setValueAtTime(0.0001, t0); g.gain.exponentialRampToValueAtTime(vol, t0 + 0.012); g.gain.exponentialRampToValueAtTime(0.0001, t0 + dur);
    o.connect(g); g.connect(bus); o.start(t0); o.stop(t0 + dur + 0.02);
  }
  const N = (n) => 440 * Math.pow(2, (n - 69) / 12);   // número MIDI a Hz

  // ---------- efectos ----------
  const SFX = {
    tap: (t) => nota(880, t, 0.06, 'square', 0.12, sfxBus),
    select: (t) => { nota(N(76), t, 0.07, 'square', 0.14, sfxBus); nota(N(83), t + 0.06, 0.09, 'square', 0.14, sfxBus); },
    tick: (t) => nota(1500, t, 0.025, 'square', 0.05, sfxBus),
    pop: (t) => nota(300, t, 0.12, 'sine', 0.3, sfxBus, 900),
    coin: (t) => { nota(N(88), t, 0.07, 'square', 0.16, sfxBus); nota(N(93), t + 0.07, 0.22, 'square', 0.16, sfxBus); },
    whoosh: (t) => nota(200, t, 0.22, 'triangle', 0.18, sfxBus, 1200),
    lose: (t) => { nota(N(67), t, 0.16, 'triangle', 0.18, sfxBus); nota(N(63), t + 0.15, 0.3, 'triangle', 0.18, sfxBus); },
    win: (t) => [72, 76, 79, 84].forEach((n, i) => nota(N(n), t + i * 0.08, 0.16, 'square', 0.15, sfxBus)),
    fanfarria: (t) => { [72, 72, 72, 76, 79, 76, 79, 84].forEach((n, i) => nota(N(n), t + [0, .12, .24, .36, .6, .78, .9, 1.08][i], i === 7 ? 0.6 : 0.14, 'square', 0.16, sfxBus));
                        [48, 55, 60].forEach((n, i) => nota(N(n), t + i * 0.36, 0.5, 'triangle', 0.22, sfxBus)); }
  };
  function sfx(nombre) { if (!est.efectos) return; iniciar(); if (!ctx || !SFX[nombre]) return; SFX[nombre](ctx.currentTime + 0.01); }

  // ---------- música generativa: 5 estilos que se turnan, acordes y melodías que cambian solos ----------
  const ESTILOS = [
    { n: 'Pop', bpm: 118, raiz: 60, escala: [0, 2, 4, 7, 9], progs: [[0, 5, 3, 4], [0, 3, 4, 4], [5, 3, 0, 4]], lead: 'square', bajo: 'triangle', patBajo: [1, 0, 0, 0, 1, 0, 1, 0], bat: 'pop' },
    { n: 'Tropical', bpm: 104, raiz: 65, escala: [0, 2, 4, 7, 9], progs: [[0, 4, 5, 3], [0, 3, 4, 0], [3, 4, 0, 5]], lead: 'marimba', bajo: 'sine', patBajo: [1, 0, 0, 1, 0, 0, 1, 0], bat: 'tresillo' },
    { n: 'Lo-fi', bpm: 82, raiz: 62, escala: [0, 3, 5, 7, 10], progs: [[0, 3, 5, 4], [5, 3, 0, 0], [0, 5, 3, 4]], lead: 'triangle', bajo: 'sine', patBajo: [1, 0, 0, 0, 0, 0, 1, 0], bat: 'lofi', swing: .18 },
    { n: 'Aventura', bpm: 128, raiz: 62, escala: [0, 2, 3, 5, 7, 9, 10], progs: [[0, 6, 5, 6], [0, 3, 6, 4], [0, 5, 6, 0]], lead: 'square', bajo: 'sawtooth', patBajo: [1, 0, 1, 0, 1, 0, 1, 0], bat: 'pop', arpe: true },
    { n: 'Fiesta', bpm: 138, raiz: 67, escala: [0, 2, 4, 5, 7, 9, 11], progs: [[0, 4, 0, 4], [0, 3, 4, 0], [0, 5, 3, 4]], lead: 'sawtooth', bajo: 'square', patBajo: [1, 0, 1, 1, 1, 0, 1, 1], bat: 'fiesta' }
  ];
  const ACORDE = { 0: [0, 4, 7], 3: [5, 9, 12], 4: [7, 11, 14], 5: [9, 12, 16], 6: [10, 14, 17] };   // grados del acorde en semitonos
  let estilo = ESTILOS[Math.floor(Math.random() * ESTILOS.length)], prog = estilo.progs[0], motivo = [], compas = 0, energia = 0.35, ruido = null, cambiar = false;
  function nuevoMotivo() { motivo = Array.from({ length: 8 }, (_, i) => (i % 2 === 0 || Math.random() < .45) ? Math.floor(Math.random() * 5) : null); }
  function siguienteEstilo() { const otros = ESTILOS.filter(e => e !== estilo); estilo = otros[Math.floor(Math.random() * otros.length)]; prog = estilo.progs[Math.floor(Math.random() * estilo.progs.length)]; nuevoMotivo(); compas = 0; }
  function golpe(t, tipo, vol) {
    if (!ruido) { ruido = ctx.createBuffer(1, ctx.sampleRate * .3, ctx.sampleRate); const d = ruido.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
    if (tipo === 'bombo') { nota(140, t, .16, 'sine', vol * 1.6, musBus, 45); return; }
    const s = ctx.createBufferSource(), f = ctx.createBiquadFilter(), g = ctx.createGain(); s.buffer = ruido;
    f.type = tipo === 'tarola' ? 'bandpass' : 'highpass'; f.frequency.value = tipo === 'tarola' ? 1800 : 7000;
    const dur = tipo === 'tarola' ? .14 : .04; g.gain.setValueAtTime(vol, t); g.gain.exponentialRampToValueAtTime(.0001, t + dur);
    s.connect(f); f.connect(g); g.connect(musBus); s.start(t); s.stop(t + dur + .02);
  }
  function tocarLead(f, t, dur, vol) {
    if (estilo.lead === 'marimba') { nota(f, t, .22, 'sine', vol * 1.6, musBus); nota(f * 4, t, .06, 'sine', vol * .4, musBus); }
    else nota(f, t, dur, estilo.lead, estilo.lead === 'sawtooth' ? vol * .6 : vol, musBus);
  }
  const PASOS_COMPAS = 8;
  function programar() {
    if (!ctx) return;
    const s = 60 / estilo.bpm / 2;
    while (siguiente < ctx.currentTime + .3) {
      const k = paso % PASOS_COMPAS, grado = prog[compas % prog.length], ac = ACORDE[grado] || ACORDE[0];
      const t = siguiente + (estilo.swing && k % 2 ? s * estilo.swing : 0), raiz = estilo.raiz;
      const capaMel = energia > .2, capaArp = energia > .5 || estilo.arpe, capaBat = energia > .3;
      // bajo
      if (estilo.patBajo[k]) nota(N(raiz - 24 + ac[k % 4 === 0 ? 0 : (k % 3 ? 0 : 2)]), t, s * 1.7, estilo.bajo, .11, musBus);
      // acorde suave al inicio del compás
      if (k === 0) ac.forEach(x => nota(N(raiz - 12 + x), t, s * PASOS_COMPAS * .95, 'triangle', .022, musBus));
      // arpegio
      if (capaArp && k % 2 === 1) nota(N(raiz + ac[(k >> 1) % 3]), t, s * .8, 'square', .025, musBus);
      // melodía: motivo transportado al acorde, con variaciones
      if (capaMel) { const m = motivo[k]; if (m !== null && m !== undefined && !(compas % 4 === 3 && k > 4)) {
        const esc = estilo.escala, idx = (m + grado + (compas % 8 >= 4 ? 1 : 0)) % esc.length, oct = (m + grado) >= esc.length ? 12 : 0;
        tocarLead(N(raiz + esc[idx] + oct), t, s * (k % 4 === 0 ? 1.6 : .85), .045); } }
      // batería por estilo
      if (capaBat) {
        const b = estilo.bat;
        if (b === 'pop') { if (k === 0 || k === 4) golpe(t, 'bombo', .12); if (k === 2 || k === 6) golpe(t, 'tarola', .05); if (energia > .6) golpe(t, 'plato', .015); }
        if (b === 'tresillo') { if (k === 0 || k === 3 || k === 6) golpe(t, 'bombo', .1); if (k === 4) golpe(t, 'tarola', .04); if (k % 2) golpe(t, 'plato', .012); }
        if (b === 'lofi') { if (k === 0 || k === 5) golpe(t, 'bombo', .1); if (k === 4) golpe(t, 'tarola', .035); if (k % 2 === 0) golpe(t, 'plato', .008); }
        if (b === 'fiesta') { if (k % 2 === 0) golpe(t, 'bombo', .1); if (k % 4 === 2) golpe(t, 'tarola', .05); golpe(t, 'plato', .01); }
      }
      siguiente += s; paso++;
      if (paso % PASOS_COMPAS === 0) {
        compas++;
        if (compas % 4 === 0 && Math.random() < .5) nuevoMotivo();                       // nueva idea melódica
        if (compas % 8 === 0) prog = estilo.progs[Math.floor(Math.random() * estilo.progs.length)];   // nueva progresión
        if (cambiar || compas >= 32) { cambiar = false; transicion(); }                     // otro estilo cada ~minuto
      }
    }
  }
  function transicion() {
    const t0 = ctx.currentTime; musBus.gain.setTargetAtTime(0, t0, .5);
    setTimeout(() => { siguienteEstilo(); if (musTimer) musBus.gain.setTargetAtTime(VOL_MUS, ctx.currentTime, .8); }, 1400);
  }
  const VOL_MUS = 0.32;
  function arrancarMusica() {
    if (!ctx || musTimer) return; if (!motivo.length) nuevoMotivo(); siguiente = ctx.currentTime + .1;
    musBus.gain.cancelScheduledValues(ctx.currentTime); musBus.gain.setTargetAtTime(VOL_MUS, ctx.currentTime, .8);
    musTimer = setInterval(programar, 80);
  }
  function pararMusica() { if (!ctx || !musTimer) return; musBus.gain.setTargetAtTime(0, ctx.currentTime, .2); clearInterval(musTimer); musTimer = null; }
  document.addEventListener('visibilitychange', () => { if (!ctx) return; if (document.hidden) pararMusica(); else if (est.musica) arrancarMusica(); });

  // ---------- confeti ----------
  function confeti() {
    if (menosMov) return;
    const c = document.createElement('canvas'); c.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:99999';
    c.width = innerWidth; c.height = innerHeight; document.body.appendChild(c);
    const g = c.getContext('2d'), col = ['#E07812', '#F5A04A', '#13233A', '#3DBE7A', '#FFFFFF', '#E5484D'];
    const ps = Array.from({ length: 140 }, () => ({ x: innerWidth / 2 + (Math.random() - .5) * 120, y: innerHeight * .35, vx: (Math.random() - .5) * 14,
      vy: -Math.random() * 13 - 4, r: Math.random() * 6 + 4, c: col[Math.floor(Math.random() * col.length)], a: Math.random() * 6.28, va: (Math.random() - .5) * .3 }));
    let f = 0; (function cuadro() {
      g.clearRect(0, 0, c.width, c.height);
      ps.forEach(p => { p.vy += .32; p.vx *= .99; p.x += p.vx; p.y += p.vy; p.a += p.va; g.save(); g.translate(p.x, p.y); g.rotate(p.a); g.fillStyle = p.c; g.fillRect(-p.r / 2, -p.r / 4, p.r, p.r / 2); g.restore(); });
      if (++f < 150) requestAnimationFrame(cuadro); else c.remove();
    })();
  }

  // ---------- logros ----------
  const vistos = new Set();
  function logro(texto, emoji) {
    if (vistos.has(texto)) return; vistos.add(texto);
    const d = document.createElement('div'); d.setAttribute('role', 'status');
    d.style.cssText = 'position:fixed;left:50%;top:84px;transform:translateX(-50%) translateY(-20px);opacity:0;z-index:99998;background:#13233A;color:#fff;border:3px solid #F5A04A;border-radius:18px;padding:10px 16px;font:800 15px "Plus Jakarta Sans",system-ui,sans-serif;box-shadow:0 10px 28px rgba(0,0,0,.3);display:flex;gap:10px;align-items:center;transition:all .35s;max-width:90vw';
    d.innerHTML = `<span style="font-size:26px">${emoji || '🏅'}</span><span><small style="display:block;color:#F5A04A;font-size:11px">¡Logro desbloqueado!</small>${texto}</span>`;
    document.body.appendChild(d); requestAnimationFrame(() => { d.style.opacity = 1; d.style.transform = 'translateX(-50%) translateY(0)'; });
    sfx('coin'); setTimeout(() => { d.style.opacity = 0; d.style.transform = 'translateX(-50%) translateY(-20px)'; setTimeout(() => d.remove(), 400); }, 2600);
  }
  function ganar(texto, emoji) { sfx('fanfarria'); confeti(); if (texto) setTimeout(() => logro(texto, emoji || '🏆'), 250); }

  // ---------- botón de sonido ----------
  function boton() {
    const b = document.createElement('div');
    b.style.cssText = 'position:fixed;right:14px;bottom:86px;z-index:99990;display:flex;flex-direction:column;align-items:flex-end;gap:6px;font:700 13px "Plus Jakarta Sans",system-ui,sans-serif';
    b.innerHTML = `<div id="jgMenu" style="background:#fff;border-radius:14px;box-shadow:0 6px 20px rgba(0,0,0,.2);padding:8px;display:none;gap:4px">
      <label style="display:flex;gap:8px;align-items:center;padding:6px 8px;cursor:pointer"><input type="checkbox" id="jgMus"> 🎵 Música</label>
      <label style="display:flex;gap:8px;align-items:center;padding:6px 8px;cursor:pointer"><input type="checkbox" id="jgSfx"> 🔔 Efectos</label>
      <button type="button" id="jgOtra" style="border:0;background:#FFF1E2;border-radius:10px;padding:8px;font:inherit;font-weight:800;color:#13233A;cursor:pointer">⏭️ Otra canción</button></div>
      <button type="button" id="jgBtn" aria-label="Sonido" style="width:50px;height:50px;border-radius:50%;border:3px solid #F5A04A;background:#13233A;color:#fff;font-size:22px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25)"></button>`;
    document.body.appendChild(b);
    const pint = () => { document.getElementById('jgBtn').textContent = est.musica || est.efectos ? '🔊' : '🔇'; document.getElementById('jgMus').checked = est.musica; document.getElementById('jgSfx').checked = est.efectos; };
    document.getElementById('jgBtn').onclick = (e) => { e.stopPropagation(); const m = document.getElementById('jgMenu'); m.style.display = m.style.display === 'grid' ? 'none' : 'grid'; };
    document.getElementById('jgMus').onchange = (e) => { est.musica = e.target.checked; guardar(); iniciar(); est.musica ? arrancarMusica() : pararMusica(); pint(); };
    document.getElementById('jgOtra').onclick = () => { iniciar(); if (!est.musica) { est.musica = true; guardar(); pint(); } if (!musTimer) { siguienteEstilo(); arrancarMusica(); } else cambiar = true; };
    document.getElementById('jgSfx').onchange = (e) => { est.efectos = e.target.checked; guardar(); pint(); if (est.efectos) sfx('select'); };
    document.addEventListener('click', (e) => { if (!b.contains(e.target)) document.getElementById('jgMenu').style.display = 'none'; });
    pint();
  }

  // ---------- sonidos automáticos en botones y barras ----------
  document.addEventListener('pointerdown', () => iniciar(), { once: true, capture: true });
  document.addEventListener('keydown', () => iniciar(), { once: true, capture: true });
  document.addEventListener('click', (e) => {
    const el = e.target.closest('button, a, input[type=checkbox]'); if (!el || el.closest('#jgMenu') || el.id === 'jgBtn') return;
    if (el.classList.contains('fav') || el.matches('.fav, [data-fav]')) return sfx('pop');
    if (el.classList.contains('prim') || el.classList.contains('quiero') || el.classList.contains('pr-cta')) return sfx('whoosh');
    if (el.tagName === 'A') return sfx('tap');
    sfx('select');
  }, true);
  let ultimoTick = 0;
  document.addEventListener('input', (e) => { if (e.target.type === 'range' && performance.now() - ultimoTick > 70) { ultimoTick = performance.now(); sfx('tick'); } }, true);

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boton); else boton();
  window.Juego = { sfx, logro, confeti, ganar, musica: (on) => { est.musica = on; guardar(); iniciar(); on ? arrancarMusica() : pararMusica(); },
    energia: (v) => { energia = Math.max(0, Math.min(1, v)); }, otraCancion: () => { cambiar = true; }, estilo: () => estilo.n };
})();
