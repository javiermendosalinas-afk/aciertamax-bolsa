"""inmobiliaria.pro · Páginas por presupuesto con Sofía y Diego.

A diferencia de acierta.pro (páginas por colonia), aquí cada página responde «¿qué alcanza con mi dinero?»:
  /presupuesto/<municipio|zmg>/<tipo>-en-<venta|renta>-hasta-<monto>.html
con comentarios de Sofía y Diego generados con los datos reales de cada propiedad (texto único por página),
tabla de lo que alcanza por colonia, preguntas frecuentes, mapa del sitio y robots.txt.
Uso: python herramientas/generar_presupuesto.py
"""
import hashlib, html, json, os, re, shutil, statistics, unicodedata
from datetime import datetime, timezone

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITIO = "https://inmobiliaria.pro"
WA = "523333777337"
HOY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
E = lambda s: html.escape(str(s if s is not None else ""), quote=True)
GRUPOS = {"casa": ["casa", "casa en condominio", "casa con uso de suelo", "quinta", "villa"], "departamento": ["departamento"], "terreno": ["terreno"]}
PLURAL = {"casa": "Casas", "departamento": "Departamentos", "terreno": "Terrenos"}
SLUG = {"casa": "casas", "departamento": "departamentos", "terreno": "terrenos"}
TOPES = {("casa", "VENTA"): [2e6, 3e6, 4e6, 5e6, 7e6, 10e6], ("departamento", "VENTA"): [2e6, 3e6, 4e6, 5e6, 7e6],
         ("terreno", "VENTA"): [1e6, 2e6, 3e6, 5e6], ("casa", "RENTA"): [10e3, 15e3, 20e3, 30e3, 50e3],
         ("departamento", "RENTA"): [8e3, 12e3, 15e3, 20e3, 30e3]}
AVATAR = {"Sofía": "/assets/avatares/sofia.svg", "Diego": "/assets/avatares/diego.svg"}


def slug(s):
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def dinero(x):
    return "${:,.0f}".format(x) if x else "—"


def monto_txt(v):
    return f"{v / 1e6:g} millones" if v >= 1e6 else f"{v / 1e3:g} mil"


def monto_slug(v):
    return f"{v / 1e6:g}-millones".replace(".", "-") if v >= 1e6 else f"{v / 1e3:g}-mil"


def grupo_de(t):
    return next((g for g, v in GRUPOS.items() if t in v), None)


def pm2(p):
    sup = p.get("terreno") if p["grupo"] == "terreno" else (p.get("construccion") or p.get("m2"))
    return p["precio"] / sup if sup and sup > 0 else None


def url_pres(muni, g, op, tope):
    return f"/presupuesto/{slug(muni) if muni else 'zmg'}/{SLUG[g]}-en-{'renta' if op == 'RENTA' else 'venta'}-hasta-{monto_slug(tope)}.html"


def quien(clave):
    return "Sofía" if int(hashlib.md5(clave.encode()).hexdigest(), 16) % 2 else "Diego"


