/* inmobiliaria.pro · "Pregúntale a Sofía y Diego": preguntas libres con IA (endpoint /api/sofia de MAX).
   Usa window.PERFIL_IPRO (si la página lo define) para personalizar. Integra Voz y Juego si están cargados. */
(function () {
  'use strict';
  const AV = { 'Sofía': '/assets/avatares/sofia-senala.svg', 'Diego': '/assets/avatares/diego.svg' };
  const ACC = {
    recorrido: { t: '🧭 Calcular cuánto me prestan y agendar', u: '/te-acompanamos.html' },
    presupuesto: { t: '💰 Ver qué alcanza con mi dinero', u: '/presupuesto/' },
    verifica: { t: '✅ Conocer Acierta Verifica', u: 'https://acierta.pro/verifica.html' },
    bellavittoria: { t: '🏢 Ver Bella Vittoria', u: 'https://residencialbellavittoria.com' },
    eleve: { t: '🏙️ Ver Élevé Valle Real', u: 'https://acierta.pro/blog/eleve-valle-real-zapopan.html' },
    villadhara: { t: '🌳 Ver Villa Dhara', u: 'https://acierta.pro/blog/villa-dhara-parque-morelos.html' },
    iteso: { t: '🎓 Ver el depa junto al ITESO', u: 'https://acierta.pro/ficha.html?eb=EB-WG7125&op=RENTA' },
    ideas: { t: '🛋️ Ideas de decoración e interiorismo', u: 'https://acierta.pro/blog/' },
    whatsapp: { t: '💬 Hablar con un asesor', u: 'https://wa.me/523333777337?text=' + encodeURIComponent('Hola, vengo de inmobiliaria.pro y quiero hablar con un asesor') }
  };
  const SUG = ['¿Cuánto me presta el banco?', '¿Cómo uso mi Infonavit?', '¿Qué desarrollos me recomiendas?', '¿Qué es Acierta Verifica?', '¿Qué papeles pido antes de comprar?', 'Ideas para decorar un depa chico'];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let historial = [], endpoint = 'https://aciertamax-webhook.onrender.com/api/sofia', abierto = false, enRecorrido = /te-acompanamos/.test(location.pathname);
  fetch('/camino-datos.json').then(r => r.json()).then(j => { if (j.endpoint) endpoint = j.endpoint.replace(/\/api\/camino.*$/, '/api/sofia'); }).catch(() => {});
  try { historial = JSON.parse(sessionStorage.getItem('ipro_preguntas') || '[]'); } catch (e) {}
  const css = document.createElement('style');
  css.textContent = `.pq-fab{position:fixed;left:14px;bottom:var(--fab-abajo,16px);z-index:99980;display:flex;align-items:center;gap:8px;background:#E07812;color:#fff;border:3px solid #fff;border-radius:999px;padding:6px 14px 6px 6px;font:800 14px 'Plus Jakarta Sans',system-ui,sans-serif;box-shadow:0 6px 18px rgba(0,0,0,.25);cursor:pointer}
.pq-fab img{width:38px;height:38px;border-radius:50%;background:#FFF1E2;object-fit:cover;object-position:top}
.pq{position:fixed;inset:0;z-index:100001;background:rgba(5,12,26,.55);display:flex;align-items:flex-end;justify-content:center}
.pq .hoja{background:#F6F7FB;width:min(560px,100%);height:min(86vh,720px);border-radius:22px 22px 0 0;display:flex;flex-direction:column;font-family:'Plus Jakarta Sans',system-ui,sans-serif}
.pq .cab{display:flex;align-items:center;gap:8px;padding:12px 14px;background:#13233A;color:#fff;border-radius:22px 22px 0 0}.pq .cab img{width:40px;height:44px}.pq .cab b{flex:1}
.pq .cab button{border:0;background:rgba(255,255,255,.15);color:#fff;border-radius:99px;width:36px;height:36px;font-size:20px;cursor:pointer}
.pq .lista{flex:1;overflow:auto;padding:12px}.pq .m{display:flex;gap:8px;align-items:flex-end;margin:8px 0}.pq .m img{width:42px;height:auto;flex:none}
.pq .m .b{background:#fff;border-radius:6px 18px 18px 18px;padding:10px 12px;line-height:1.5;white-space:pre-line;box-shadow:0 2px 6px rgba(19,35,58,.07);font-size:.95rem}
.pq .m.diego .b{background:#E4ECF6}.pq .m.yo{justify-content:flex-end}.pq .m.yo .b{background:#13233A;color:#fff;border-radius:18px 6px 18px 18px}
.pq .quien{display:block;font-size:.75rem;font-weight:800;color:#E07812}.pq .acc{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 0 50px}
.pq .acc a,.pq .acc button{border:2px solid #E07812;background:#fff;color:#13233A;border-radius:999px;padding:7px 11px;font:inherit;font-weight:700;font-size:.85rem;text-decoration:none;cursor:pointer}
.pq .sug{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 8px}.pq .sug button{border:1.5px solid #DCE1EA;background:#fff;border-radius:999px;padding:7px 11px;font:inherit;font-size:.85rem;cursor:pointer;color:#13233A}
.pq form{display:flex;gap:8px;padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:#fff;border-top:1px solid #E3E7EF}
.pq input{flex:1;font:inherit;padding:11px 14px;border:2px solid #DCE1EA;border-radius:999px}.pq input:focus{outline:3px solid #F5A04A;outline-offset:1px}
.pq form button{border:0;border-radius:999px;padding:0 16px;font:inherit;font-weight:800;cursor:pointer;background:#E07812;color:#fff}.pq form .mic{background:#13233A}
.pq .res{margin:6px 0 4px 50px;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.pq .res a{background:#fff;border-radius:14px;overflow:hidden;text-decoration:none;color:#13233A;box-shadow:0 2px 6px rgba(19,35,58,.1);font-size:.82rem}
.pq .res img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#13233A}.pq .res div{padding:6px 8px}.pq .res b{color:#E07812;display:block;font-size:.95rem}
.pq .mapa-btn{display:block;margin:6px 0 4px 50px;background:#13233A;color:#fff;border-radius:999px;padding:10px 14px;text-align:center;font-weight:800;text-decoration:none}
.pq .alt{margin:4px 0 0 50px;display:flex;flex-wrap:wrap;gap:6px}.pq .alt button{border:2px solid #E07812;background:#FFF6EC;border-radius:999px;padding:7px 11px;font:inherit;font-weight:700;font-size:.82rem;color:#13233A;cursor:pointer}
.pq .escribe{color:#5b6575;font-size:.85rem;margin:6px 0 0 50px}
@media(max-width:560px){.pq-fab{padding:4px}.pq-fab span{display:none}}`;
  document.head.appendChild(css);
  function contexto() { const p = window.PERFIL_IPRO || {}; return Object.assign({ pagina: document.title.split('|')[0].trim().slice(0, 60) }, p); }
  function burbuja(lista, rol, texto, quien, acciones) {
    const d = document.createElement('div');
    if (rol === 'yo') { d.className = 'm yo'; d.innerHTML = `<div class="b">${esc(texto)}</div>`; }
    else { d.className = 'm' + (quien === 'Diego' ? ' diego' : ''); d.innerHTML = `<img src="${AV[quien] || AV['Sofía']}" alt="${quien}" width="42"><div class="b"><span class="quien">${quien}</span>${esc(texto)}</div>`; }
    lista.appendChild(d);
    if (acciones && acciones.length) {
      const a = document.createElement('div'); a.className = 'acc';
      a.innerHTML = acciones.map(k => ACC[k] ? (k === 'recorrido' && enRecorrido ? `<button type="button" data-cerrar="1">🧭 Seguir con mi búsqueda</button>` : `<a href="${ACC[k].u}" ${/^https?:/.test(ACC[k].u) && !/inmobiliaria\.pro/.test(ACC[k].u) ? 'target="_blank" rel="noopener"' : ''}>${ACC[k].t}</a>`) : '').join('');
      lista.appendChild(a); a.querySelectorAll('[data-cerrar]').forEach(b => b.onclick = cerrar);
    }
    lista.scrollTop = lista.scrollHeight;
  }
  let DATOS = null;
  const cargarDatos = () => DATOS ? Promise.resolve(DATOS) : fetch('/presupuesto/buscador.json').then(r => r.json()).then(j => DATOS = j).catch(() => DATOS = []);
  const din = v => '$' + Math.round(v || 0).toLocaleString('es-MX');
  function filtrar(b) { return (DATOS || []).filter(p => p.o === b.o && p.g === b.g && (!b.m || p.m === b.m) && (!b.tope || p.p <= b.tope) && (b.g === 't' || !b.rec || p.r >= b.rec) && [...(b.k || '')].every(c => (p.k || '').includes(c))); }
  function urlMapa(b) { return '/presupuesto/#' + new URLSearchParams(Object.assign({ o: b.o, g: b.g, m: b.m || '', r: b.rec || 0, tope: b.tope || (b.o === 'R' ? 20000 : 4000000), vista: 'mapa' }, b.k ? { k: b.k } : {})); }
  async function mostrarBusqueda(lista, b) {
    await cargarDatos(); const L = filtrar(b).sort((x, y) => x.p - y.p);
    const tipo = { c: 'casas', d: 'depas', t: 'terrenos' }[b.g] || 'opciones';
    if (L.length) {
      const r = document.createElement('div'); r.className = 'res';
      r.innerHTML = L.slice(0, 4).map(p => `<a href="/ficha.html?eb=${encodeURIComponent(p.e)}&op=${p.o === 'V' ? 'VENTA' : 'RENTA'}">${p.f ? `<img src="${esc(p.f)}" alt="" loading="lazy">` : '<img alt="">'}<div><b>${din(p.p)}${p.o === 'R' ? '/mes' : ''}</b>${esc(p.c || p.m)}${p.r ? ` · ${p.r} rec` : ''}${(p.k || '').includes('M') ? ' · 🐾' : ''}${(p.k || '').includes('F') ? ' · 🛋️' : ''}</div></a>`).join('');
      lista.appendChild(r);
    }
    const m = document.createElement('a'); m.className = 'mapa-btn'; m.href = urlMapa(b);
    m.textContent = L.length ? `🗺️ Ver las ${L.length} ${tipo} en el mapa` : '🗺️ Abrir el mapa con esta búsqueda'; lista.appendChild(m);
    if (L.length < 5) {
      const alts = [];
      if (b.tope) { const b2 = Object.assign({}, b, { tope: Math.round(b.tope * 1.15 / 500) * 500 }); alts.push([`Hasta ${din(b2.tope)} (${filtrar(b2).length})`, b2]); }
      if (b.g === 'd') { const b2 = Object.assign({}, b, { g: 'c' }); alts.push([`También casas (${filtrar(b2).length})`, b2]); }
      if (b.m) { const b2 = Object.assign({}, b, { m: '' }); alts.push([`En toda la ZMG (${filtrar(b2).length})`, b2]); }
      if (b.k) { const b2 = Object.assign({}, b, { k: '' }); alts.push([`Sin indispensables (${filtrar(b2).length})`, b2]); }
      if (b.rec > 1) { const b2 = Object.assign({}, b, { rec: b.rec - 1 }); alts.push([`${b.rec - 1}+ recámaras (${filtrar(b2).length})`, b2]); }
      const buenas = alts.filter(a => filtrar(a[1]).length > L.length);
      if (buenas.length) {
        const nota = document.createElement('div'); nota.className = 'escribe'; nota.textContent = L.length ? 'Hay pocas así. Si abres un poquito la búsqueda:' : 'Así exacto no hay ahorita. Si abres un poquito la búsqueda:'; lista.appendChild(nota);
        const a = document.createElement('div'); a.className = 'alt'; a.innerHTML = buenas.map((x, i) => `<button type="button" data-i="${i}">${esc(x[0])}</button>`).join(''); lista.appendChild(a);
        a.querySelectorAll('button').forEach(bt => bt.onclick = () => { a.remove(); nota.remove(); mostrarBusqueda(lista, buenas[+bt.dataset.i][1]); });
      }
    }
    lista.scrollTop = lista.scrollHeight;
  }
  let capa = null;
  function cerrar() { if (capa) { capa.remove(); capa = null; document.body.style.overflow = ''; abierto = false; } }
  function abrir(pregunta) {
    if (abierto) return; abierto = true;
    capa = document.createElement('div'); capa.className = 'pq';
    capa.innerHTML = `<div class="hoja" role="dialog" aria-label="Pregúntale a Sofía y Diego"><div class="cab"><img src="/assets/avatares/sofia.svg" alt=""><img src="/assets/avatares/diego.svg" alt=""><b>Pregúntale a Sofía y Diego</b><button type="button" aria-label="Cerrar">×</button></div>
      <div class="lista" id="pqLista"></div><div class="sug" id="pqSug">${SUG.map(s => `<button type="button">${esc(s)}</button>`).join('')}</div>
      <form id="pqForm"><input id="pqIn" placeholder="Escribe tu pregunta…" autocomplete="off" maxlength="500">${window.Voz && Voz.puedeOir ? '<button type="button" class="mic" id="pqMic" aria-label="Preguntar hablando">🎙️</button>' : ''}<button type="submit">Enviar</button></form></div>`;
    document.body.appendChild(capa); document.body.style.overflow = 'hidden';
    const lista = capa.querySelector('#pqLista');
    capa.querySelector('.cab button').onclick = cerrar; capa.onclick = (e) => { if (e.target === capa) cerrar(); };
    if (!historial.length) burbuja(lista, 'ia', '¡Qué onda! Pregúntanos lo que quieras: crédito, Infonavit, zonas, desarrollos, escrituras y contratos, cómo revisar una casa antes de comprar, y hasta ideas para decorarla. Te contestamos como amigos que saben del tema.', 'Sofía');
    historial.forEach(h => burbuja(lista, h.rol === 'usuario' ? 'yo' : 'ia', h.texto, h.quien, h.acciones));
    capa.querySelectorAll('#pqSug button').forEach(b => b.onclick = () => enviar(b.textContent));
    capa.querySelector('#pqForm').onsubmit = (e) => { e.preventDefault(); const v = capa.querySelector('#pqIn').value.trim(); if (v) enviar(v); };
    const mic = capa.querySelector('#pqMic');
    if (mic) mic.onclick = async () => { mic.textContent = '👂'; try { const t = await Voz.escuchar(); mic.textContent = '🎙️'; enviar(t.split(' | ')[0]); } catch (e) { mic.textContent = '🎙️'; } };
    setTimeout(() => { const i = capa && capa.querySelector('#pqIn'); if (i && !pregunta) i.focus(); }, 60);
    if (pregunta) enviar(pregunta);
  }
  async function enviar(texto) {
    if (!capa) return; const lista = capa.querySelector('#pqLista'), inp = capa.querySelector('#pqIn');
    inp.value = ''; capa.querySelector('#pqSug').style.display = 'none';
    historial.push({ rol: 'usuario', texto }); burbuja(lista, 'yo', texto);
    const e = document.createElement('div'); e.className = 'escribe'; e.textContent = 'Sofía y Diego están escribiendo…'; lista.appendChild(e); lista.scrollTop = lista.scrollHeight;
    let res;
    try { const r = await fetch(endpoint, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ mensajes: historial.slice(-10).map(h => ({ rol: h.rol, texto: h.texto })), contexto: contexto() }) });
      res = await r.json(); } catch (err) { res = { ok: false, error: 'No pudimos conectar. Revisa tu internet.' }; }
    e.remove();
    if (!res || !res.ok) { burbuja(lista, 'ia', (res && res.error) || 'No pude contestar ahorita. Escríbenos por WhatsApp y te atiende un asesor.', 'Diego', ['whatsapp']); return; }
    historial.push({ rol: 'asistente', texto: res.texto, quien: res.quien, acciones: res.acciones });
    try { sessionStorage.setItem('ipro_preguntas', JSON.stringify(historial.slice(-20))); } catch (err) {}
    burbuja(lista, 'ia', res.texto, res.quien, res.acciones);
    if (res.busqueda) await mostrarBusqueda(lista, res.busqueda);
    if (window.Voz && Voz.activa()) Voz.decir(res.quien, res.texto);
    if (window.Juego) Juego.sfx('coin');
  }
  function boton() {
    if (document.querySelector('.fi-barra')) document.documentElement.style.setProperty('--fab-abajo', '86px');
    const b = document.createElement('button'); b.type = 'button'; b.className = 'pq-fab'; b.setAttribute('aria-label', 'Pregúntale a Sofía y Diego');
    b.innerHTML = '<img src="/assets/avatares/sofia.svg" alt=""><span>Pregúntanos</span>'; b.onclick = () => abrir(); document.body.appendChild(b);
  }
  // Todo botón de WhatsApp lleva lo que el cliente ya eligió, para que MAX continúe desde ahí
  function mensajeConContexto(base) {
    let S = {}; try { S = JSON.parse(localStorage.getItem('ipro_acomp') || '{}'); } catch (e) {}
    const P = window.PERFIL_IPRO || {}, d = v => '$' + Math.round(v).toLocaleString('es-MX'), partes = [];
    if (S.nombre) partes.push(`Soy ${S.nombre}.`);
    if (S.operacion || S.tipo) {
      let b = `Busco ${S.operacion === 'renta' ? 'rentar' : 'comprar'} ${({ casa: 'casa', departamento: 'depa', terreno: 'terreno' })[S.tipo] || ''}`.trim();
      if (S.municipio && S.municipio !== 'cualquiera') b += ` en ${S.municipio}${S.zona ? ` (zona de ${S.zona.r} km que marqué en el mapa)` : ''}`;
      if (S.presupuesto) b += ` hasta ${d(S.presupuesto)}${S.operacion === 'renta' ? ' al mes' : ''}`;
      if (S.recamaras) b += `, ${S.recamaras}+ recámaras`;
      if ((S.imprescindibles || []).length) b += `, con: ${S.imprescindibles.join(', ')}`;
      partes.push(b + '.');
    }
    if (S.precalif && S.precalif.alcance) partes.push(`Mi precalificación estimada: hasta ${d(S.precalif.alcance)}.`);
    const fav = (S.seleccion && S.seleccion.length ? S.seleccion : S.favoritas) || [];
    if (fav.length) partes.push(`Mis favoritas: ${fav.slice(0, 3).join(', ')}.`);
    if (P.clave) partes.push(`Me interesa la ${P.clave}: ${P.viendo_propiedad || ''} (${P.precio || ''}).`);
    if (S.folio) partes.push(`Folio ${S.folio}.`);
    base = base.trim(); if (!/[.!?)]$/.test(base)) base += '.';
    return (base + ' ' + partes.join(' ')).trim().slice(0, 700);
  }
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href*="wa.me/523333777337"]'); if (!a) return;
    try { const u = new URL(a.href), base = (u.searchParams.get('text') || 'Hola, vengo de inmobiliaria.pro.').split(' Soy ')[0];
      const msg = mensajeConContexto(/inmobiliaria\.pro/.test(base) ? base : base + ' (vengo de inmobiliaria.pro)');
      u.searchParams.set('text', msg); a.href = u.toString(); } catch (err) {}
  }, true);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boton); else boton();
  window.Pregunta = { abrir };
})();
