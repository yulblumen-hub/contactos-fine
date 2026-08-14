#!/usr/bin/env python3
"""Genera data.js y los .vcf a partir de contactos.json.

contactos.json es la unica fuente de verdad: se edita ahi y se corre este script.

    python3 build.py
"""
import json
import pathlib
import re
import unicodedata

RAIZ = pathlib.Path(__file__).parent
DATOS = json.loads((RAIZ / "contactos.json").read_text(encoding="utf-8"))


def slug(texto):
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def escapar(valor):
    """Escapa un valor segun RFC 6350 (vCard 3.0)."""
    return valor.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")


def vcard(persona, empresa):
    nombre = persona["nombre"].strip()
    apellido = persona.get("apellido", "").strip()
    completo = f"{nombre} {apellido}".strip()

    lineas = [
        "BEGIN:VCARD",
        "VERSION:3.0",
        f"N:{escapar(apellido)};{escapar(nombre)};;;",
        f"FN:{escapar(completo)}",
        f"ORG:{escapar(empresa['nombre'])}",
    ]
    if persona.get("cargo"):
        lineas.append(f"TITLE:{escapar(persona['cargo'])}")
    if persona.get("telefono"):
        lineas.append(f"TEL;TYPE=CELL,VOICE:{persona['telefono']}")
    if persona.get("mail"):
        lineas.append(f"EMAIL;TYPE=WORK,INTERNET:{persona['mail']}")
    lineas.append(f"URL:{empresa['web']}")
    lineas.append("END:VCARD")
    # CRLF: lo exigen iOS y Outlook para importar sin romperse.
    return "\r\n".join(lineas) + "\r\n"


def main():
    carpeta_vcf = RAIZ / "vcf"
    carpeta_vcf.mkdir(exist_ok=True)
    for viejo in carpeta_vcf.glob("*.vcf"):
        viejo.unlink()

    generados = 0
    for area in DATOS["areas"]:
        for persona in area["personas"]:
            completo = f"{persona['nombre']} {persona.get('apellido', '')}".strip()
            persona["slug"] = slug(completo)
            persona["vcf"] = f"vcf/{persona['slug']}.vcf"
            (carpeta_vcf / f"{persona['slug']}.vcf").write_text(
                vcard(persona, DATOS["empresa"]), encoding="utf-8"
            )
            generados += 1

    js = (
        "// GENERADO POR build.py — no editar a mano.\n"
        "// Para cambiar datos: edita contactos.json y corre `python3 build.py`.\n"
        "window.FINE = "
        + json.dumps(DATOS, ensure_ascii=False, indent=2)
        + ";\n"
    )
    (RAIZ / "data.js").write_text(js, encoding="utf-8")
    print(f"OK — {generados} vCards y data.js generados.")


if __name__ == "__main__":
    main()