def comentario(p, ref_pm2):
    """Comentario corto y único del asesor para una propiedad (varias formas de decirlo, elegidas por la clave)."""
    h = int(hashlib.md5(p["eb"].encode()).hexdigest(), 16)
    elige = lambda opciones, k=0: opciones[(h >> (k * 4)) % len(opciones)]
    frases = []
    v = pm2(p)
    if v and ref_pm2:
        d = (v / ref_pm2 - 1) * 100
        x = abs(d)
        if d <= -45:
            frases.append("Su precio por m² está muy por debajo de la zona: confirma superficie y estado antes de emocionarte")
        elif d <= -12:
            frases.append(elige([f"Está {x:.0f}% abajo del precio por m² de la zona, de lo que más rinde",
                                 f"Por m² sale {x:.0f}% más barata que el promedio de la zona",
                                 f"Es de las que más rinden: {x:.0f}% abajo del m² de la zona"]))
        elif d >= 12:
            frases.append(elige([f"Cuesta {x:.0f}% más por m² que la zona; pregunta qué lo justifica",
                                 f"Su m² está {x:.0f}% arriba del promedio: revisa acabados y ubicación",
                                 f"Va {x:.0f}% arriba del m² de la zona; vale la pena negociar"]))
        else:
            frases.append(elige(["Trae un precio por m² en línea con la zona", "Su precio por m² es justo para la zona",
                                 "Está en el precio normal de la zona"]))
    r = int(p.get("recamaras") or 0)
    if p["grupo"] != "terreno":
        if r >= 3:
            frases.append(elige([f"Tiene {r} recámaras, buena para familia", f"Con {r} recámaras cabe toda la familia",
                                 f"{r} recámaras: espacio de sobra"], 1))
        elif r == 1 and p["grupo"] == "departamento":
            frases.append(elige(["Una recámara, ideal si vives solo o para rentar", "Perfecto como primer depa o para inversión"], 1))
        if p.get("terreno") and p.get("construccion") and p["terreno"] > p["construccion"] * 1.4:
            frases.append(elige([f"Con {round(p['terreno'])} m² de terreno hay espacio para crecer",
                                 f"El terreno de {round(p['terreno'])} m² da para jardín o ampliación"], 2))
    elif p.get("terreno"):
        frases.append(f"Son {round(p['terreno']):,} m² de terreno")
    if not frases:
        frases.append("Vale la pena verla en persona")
    return ". ".join(frases[:2]) + "."


def cargar():
    data = json.load(open(os.path.join(RAIZ, "data.json"), encoding="utf-8"))
    out = []
    for p in data:
        g = grupo_de(p.get("tipo"))
        if g and p.get("precio") and p.get("municipio") and (p.get("moneda") in (None, "", "MXN")):
            out.append(dict(p, grupo=g, colonia=(p.get("colonia") or "").strip()))
    return out


def med(xs):
    xs = [x for x in xs if x]
    return statistics.median(xs) if xs else None


CSS = """
.pr-wrap{max-width:1100px;margin:0 auto;padding:22px 18px 40px;font-family:'Plus Jakarta Sans',system-ui,sans-serif;color:#1d2433}
.pr-migas{font-size:14px;color:#5b6575;margin-bottom:10px}.pr-migas a{color:#5b6575}
.pr-h1{font-size:clamp(1.6rem,4.4vw,2.4rem);line-height:1.15;color:#13233A;margin:4px 0 6px;font-weight:800}
.pr-sub{color:#5b6575;margin:0 0 18px}
.pr-burbuja{display:flex;gap:14px;align-items:flex-start;margin:14px 0}.pr-burbuja img{width:64px;height:64px;flex:none}
.pr-burbuja .txt{background:#fff;border-radius:4px 18px 18px 18px;padding:14px 16px;box-shadow:0 2px 10px rgba(19,35,58,.08);line-height:1.6;position:relative}
.pr-burbuja .txt b.n{display:block;color:#E07812;font-size:.85rem;letter-spacing:.04em;margin-bottom:2px}
.pr-burbuja.der{flex-direction:row-reverse}.pr-burbuja.der .txt{border-radius:18px 4px 18px 18px;background:#FFF6EC}
.pr-datos{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin:16px 0}
.pr-datos div{background:#13233A;color:#fff;border-radius:16px;padding:12px 14px}.pr-datos b{display:block;font-size:1.35rem;color:#F5A04A}.pr-datos span{font-size:.82rem;color:#cdd7e4}
.pr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:16px;margin-top:12px}
.pr-card{background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 3px 14px rgba(19,35,58,.09);display:flex;flex-direction:column}
.pr-card .foto{position:relative;aspect-ratio:4/3;background:#13233A}.pr-card .foto img{width:100%;height:100%;object-fit:cover;display:block}
.pr-card .precio{position:absolute;left:10px;bottom:10px;background:#F5A04A;color:#13233A;font-weight:800;border-radius:999px;padding:6px 12px;font-size:1rem}
.pr-card .cuerpo{padding:12px 14px 14px;display:flex;flex-direction:column;gap:8px;flex:1}
.pr-card .tit{font-weight:700;color:#13233A;line-height:1.3;font-size:.98rem}
.pr-card .meta{font-size:.84rem;color:#5b6575}
.pr-card .dice{display:flex;gap:8px;align-items:flex-start;background:#FFF6EC;border-radius:12px;padding:8px 10px;font-size:.86rem;line-height:1.45}
.pr-card .dice img{width:30px;height:30px;flex:none}
.pr-card .ver{margin-top:auto;text-align:center;background:#13233A;color:#fff;border-radius:999px;padding:9px;font-weight:700;text-decoration:none}
.pr-sec{background:#fff;border-radius:20px;padding:18px 20px;margin-top:20px;box-shadow:0 2px 10px rgba(19,35,58,.06)}
.pr-sec h2{color:#13233A;font-size:1.25rem;margin:0 0 10px}
.pr-tabla{width:100%;border-collapse:collapse;font-size:.95rem}.pr-tabla th,.pr-tabla td{padding:8px 10px;border-bottom:1px solid #eef1f5;text-align:left}.pr-tabla th{color:#5b6575;font-weight:600}
.pr-chips{display:flex;flex-wrap:wrap;gap:8px}.pr-chips a{border:1.5px solid #E07812;color:#13233A;border-radius:999px;padding:7px 13px;text-decoration:none;font-weight:600;font-size:.9rem}
.pr-chips a.on{background:#E07812;color:#fff}
.pr-faq dt{font-weight:700;margin-top:12px;color:#13233A}.pr-faq dd{margin:4px 0 0;line-height:1.55}
.pr-cta{display:inline-block;background:#E07812;color:#fff;border-radius:999px;padding:12px 20px;font-weight:800;text-decoration:none;margin-top:10px}
.pr-aviso{font-size:.8rem;color:#5b6575;margin-top:14px}
"""


