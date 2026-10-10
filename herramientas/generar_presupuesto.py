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
AVATAR = {"Sofía": "/assets/avatares/sofia.svg", "Diego": "/assets/avatares/diego.svg", "Sofía celebra": "/assets/avatares/sofia-celebra.svg",
          "Sofía señala": "/assets/avatares/sofia-senala.svg", "Diego lupa": "/assets/avatares/diego-lupa.svg", "Diego pensando": "/assets/avatares/diego-pensando.svg"}


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


def mensualidad(precio, enganche=0.2, tasa=0.1013, anios=20):
    r, n = tasa / 12, anios * 12
    m = precio * (1 - enganche)
    return m * r / (1 - (1 + r) ** -n)


def explicacion(p, ref_pm2):
    """Lo bueno, ojo con esto, para quién es y recomendación, con los datos de la propiedad."""
    h = int(hashlib.md5(p["eb"].encode()).hexdigest(), 16)
    elige = lambda o, k=0: o[(h >> (k * 4)) % len(o)]
    v, r = pm2(p), int(p.get("recamaras") or 0)
    s = p.get("construccion") or p.get("m2") or 0
    d = (v / ref_pm2 - 1) * 100 if v and ref_pm2 else None
    bueno, ojo, para = [], [], ""
    if d is not None:
        if -45 < d <= -12:
            bueno.append(elige([f"Por m² sale {abs(d):.0f}% más barata que el promedio de la zona", f"Está {abs(d):.0f}% abajo del m² de la zona: de las que más rinden"]))
        elif d <= -45:
            ojo.append("Su precio por m² está demasiado abajo de la zona: confirma la superficie real y el estado")
        elif d >= 12:
            ojo.append(f"Su m² va {d:.0f}% arriba del promedio: pregunta qué lo justifica y negocia")
        else:
            bueno.append("Su precio por m² es justo para la zona")
    if p["grupo"] != "terreno":
        if r >= 3:
            bueno.append(f"{r} recámaras")
        if p.get("terreno") and s and p["terreno"] > s * 1.4:
            bueno.append(f"{round(p['terreno'])} m² de terreno, con espacio para crecer")
        if r and s and s / r < 22:
            ojo.append(f"Espacios compactos: unos {round(s / r)} m² por recámara")
        para = ("una familia que necesita espacio" if r >= 3 else "una pareja o tu primer depa" if r == 2 and p["grupo"] == "departamento"
                else "vivir solo o invertir para rentar" if r == 1 else "quien busca su primera casa" if p["grupo"] == "casa" else "quien busca buena ubicación")
    else:
        if p.get("terreno"):
            bueno.append(f"{round(p['terreno']):,} m² de terreno")
        para = "quien quiere construir a su gusto o invertir a largo plazo"
    if p["operacion"] == "RENTA":
        consejo = f"Para rentarla suelen pedir ingresos de unas 3 veces la renta (alrededor de {dinero(p['precio'] * 3)} al mes) y depósito de 1 a 2 meses. Pide contrato por escrito."
    elif p["grupo"] == "terreno":
        consejo = "Antes de apartar, pide el uso de suelo y confirma que agua, luz y drenaje lleguen hasta el lote."
    else:
        m = mensualidad(p["precio"])
        consejo = f"Con 20% de enganche ({dinero(p['precio'] * 0.2)}), la mensualidad rondaría {dinero(m)} a 20 años; te pedirían ingresos de unos {dinero(m / 0.3)} al mes. Y antes de firmar, pide una revisión."
    return {"bueno": "; ".join(bueno[:2]) or "Vale la pena verla en persona", "ojo": "; ".join(ojo[:2]) or "Nada raro en los datos; confírmalo en la visita",
            "para": para[0].upper() + para[1:], "consejo": consejo}


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
.pr-burbuja{display:flex;gap:14px;align-items:flex-end;margin:16px 0}.pr-burbuja figure{margin:0;flex:none;text-align:center}.pr-burbuja figure img{width:104px;height:auto;display:block}
.pr-burbuja figcaption{font-size:.75rem;font-weight:800;color:#13233A;background:#F5A04A;border-radius:999px;padding:2px 10px;display:inline-block;margin-top:-6px}
.pr-duo{display:flex;align-items:flex-end;justify-content:center;gap:10px;margin:8px 0 0}.pr-duo img{width:min(42vw,200px);height:auto}
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
.pr-card .dice{display:block;background:#FFF6EC;border-radius:14px;padding:10px 11px;font-size:.84rem;line-height:1.45}
.pr-card .dice::after{content:"";display:block;clear:both}
.pr-card .dice img{float:left;width:44px;height:auto;margin:0 8px 2px 0}.pr-card .dice > div > b:first-child{display:block;padding-top:8px;min-height:30px}.pr-card .dice b{color:#13233A}.pr-card .dice p{margin:4px 0 0}
.pr-card .dice p.tip{background:#fff;border-radius:10px;padding:6px 8px;margin-top:6px;border-left:3px solid #E07812}
.pr-card .ver{margin-top:auto;text-align:center;background:#13233A;color:#fff;border-radius:999px;padding:9px;font-weight:700;text-decoration:none}
.pr-sec{background:#fff;border-radius:20px;padding:18px 20px;margin-top:20px;box-shadow:0 2px 10px rgba(19,35,58,.06)}
.pr-sec h2{color:#13233A;font-size:1.25rem;margin:0 0 10px}
.pr-tabla{width:100%;border-collapse:collapse;font-size:.95rem}.pr-tabla th,.pr-tabla td{padding:8px 10px;border-bottom:1px solid #eef1f5;text-align:left}.pr-tabla th{color:#5b6575;font-weight:600}
.pr-chips{display:flex;flex-wrap:wrap;gap:8px}.pr-chips a{border:1.5px solid #E07812;color:#13233A;border-radius:999px;padding:7px 13px;text-decoration:none;font-weight:600;font-size:.9rem}
.pr-chips a.on{background:#E07812;color:#fff}
.pr-faq dt{font-weight:700;margin-top:12px;color:#13233A}.pr-faq dd{margin:4px 0 0;line-height:1.55}
.pr-cta{display:inline-block;background:#E07812;color:#fff;border-radius:999px;padding:12px 20px;font-weight:800;text-decoration:none;margin-top:10px}
.pr-aviso{font-size:.8rem;color:#5b6575;margin-top:14px}
.bq{background:#fff;border-radius:22px;padding:18px 20px;box-shadow:0 4px 18px rgba(19,35,58,.08);margin:18px 0}
.bq-paso{margin:12px 0 4px;font-weight:800;color:#13233A}.bq-paso span{color:#E07812;margin-right:6px}
.bq-ops{display:flex;flex-wrap:wrap;gap:8px}.bq-ops button{border:2px solid #E6E9F0;background:#fff;border-radius:16px;padding:10px 14px;font:inherit;font-weight:700;color:#13233A;cursor:pointer;display:flex;align-items:center;gap:8px}
.bq-ops button.on{border-color:#E07812;background:#FFF1E2}.bq-ops button .ico{font-size:1.4rem}
.bq-rango{display:flex;align-items:center;gap:14px;flex-wrap:wrap}.bq-rango input[type=range]{flex:1;min-width:220px;accent-color:#E07812}.bq-rango b{font-size:1.3rem;color:#E07812;min-width:150px}
.bq-res{display:grid;grid-template-columns:1.05fr .95fr;gap:18px;margin-top:14px;align-items:start}
#bqMapa{height:620px;border-radius:20px;overflow:hidden;position:sticky;top:12px;box-shadow:0 4px 18px rgba(19,35,58,.12)}
#bqMapa .leaflet-tile-pane{filter:sepia(.5) saturate(1.45) hue-rotate(-14deg) brightness(1.03) contrast(.95)}
.pin-precio{background:#F5A04A;color:#13233A;font-weight:800;font-size:12px;border-radius:999px;padding:3px 8px;border:2px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.25);white-space:nowrap;font-family:'Plus Jakarta Sans',sans-serif}
.pin-precio.top{background:#13233A;color:#F5A04A}
.bq-lista{display:grid;grid-template-columns:1fr 1fr;gap:12px}.bq-mas{grid-column:1/-1;text-align:center}
.bq-vacio{background:#FFF6EC;border-radius:16px;padding:16px;line-height:1.6}
@media(max-width:600px){.pr-burbuja figure img{width:78px}}
@media(max-width:900px){.bq-res{grid-template-columns:1fr}#bqMapa{height:380px;position:relative;order:-1}.bq-lista{grid-template-columns:1fr}}
"""


BUSCADOR = '''<link rel="stylesheet" href="/assets/vendor/leaflet/leaflet.css">
<section class="bq" id="buscador">
<div class="bq-paso"><span>1</span>¿Comprar o rentar?</div><div class="bq-ops" data-campo="o"><button data-v="V" class="on"><span class="ico">🔑</span>Comprar</button><button data-v="R"><span class="ico">📝</span>Rentar</button></div>
<div class="bq-paso"><span>2</span>¿Qué buscas?</div><div class="bq-ops" data-campo="g"><button data-v="c" class="on"><span class="ico">🏡</span>Casa</button><button data-v="d"><span class="ico">🏢</span>Depa</button><button data-v="t"><span class="ico">🌳</span>Terreno</button></div>
<div class="bq-paso"><span>3</span>¿Por dónde?</div><div class="bq-ops" data-campo="m"><button data-v="" class="on">📍 Donde sea</button><button data-v="Zapopan">Zapopan</button><button data-v="Guadalajara">Guadalajara</button><button data-v="Tlaquepaque">Tlaquepaque</button><button data-v="Tonalá">Tonalá</button><button data-v="Tlajomulco de Zúñiga">Tlajomulco</button></div>
<div class="bq-paso"><span>4</span>¿Cuánto tienes?</div><div class="bq-rango"><input type="range" id="bqTope" aria-label="Presupuesto máximo"><b id="bqTopeTxt"></b></div>
<div class="bq-paso" id="bqRecPaso"><span>5</span>¿Cuántas recámaras?</div><div class="bq-ops" data-campo="r" id="bqRec"><button data-v="0" class="on">Me da igual</button><button data-v="1">1 o más</button><button data-v="2">2 o más</button><button data-v="3">3 o más</button></div>
<div id="bqResumen"></div>
<div class="bq-res"><div><div class="bq-lista" id="bqLista"></div></div><div id="bqMapa"></div></div>
</section>
<script src="/assets/vendor/leaflet/leaflet.js"></script>
<script>
(function(){
const LF=window.L;
const AV={S:'/assets/avatares/sofia.svg',D:'/assets/avatares/diego.svg',SC:'/assets/avatares/sofia-celebra.svg',SS:'/assets/avatares/sofia-senala.svg',DL:'/assets/avatares/diego-lupa.svg',DP:'/assets/avatares/diego-pensando.svg'};
const ZONA={'Zapopan':'Zapopan es el que más oferta tiene. Por Valle Real, Puerta de Hierro y Andares está lo más caro; hacia Tesistán y la orilla norte encuentras precios más accesibles.',
 'Guadalajara':'En Guadalajara estás cerca de todo: Providencia, Chapultepec y la Americana concentran servicios y vida de barrio; el Centro y las colonias tradicionales tienen opciones más accesibles.',
 'Tlaquepaque':'Tlaquepaque está a un paso de Guadalajara, con el encanto de su Centro; buena relación entre precio y ubicación.',
 'Tonalá':'Tonalá tiene de los precios más accesibles de la zona metropolitana; revisa bien los servicios y las vialidades de cada colonia.',
 'Tlajomulco de Zúñiga':'En Tlajomulco hay fraccionamientos nuevos con buen precio por m². Antes de decidir, calcula tus traslados en hora pico por López Mateos o la carretera a Chapala.',
 '':'En toda la zona metropolitana hay de todo. Si tienes una zona en mente, elígela arriba y afino la búsqueda.'};
const RANGO={'Vc':[1e6,15e6,25e4,4e6],'Vd':[1e6,10e6,25e4,3e6],'Vt':[3e5,1e7,1e5,2e6],'Rc':[5e3,8e4,1e3,2e4],'Rd':[4e3,5e4,1e3,15e3],'Rt':[5e3,1e5,1e3,2e4]};
let D=[],ref={},est={o:'V',g:'c',m:'',r:0,tope:null},mapa,capa;
const $=id=>document.getElementById(id), esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const din=v=>'$'+Math.round(v).toLocaleString('es-MX'), corto=v=>v>=1e6?'$'+(v/1e6).toFixed(v>=1e7?0:1).replace('.0','')+'M':'$'+Math.round(v/1e3)+'k';
const sup=p=>p.g==='t'?p.t:(p.s||0), pm2=p=>sup(p)>0?p.p/sup(p):null;
const med=a=>{a=a.filter(x=>x).sort((x,y)=>x-y);return a.length?a[Math.floor(a.length/2)]:null};
const h=s=>{let x=0;for(const c of s)x=(x*31+c.charCodeAt(0))>>>0;return x};
function comentario(p){const k=h(p.e),el=(o,i)=>o[(k>>>(i*3))%o.length],f=[],r0=ref[p.m+p.g+p.o],v=pm2(p);
 if(v&&r0){const d=(v/r0-1)*100,x=Math.abs(d).toFixed(0);
  if(d<=-45)f.push('Su precio por m² está muy por debajo de la zona: confirma superficie y estado antes de emocionarte');
  else if(d<=-12)f.push(el([`Está ${x}% abajo del m² de la zona, de lo que más rinde`,`Por m² sale ${x}% más barata que el promedio`,`¡Ojo aquí! ${x}% abajo del m² de la zona`],0));
  else if(d>=12)f.push(el([`Cuesta ${x}% más por m² que la zona; pregunta qué lo justifica`,`Va ${x}% arriba del m² de la zona; hay margen para negociar`],0));
  else f.push(el(['Precio por m² justo para la zona','Está en el precio normal de la zona'],0));}
 if(p.g!=='t'){if(p.r>=3)f.push(el([`${p.r} recámaras: cabe toda la familia`,`Con ${p.r} recámaras hay espacio de sobra`],1));
  else if(p.r===1&&p.g==='d')f.push(el(['Ideal como primer depa o para rentar','Una recámara: perfecto si vives solo'],1));
  if(p.t&&p.s&&p.t>p.s*1.4)f.push(`Con ${p.t} m² de terreno hay espacio para crecer`);}
 else if(p.t)f.push(`Son ${p.t.toLocaleString('es-MX')} m² de terreno`);
 if(!f.length)f.push('Vale la pena verla en persona');return f.slice(0,2).join('. ')+'.';}
function explica(p){const k=h(p.e),el=(o,i)=>o[(k>>>(i*3))%o.length],r0=ref[p.m+p.g+p.o],v=pm2(p),s=p.s||0,d=v&&r0?(v/r0-1)*100:null,bueno=[],ojo=[];let para='';
 if(d!==null){if(d>-45&&d<=-12)bueno.push(el([`Por m² sale ${Math.abs(d).toFixed(0)}% más barata que el promedio de la zona`,`Está ${Math.abs(d).toFixed(0)}% abajo del m² de la zona: de las que más rinden`],0));
  else if(d<=-45)ojo.push('Su precio por m² está demasiado abajo de la zona: confirma la superficie real y el estado');
  else if(d>=12)ojo.push(`Su m² va ${d.toFixed(0)}% arriba del promedio: pregunta qué lo justifica y negocia`);else bueno.push('Su precio por m² es justo para la zona');}
 if(p.g!=='t'){if(p.r>=3)bueno.push(p.r+' recámaras');if(p.t&&s&&p.t>s*1.4)bueno.push(p.t+' m² de terreno, con espacio para crecer');if(p.r&&s&&s/p.r<22)ojo.push(`Espacios compactos: unos ${Math.round(s/p.r)} m² por recámara`);
  para=p.r>=3?'Una familia que necesita espacio':(p.r===2&&p.g==='d')?'Una pareja o tu primer depa':p.r===1?'Vivir solo o invertir para rentar':p.g==='c'?'Quien busca su primera casa':'Quien busca buena ubicación';}
 else{if(p.t)bueno.push(p.t.toLocaleString('es-MX')+' m² de terreno');para='Quien quiere construir a su gusto o invertir a largo plazo';}
 let tip;if(p.o==='R')tip=`Para rentarla suelen pedir ingresos de unas 3 veces la renta (alrededor de ${din(p.p*3)} al mes) y depósito de 1 a 2 meses. Pide contrato por escrito.`;
 else if(p.g==='t')tip='Antes de apartar, pide el uso de suelo y confirma que agua, luz y drenaje lleguen hasta el lote.';
 else{const r=.1013/12,n=240,m=p.p*.8*r/(1-Math.pow(1+r,-n));tip=`Con 20% de enganche (${din(p.p*.2)}), la mensualidad rondaría ${din(m)} a 20 años; te pedirían ingresos de unos ${din(m/.3)} al mes. Y antes de firmar, pide una revisión.`;}
 return{bueno:bueno.slice(0,2).join('; ')||'Vale la pena verla en persona',ojo:ojo.slice(0,2).join('; ')||'Nada raro en los datos; confírmalo en la visita',para,tip};}
function tarjeta(p){const X=explica(p),adv=!X.ojo.startsWith('Nada raro'),q=adv?'DL':'SS',n=adv?'Diego':'Sofía',vb=adv?'te advierte':'te explica',u='/ficha.html?eb='+encodeURIComponent(p.e)+'&op='+(p.o==='V'?'VENTA':'RENTA');
 const meta=[p.c||p.m,p.r?p.r+' rec':'',sup(p)?sup(p)+' m²':''].filter(Boolean).join(' · ');
 return `<article class="pr-card"><a class="foto" href="${u}">${p.f?`<img src="${esc(p.f)}" alt="" loading="lazy">`:''}<span class="precio">${din(p.p)}${p.o==='R'?'/mes':''}</span></a><div class="cuerpo"><a class="tit" href="${u}" style="text-decoration:none">${esc(p.x)}</a><div class="meta">📍 ${esc(meta)}</div>${(x=>`<div class="dice"><img src="${AV[q]}" alt="" width="46" height="50"><div><b>${n} ${vb}</b><p>👍 <b>Lo bueno:</b> ${esc(x.bueno)}.</p><p>⚠️ <b>Ojo:</b> ${esc(x.ojo)}.</p><p>🎯 <b>Para:</b> ${esc(x.para)}.</p><p class="tip">💡 ${esc(x.tip)}</p></div></div>`)(X)}<a class="ver" href="${u}">Verla</a></div></article>`;}
function rango(){const r=RANGO[est.o+est.g],s=$('bqTope');s.min=r[0];s.max=r[1];s.step=r[2];if(est.tope==null||est.tope<r[0]||est.tope>r[1])est.tope=r[3];s.value=est.tope;
 $('bqTopeTxt').textContent='Hasta '+din(est.tope)+(est.o==='R'?' al mes':'');$('bqRecPaso').style.display=$('bqRec').style.display=est.g==='t'?'none':'';}
let mostrar=24;
function pintar(){rango();
 const L=D.filter(p=>p.o===est.o&&p.g===est.g&&(!est.m||p.m===est.m)&&p.p<=est.tope&&(est.g==='t'||p.r>=est.r));
 const clave=p=>{const r0=ref[p.m+p.g+p.o],v=pm2(p),x=v&&r0?v/r0:1.5;return x>=.55?x:3+x};
 L.sort((a,b)=>clave(a)-clave(b)||b.p-a.p);
 const tipo={c:'casas',d:'depas',t:'terrenos'}[est.g],lugar=est.m||'toda la zona metropolitana';
 if(!L.length){$('bqResumen').innerHTML=`<div class="pr-burbuja"><figure><img src="${AV.DP}" alt="" width="104" height="113"><figcaption>Diego</figcaption></figure><div class="txt"><b class="n">DIEGO DICE</b>Mmm… con esos filtros no encontré ${tipo} en ${esc(lugar)}. Súbele tantito al presupuesto o prueba otra zona, ¡seguro sale algo!</div></div>`;$('bqLista').innerHTML='';capa.clearLayers();location.hash='';return;}
 const m=med(L.map(p=>p.p)),s=med(L.map(sup)),r=med(L.filter(p=>p.r).map(p=>p.r));
 const cols={};L.forEach(p=>{if(p.c)(cols[p.c]=cols[p.c]||[]).push(p)});
 const rinde=Object.entries(cols).filter(([,l])=>l.length>=3).map(([c,l])=>[c,med(l.map(sup))/med(l.map(p=>p.p))]).sort((a,b)=>b[1]-a[1]).slice(0,3).map(x=>x[0]);
 $('bqResumen').innerHTML=`<div class="pr-burbuja"><figure><img src="${AV.SC}" alt="" width="104" height="113"><figcaption>Sofía</figcaption></figure><div class="txt"><b class="n">SOFÍA DICE</b>¡Va! Encontré <b>${L.length} ${tipo}</b> para ${est.o==='V'?'comprar':'rentar'} en ${esc(lugar)} de hasta ${din(est.tope)}${est.o==='R'?' al mes':''}. La mitad cuesta menos de <b>${din(m)}</b>${s?` y lo típico son <b>${Math.round(s)} m²</b>`:''}${r&&est.g!=='t'?` con <b>${r} recámaras</b>`:''}.${rinde.length?` Donde más rinde tu lana: <b>${rinde.map(esc).join(', ')}</b>.`:''}</div></div>
 <div class="pr-burbuja der"><figure><img src="${AV.D}" alt="" width="104" height="113"><figcaption>Diego</figcaption></figure><div class="txt"><b class="n">DIEGO DICE</b>Ojo, ahí te va un tip: ${esc(ZONA[est.m])} Te las puse de las que más rinden a las que menos. ¿Quieres saber cuánto te prestan y que un asesor te acompañe? <a href="/te-acompanamos.html" style="color:#E07812;font-weight:800">Platica con nosotros</a>.</div></div>`;
 $('bqLista').innerHTML=L.slice(0,mostrar).map(tarjeta).join('')+(L.length>mostrar?`<div class="bq-mas"><button class="pr-cta" id="bqMas" style="border:0;cursor:pointer">Ver ${Math.min(24,L.length-mostrar)} más</button></div>`:'');
 const b=$('bqMas');if(b)b.onclick=()=>{mostrar+=24;pintar()};
 capa.clearLayers();const pts=[];L.slice(0,300).forEach((p,i)=>{if(!p.a)return;const mk=i<40?LF.marker([p.a,p.n],{zIndexOffset:i<10?1000:(40-i)*10,icon:LF.divIcon({className:'',html:`<span class="pin-precio${i<10?' top':''}">${corto(p.p)}</span>`,iconSize:null})}):LF.circleMarker([p.a,p.n],{radius:5,color:'#fff',weight:1.5,fillColor:'#E07812',fillOpacity:.85});
  mk.bindPopup(`<div style="width:200px">${p.f?`<img src="${esc(p.f)}" style="width:100%;height:110px;object-fit:cover;border-radius:8px">`:''}<b>${din(p.p)}</b><br>${esc(p.x)}<br><a href="/ficha.html?eb=${encodeURIComponent(p.e)}&op=${p.o==='V'?'VENTA':'RENTA'}" style="color:#E07812;font-weight:800">Verla →</a></div>`);mk.addTo(capa);pts.push([p.a,p.n]);});
 if(pts.length)mapa.fitBounds(pts,{padding:[30,30],maxZoom:14});
 history.replaceState(null,'','#'+new URLSearchParams({o:est.o,g:est.g,m:est.m,r:est.r,tope:est.tope}));}
document.querySelectorAll('.bq-ops').forEach(g=>g.addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;g.querySelectorAll('button').forEach(x=>x.classList.toggle('on',x===b));
 const c=g.dataset.campo;est[c]=c==='r'?+b.dataset.v:b.dataset.v;if(c==='o'||c==='g')est.tope=null;mostrar=24;pintar();}));
$('bqTope').addEventListener('input',e=>{est.tope=+e.target.value;mostrar=24;pintar();});
mapa=LF.map('bqMapa',{scrollWheelZoom:false}).setView([20.67,-103.38],11);
LF.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',{maxZoom:19,attribution:'© OpenStreetMap © CARTO'}).addTo(mapa);capa=LF.layerGroup().addTo(mapa);
const q=new URLSearchParams(location.hash.slice(1));['o','g','m'].forEach(k=>{if(q.has(k))est[k]=q.get(k)});if(q.has('r'))est.r=+q.get('r');if(q.has('tope'))est.tope=+q.get('tope');
document.querySelectorAll('.bq-ops').forEach(g=>{const c=g.dataset.campo;g.querySelectorAll('button').forEach(b=>b.classList.toggle('on',String(b.dataset.v)===String(est[c])))});
fetch('/presupuesto/buscador.json').then(r=>r.json()).then(j=>{D=j;const gr={};D.forEach(p=>{const v=pm2(p);if(v)(gr[p.m+p.g+p.o]=gr[p.m+p.g+p.o]||[]).push(v)});for(const k in gr)ref[k]=med(gr[k]);pintar();});
})();
</script>'''


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
<nav class="header-nav"><a href="/presupuesto/">¿Cuánto tienes?</a><a href="/mapa.html">Mapa</a><a href="/sofia-y-diego.html">Sofía y Diego</a></nav>
<a class="header-cta" href="https://wa.me/{WA}?text=Hola%2C%20vi%20una%20propiedad%20en%20inmobiliaria.pro" target="_blank" rel="noopener">Escríbenos →</a>
</div></header><main class="pr-wrap">"""


PIE = """<p class="pr-aviso"><a href="/sofia-y-diego.html">Sofía y Diego</a> son asesores virtuales de inmobiliaria.pro: sus comentarios se generan con los datos publicados de cada propiedad. Precios de oferta sujetos a confirmación. Operado por Acierta Max, S.A. de C.V.</p>
</main><footer class="site-footer">inmobiliaria.pro · Solo inmobiliarios profesionales · Zona Metropolitana de Guadalajara · <a href="/presupuesto/">Busca por presupuesto</a></footer></body></html>"""


def burbuja(nombre, texto, derecha=False, pose=None):
    return f'<div class="pr-burbuja{" der" if derecha else ""}"><figure><img src="{AVATAR[pose or nombre]}" alt="{nombre}, asesor virtual" width="104" height="113"><figcaption>{nombre}</figcaption></figure><div class="txt"><b class="n">{nombre.upper()} DICE</b>{texto}</div></div>'


def bloque_explica(q, x):
    advierte = not x["ojo"].startswith("Nada raro")
    q, pose, verbo = ("Diego", "Diego lupa", "te advierte") if advierte else ("Sofía", "Sofía señala", "te explica")
    return (f'<div class="dice"><img src="{AVATAR[pose]}" alt="{q}" width="46" height="50"><div><b>{q} {verbo}</b>'
            f'<p>👍 <b>Lo bueno:</b> {E(x["bueno"])}.</p><p>⚠️ <b>Ojo:</b> {E(x["ojo"])}.</p><p>🎯 <b>Para:</b> {E(x["para"])}.</p>'
            f'<p class="tip">💡 {E(x["consejo"])}</p></div></div>')


def tarjeta(p, ref):
    q = quien(p["eb"])
    meta = " · ".join(x for x in ((p["colonia"] or p["municipio"]), f"{int(p['recamaras'])} rec" if p.get("recamaras") else "",
                                  f"{round(p.get('construccion') or p.get('m2') or 0)} m²" if p["grupo"] != "terreno" and (p.get("construccion") or p.get("m2")) else "") if x)
    foto = f'<img src="{E(p["foto"])}" alt="{E(p["titulo"])}" loading="lazy">' if p.get("foto") else ""
    url = f"/ficha.html?eb={E(p['eb'])}&amp;op={E(p['operacion'])}"
    return f"""<article class="pr-card"><a class="foto" href="{url}">{foto}<span class="precio">{dinero(p['precio'])}{'/mes' if p['operacion'] == 'RENTA' else ''}</span></a>
<div class="cuerpo"><a class="tit" href="{url}" style="text-decoration:none">{E(p['titulo'].split(' | ')[0])}</a><div class="meta">📍 {E(meta)}</div>
{bloque_explica(q, explicacion(p, ref))}
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
        txt2 = "Pide el contrato por escrito, revisa qué incluye la renta (mantenimiento, agua) y nunca deposites sin conocer el inmueble y a quien lo renta."
    elif g == "terreno":
        txt2 = "Antes de apartar un terreno, pide el uso de suelo y revisa que los servicios (agua, luz, drenaje) lleguen hasta el lote. Te ahorras sorpresas."
    else:
        txt2 = f"Además del precio, separa entre 5% y 8% para escrituración e impuestos. Y si te gusta una, pide una revisión antes de firmar; no es desconfianza, es cuidar tu dinero."
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
    h += burbuja("Sofía", "¡Va! " + txt1, pose="Sofía celebra") + burbuja("Diego", "Ojo, ahí te va un tip: " + E(txt2[0].lower() + txt2[1:]), derecha=True)
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
    h += '<a class="pr-cta" href="/te-acompanamos.html">Platica con Sofía y Diego y agenda con un asesor</a></section>'
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
    h += '<div class="pr-duo"><img src="/assets/avatares/sofia.svg" alt="Sofía, asesora virtual" width="200" height="217"><img src="/assets/avatares/diego.svg" alt="Diego, asesor virtual" width="200" height="217"></div>'
    h += burbuja("Sofía", "¡Qué onda! Soy Sofía. Con Diego le echamos un ojo a todas las propiedades de la Perla Tapatía para decirte, sin rodeos, qué te alcanza y dónde rinde más tu lana.")
    h += burbuja("Diego", "Contéstanos cuatro cositas y te enseñamos las que valen la pena, en lista y en el mapa. ¿Le entramos? 👇", derecha=True)
    h += BUSCADOR
    h += '<h2 class="pr-h1" style="font-size:1.4rem;margin-top:28px">O ve directo a tu zona y presupuesto</h2>'
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
    ligero = [{"e": p["eb"], "o": p["operacion"][0], "g": p["grupo"][0], "m": p["municipio"], "c": p["colonia"], "p": round(p["precio"]),
               "r": int(p["recamaras"]) if p.get("recamaras") else 0, "s": round(p.get("construccion") or p.get("m2") or 0),
               "t": round(p.get("terreno") or 0), "f": p.get("foto") or "", "a": round(p["lat"], 5) if p.get("lat") else None,
               "n": round(p["lon"], 5) if p.get("lon") else None, "x": p["titulo"].split(" | ")[0][:90]} for p in props]
    with open(os.path.join(RAIZ, "presupuesto", "buscador.json"), "w", encoding="utf-8") as fh:
        json.dump(ligero, fh, ensure_ascii=False, separators=(",", ":"))
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
