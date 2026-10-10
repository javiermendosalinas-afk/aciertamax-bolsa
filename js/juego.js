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

  // ---------- música original (bucle de 4 compases, tipo chiptune alegre) ----------
  const MEL = [76, 79, 81, 79, 76, 74, 72, 74, 76, 76, 79, 81, 84, 81, 79, 0, 81, 81, 79, 76, 79, 76, 74, 72, 74, 76, 74, 72, 69, 72, 0, 0];
  const BAJO = [48, 48, 55, 55, 53, 53, 55, 55];
  const PASO_S = 60 / 128 / 2;   // corcheas a 128 bpm
  function programar() {
    if (!ctx) return;
    while (siguiente < ctx.currentTime + 0.25) {
      const m = MEL[paso % MEL.length]; if (m) nota(N(m), siguiente, PASO_S * 0.9, 'square', 0.05, musBus);
      if (paso % 4 === 0) { const b = BAJO[Math.floor(paso / 4) % BAJO.length]; nota(N(b), siguiente, PASO_S * 3.6, 'triangle', 0.12, musBus); }
      if (paso % 2 === 1) nota(6000, siguiente, 0.02, 'square', 0.012, musBus);   // charleston suave
      siguiente += PASO_S; paso++;
    }
  }
  function arrancarMusica() {
    if (!ctx || musTimer) return; siguiente = ctx.currentTime + 0.1;
    musBus.gain.cancelScheduledValues(ctx.currentTime); musBus.gain.setTargetAtTime(0.55, ctx.currentTime, 0.6);
    musTimer = setInterval(programar, 90);
  }
  function pararMusica() { if (!ctx || !musTimer) return; musBus.gain.setTargetAtTime(0, ctx.currentTime, 0.2); clearInterval(musTimer); musTimer = null; }
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
      <label style="display:flex;gap:8px;align-items:center;padding:6px 8px;cursor:pointer"><input type="checkbox" id="jgSfx"> 🔔 Efectos</label></div>
      <button type="button" id="jgBtn" aria-label="Sonido" style="width:50px;height:50px;border-radius:50%;border:3px solid #F5A04A;background:#13233A;color:#fff;font-size:22px;cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.25)"></button>`;
    document.body.appendChild(b);
    const pint = () => { document.getElementById('jgBtn').textContent = est.musica || est.efectos ? '🔊' : '🔇'; document.getElementById('jgMus').checked = est.musica; document.getElementById('jgSfx').checked = est.efectos; };
    document.getElementById('jgBtn').onclick = (e) => { e.stopPropagation(); const m = document.getElementById('jgMenu'); m.style.display = m.style.display === 'grid' ? 'none' : 'grid'; };
    document.getElementById('jgMus').onchange = (e) => { est.musica = e.target.checked; guardar(); iniciar(); est.musica ? arrancarMusica() : pararMusica(); pint(); };
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
  window.Juego = { sfx, logro, confeti, ganar, musica: (on) => { est.musica = on; guardar(); iniciar(); on ? arrancarMusica() : pararMusica(); } };
})();