def cabeza(titulo, desc, canon, img=None, extra=""):
    return f"""<!DOCTYPE html>
<html lang="es-MX"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{E(titulo)}</title><meta name="description" content="{E(desc)}"><link rel="canonical" href="{SITIO}{canon}">
<meta property="og:type" content="website"><meta property="og:title" content="{E(titulo)}"><meta property="og:description" content="{E(desc)}"><meta property="og:url" content="{SITIO}{canon}">
<meta property="og:image" content="{E(img or SITIO + '/assets/marca/og-inmobiliaria-pro.jpg')}"><meta property="og:site_name" content="inmobiliaria.pro"><meta property="og:locale" content="es_MX">
<meta name="theme-color" content="#13233A"><link rel="icon" type="image/png" href="/assets/marca/favicon-32.png">
<link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/presupuesto.css">{extra}</head>
<body style="background:#F6F7FB"><header class="site-header"><div class="header-inner">
<a href="/"><img src="/assets/marca/logo-oscuro.png" alt="inmobiliaria.pro" style="height:34px;width:auto"></a>
<nav class="header-nav"><a href="/presupuesto/">¿Cuánto tienes?</a><a href="/mapa.html">Mapa</a></nav>
<a class="header-cta" href="https://wa.me/{WA}?text=Hola%2C%20vi%20una%20propiedad%20en%20inmobiliaria.pro" target="_blank" rel="noopener">Escríbenos →</a>
</div></header><main class="pr-wrap">"""


PIE = """<p class="pr-aviso">Sofía y Diego son asesores virtuales de inmobiliaria.pro: sus comentarios se generan con los datos publicados de cada propiedad. Precios de oferta sujetos a confirmación. Operado por Acierta Max, S.A. de C.V.</p>
</main><footer class="site-footer">inmobiliaria.pro · Solo inmobiliarios profesionales · Zona Metropolitana de Guadalajara · <a href="/presupuesto/">Busca por presupuesto</a></footer></body></html>"""


def burbuja(nombre, texto, derecha=False):
    return f'<div class="pr-burbuja{" der" if derecha else ""}"><img src="{AVATAR[nombre]}" alt="{nombre}, asesor virtual" width="64" height="64"><div class="txt"><b class="n">{nombre.upper()} DICE</b>{texto}</div></div>'


