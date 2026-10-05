"""Trae el inventario de la bolsa NeoJaus que genera el repo acierta-pro-web
(herramientas/neojaus/neojaus.json) y lo publica como data.json de este sitio,
con la liga de cada ficha apuntando a inmobiliaria.pro.
Si la descarga falla o viene casi vacía, se conserva el inventario vigente."""
import json, os, sys
from collections import Counter
from datetime import datetime, timezone
import requests

FUENTE = "https://raw.githubusercontent.com/javiermendosalinas-afk/acierta-pro-web/main/herramientas/neojaus/neojaus.json"
SITIO = "https://inmobiliaria.pro"
MUNICIPIOS = ["Guadalajara", "Tlajomulco de Zúñiga", "Tlaquepaque", "Tonalá", "Zapopan"]

def main():
    try:
        r = requests.get(FUENTE, timeout=60)
        r.raise_for_status()
        datos = r.json()
    except Exception as e:
        print(f"No se pudo descargar la bolsa ({e}); se conserva el inventario vigente")
        return 0
    previo = json.load(open("data.json", encoding="utf-8")) if os.path.exists("data.json") else []
    if len(datos) < 100 or (previo and len(datos) < len(previo) * 0.5):
        print(f"[FRENO] La bolsa trae {len(datos)} fichas (antes {len(previo)}): se conserva el inventario vigente")
        return 0
    for d in datos:
        d["liga"] = f"{SITIO}/ficha.html?eb={d['eb']}&op={d['operacion']}"
    datos.sort(key=lambda f: (f["operacion"], f["municipio"], -(f.get("precio") or 0)))
    with open("data.json", "w", encoding="utf-8") as fh:
        json.dump(datos, fh, ensure_ascii=False, separators=(",", ":"))
    with open("inventario-meta.json", "w", encoding="utf-8") as fh:
        json.dump({"actualizado": datetime.now(timezone.utc).isoformat(timespec="seconds"), "total": len(datos),
                   "por_segmento": dict(Counter(f.get("segmento") for f in datos)), "municipios": MUNICIPIOS},
                  fh, ensure_ascii=False, indent=1)
    print(f"Bolsa publicada: {len(datos):,} fichas")
    return 0

if __name__ == "__main__":
    sys.exit(main())
