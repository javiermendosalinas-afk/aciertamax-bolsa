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
    whatsapp: { t: '💬 Hablar con un asesor', u: 'https://wa.me/523333777337?text=' + encodeURIComponent('Hola, vengo de inmobiliaria.pro y quiero hablar con un asesor') }
  };
  const SUG = ['¿Cuánto me presta el banco?', '¿Cómo uso mi Infonavit?', '¿Qué desarrollos me recomiendas?', '¿Qué es Acierta Verifica?'];
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  let historial = [], endpoint = 'https://aciertamax-webhook.onrender.com/api/sofia', abierto = false, enRecorrido = /te-acompanamos/.test(location.pathname);
  fetch('/camino-datos.json').then(r => r.json()).then(j => { if (j.endpoint) endpoint = j.endpoint.replace(/\/api\/camino.*$/, '/api/sofia'); }).catch(() => {});
  try { historial = JSON.parse(sessionStorage.getItem('ipro_preguntas') || '[]'); } catch (e) {}
  const css = document.createElement('style');
  css.textContent = `.pq-fab{position:fixed;left:14px;bottom:86px;z-index:99980;display:flex;align-items:center;gap:8px;background:#E07812;color:#fff;border:3px solid #fff;border-radius:999px;padding:6px 14px 6px 6px;font:800 14px 'Plus Jakarta Sans',system-ui,sans-serif;box-shadow:0 6px 18px rgba(0,0,0,.25);cursor:pointer}
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
    if (!historial.length) burbuja(lista, 'ia', '¡Qué onda! Pregúntanos lo que quieras: crédito, Infonavit, zonas, desarrollos, cómo revisar una casa antes de comprar… Te contestamos como amigos que saben del tema.', 'Sofía');
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
    if (window.Voz && Voz.activa()) Voz.decir(res.quien, res.texto);
    if (window.Juego) Juego.sfx('coin');
  }
  function boton() {
    const b = document.createElement('button'); b.type = 'button'; b.className = 'pq-fab'; b.setAttribute('aria-label', 'Pregúntale a Sofía y Diego');
    b.innerHTML = '<img src="/assets/avatares/sofia.svg" alt=""><span>Pregúntanos</span>'; b.onclick = () => abrir(); document.body.appendChild(b);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boton); else boton();
  window.Pregunta = { abrir };
})();