def tarjeta(p, ref):
    q = quien(p["eb"])
    meta = " · ".join(x for x in ((p["colonia"] or p["municipio"]), f"{int(p['recamaras'])} rec" if p.get("recamaras") else "",
                                  f"{round(p.get('construccion') or p.get('m2') or 0)} m²" if p["grupo"] != "terreno" and (p.get("construccion") or p.get("m2")) else "") if x)
    foto = f'<img src="{E(p["foto"])}" alt="{E(p["titulo"])}" loading="lazy">' if p.get("foto") else ""
    url = f"/ficha.html?eb={E(p['eb'])}&amp;op={E(p['operacion'])}"
    return f"""<article class="pr-card"><a class="foto" href="{url}">{foto}<span class="precio">{dinero(p['precio'])}{'/mes' if p['operacion'] == 'RENTA' else ''}</span></a>
<div class="cuerpo"><a class="tit" href="{url}" style="text-decoration:none">{E(p['titulo'].split(' | ')[0])}</a><div class="meta">📍 {E(meta)}</div>
<div class="dice"><img src="{AVATAR[q]}" alt="{q}" width="30" height="30"><span><b>{q}:</b> {E(comentario(p, ref))}</span></div>
<a class="ver" href="{url}">Verla</a></div></article>"""


def pagina(muni, g, op, tope, lista, todos_muni, vecinos):
    opn = "renta" if op == "RENTA" else "venta"
    lugar = muni or "la Zona Metropolitana de Guadalajara"
    ref = med(pm2(p) for p in todos_muni)
    precios = [p["precio"] for p in lista]
    sup = [p.get("terreno") if g == "terreno" else (p.get("construccion") or p.get("m2")) for p in lista]
    rec = [p.get("recamaras") for p in lista if p.get("recamaras")]
    st = {"n": len(lista), "med": med(precios), "sup": med(sup), "rec": med(rec)}
    # colonias donde más rinde: más m² por peso, con 3 o más opciones
    cols = {}
    for p in lista:
        if p["colonia"]:
            cols.setdefault(p["colonia"], []).append(p)
    tabla_cols = sorted(((c, len(l), med(x["precio"] for x in l), med((x.get("terreno") if g == "terreno" else (x.get("construccion") or x.get("m2"))) for x in l)) for c, l in cols.items() if len(l) >= 3),
                        key=lambda r: -((r[3] or 0) / (r[2] or 1)))
    rinde = ", ".join(c for c, *_ in tabla_cols[:3])
    titulo_h1 = f"{PLURAL[g]} en {opn} en {muni or 'Guadalajara y su zona metropolitana'} por menos de ${monto_txt(tope)}"
    canon = url_pres(muni, g, op, tope)
    a1 = quien(canon)
    a2 = "Diego" if a1 == "Sofía" else "Sofía"
    txt1 = (f"Encontré <b>{st['n']} {PLURAL[g].lower()}</b> en {opn} en {E(lugar)} de hasta ${monto_txt(tope)}. "
            f"La mitad cuesta menos de <b>{dinero(st['med'])}{'/mes' if op == 'RENTA' else ''}</b>. "
            + (f"Con ese presupuesto lo típico son <b>{st['rec']:g} recámaras</b> y " if st['rec'] and g != 'terreno' else "Lo típico son ")
            + f"<b>{round(st['sup']) if st['sup'] else '—'} m²</b>."
            + (f" Donde más m² te dan por tu dinero: <b>{E(rinde)}</b>." if rinde else ""))
    if op == "RENTA":
        txt2 = "Un consejo de amigo: pide el contrato por escrito, revisa qué incluye la renta (mantenimiento, agua) y nunca deposites sin conocer el inmueble y a quien lo renta."
    elif g == "terreno":
        txt2 = "Un consejo de amigo: antes de apartar un terreno, pide el uso de suelo y revisa que los servicios (agua, luz, drenaje) lleguen hasta el lote. Te ahorras sorpresas."
    else:
        txt2 = f"Un consejo de amigo: además del precio, separa entre 5% y 8% para escrituración e impuestos. Y si te gusta una, pide una revisión antes de firmar; no es desconfianza, es cuidar tu dinero."
    def rinde_clave(p):
        r = (pm2(p) / ref) if pm2(p) and ref else 1.5
        return (r if r >= 0.55 else 3 + r, -p["precio"])      # datos atípicos (más de 45% abajo) al final
    orden = sorted(lista, key=rinde_clave)[:36]
    faq = [(f"¿Qué {PLURAL[g].lower()} hay en {opn} en {lugar} por menos de ${monto_txt(tope)}?",
            f"Hay {st['n']} {PLURAL[g].lower()} publicadas en inmobiliaria.pro al {HOY}, con un precio mediano de {dinero(st['med'])}" + (f" y una superficie típica de {round(st['sup'])} m²." if st['sup'] else ".")),
           (f"¿En qué colonias rinde más un presupuesto de ${monto_txt(tope)}?",
            (f"Las colonias con más m² por peso en este rango son {rinde}." if rinde else "Todavía no hay suficientes opciones por colonia para compararlas.") + " Revisa siempre el estado del inmueble y sus documentos.")]
    ld = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
    ld2 = {"@context": "https://schema.org", "@type": "ItemList", "name": titulo_h1, "numberOfItems": st["n"],
           "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": f"{SITIO}/ficha.html?eb={p['eb']}&op={p['operacion']}", "name": p["titulo"].split(" | ")[0]} for i, p in enumerate(orden[:20])]}
    desc = f"{st['n']} {PLURAL[g].lower()} en {opn} en {lugar} por menos de ${monto_txt(tope)}. Sofía y Diego te dicen qué alcanza y dónde rinde más tu dinero."
    h = cabeza(f"{titulo_h1} ({st['n']}) | inmobiliaria.pro", desc, canon, orden[0].get("foto") if orden else None,
               f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script><script type="application/ld+json">{json.dumps(ld2, ensure_ascii=False)}</script>')
    h += f'<nav class="pr-migas"><a href="/">Inicio</a> › <a href="/presupuesto/">¿Cuánto tienes?</a> › {E(muni or "Toda la ZMG")}</nav>'
    h += f'<h1 class="pr-h1">{E(titulo_h1)}</h1><p class="pr-sub">Actualizado al {HOY} · te lo explicamos como amigos, con datos reales</p>'
    h += burbuja(a1, txt1) + burbuja(a2, E(txt2), derecha=True)
    h += f'''<div class="pr-datos"><div><b>{st["n"]}</b><span>opciones</span></div><div><b>{dinero(st["med"])}</b><span>precio mediano</span></div>
<div><b>{round(st["sup"]) if st["sup"] else "—"} m²</b><span>superficie típica</span></div>{f'<div><b>{st["rec"]:g}</b><span>recámaras típicas</span></div>' if st["rec"] and g != "terreno" else ""}</div>'''
    h += '<div class="pr-chips">' + "".join(f'<a class="{"on" if t == tope else ""}" href="{url_pres(muni, g, op, t)}">Hasta ${monto_txt(t)}</a>' for t in vecinos) + "</div>"
    h += f'<section class="pr-sec"><h2>Las que más rinden, primero</h2><div class="pr-grid">{"".join(tarjeta(p, ref) for p in orden)}</div>'
    if st["n"] > 36:
        h += f'<p>Te mostramos 36 de {st["n"]}. <a href="/mapa.html">Ver todas en el mapa</a>.</p>'
    h += "</section>"
    if tabla_cols:
        h += '<section class="pr-sec"><h2>Qué alcanza por colonia</h2><div style="overflow-x:auto"><table class="pr-tabla"><tr><th>Colonia</th><th>Opciones</th><th>Precio mediano</th><th>m² típicos</th></tr>' + "".join(
            f"<tr><td>{E(c)}</td><td>{n}</td><td>{dinero(pr)}</td><td>{round(s) if s else '—'}</td></tr>" for c, n, pr, s in tabla_cols[:15]) + "</table></div></section>"
    h += '<section class="pr-sec"><h2>Preguntas frecuentes</h2><dl class="pr-faq">' + "".join(f"<dt>{E(q)}</dt><dd>{E(a)}</dd>" for q, a in faq) + "</dl>"
    h += f'<a class="pr-cta" href="https://wa.me/{WA}?text=' + E(f"Hola, busco {PLURAL[g].lower()} en {opn} en {lugar} por menos de ${monto_txt(tope)}") + '" target="_blank" rel="noopener">Platícanos qué buscas</a></section>'
    return h + PIE


def main():
    props = cargar()
    shutil.rmtree(os.path.join(RAIZ, "presupuesto"), ignore_errors=True)
    with open(os.path.join(RAIZ, "presupuesto.css"), "w", encoding="utf-8") as fh:
        fh.write(CSS.strip() + "\n")
    urls, indice = [], {}
    munis = sorted({p["municipio"] for p in props})
    for (g, op), topes in TOPES.items():
        for muni in [None] + munis:
            base = [p for p in props if p["grupo"] == g and p["operacion"] == op and (muni is None or p["municipio"] == muni)]
            validos = [t for t in topes if sum(1 for p in base if p["precio"] <= t) >= 5]
            for t in validos:
                lista = [p for p in base if p["precio"] <= t]
                u = url_pres(muni, g, op, t)
                ruta = os.path.join(RAIZ, u.lstrip("/"))
                os.makedirs(os.path.dirname(ruta), exist_ok=True)
                open(ruta, "w", encoding="utf-8").write(pagina(muni, g, op, t, lista, base, validos))
                urls.append(u)
                indice.setdefault(muni or "Toda la ZMG", []).append((g, op, t, len(lista), u))
    # índice
    h = cabeza("¿Cuánto tienes? Casas, departamentos y terrenos por presupuesto en Guadalajara | inmobiliaria.pro",
               "Dinos tu presupuesto y Sofía y Diego te enseñan qué casas, departamentos y terrenos alcanzan en Guadalajara, Zapopan, Tlaquepaque, Tonalá y Tlajomulco.", "/presupuesto/")
    h += '<h1 class="pr-h1">¿Cuánto tienes? Te enseñamos qué alcanza</h1><p class="pr-sub">Elige tu municipio y tu presupuesto · actualizado al ' + HOY + "</p>"
    h += burbuja("Sofía", "Hola, soy Sofía. Con Diego revisamos todas las propiedades para decirte, sin rodeos, qué te alcanza con tu dinero y dónde rinde más.")
    h += burbuja("Diego", "Y si algo te late, te ayudamos a revisarlo antes de que des un peso. Empieza eligiendo tu zona 👇", derecha=True)
    for zona in ["Toda la ZMG"] + munis:
        if zona not in indice:
            continue
        h += f'<section class="pr-sec"><h2>{E(zona)}</h2>'
        for (g, op) in TOPES:
            items = [x for x in indice[zona] if x[0] == g and x[1] == op]
            if items:
                h += f'<p style="margin:10px 0 6px;font-weight:700;color:#13233A">{PLURAL[g]} en {"renta" if op == "RENTA" else "venta"}</p><div class="pr-chips">' + "".join(
                    f'<a href="{u}">Hasta ${monto_txt(t)} ({n})</a>' for _, _, t, n, u in items) + "</div>"
        h += "</section>"
    os.makedirs(os.path.join(RAIZ, "presupuesto"), exist_ok=True)
    open(os.path.join(RAIZ, "presupuesto", "index.html"), "w", encoding="utf-8").write(h + PIE)
    urls.insert(0, "/presupuesto/")
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "\n".join(
        f"<url><loc>{SITIO}{u}</loc><lastmod>{HOY}</lastmod></url>" for u in urls) + "\n</urlset>\n"
    open(os.path.join(RAIZ, "sitemap-presupuesto.xml"), "w", encoding="utf-8").write(xml)
    rob = os.path.join(RAIZ, "robots.txt")
    r = open(rob, encoding="utf-8").read().splitlines() if os.path.exists(rob) else ["User-agent: *", "Allow: /"]
    r = [ln for ln in r if "sitemap-presupuesto.xml" not in ln]
    r.append(f"Sitemap: {SITIO}/sitemap-presupuesto.xml")
    open(rob, "w", encoding="utf-8").write("\n".join(r) + "\n")
    print(f"inmobiliaria.pro · páginas por presupuesto: {len(urls):,}", flush=True)


if __name__ == "__main__":
    main()
