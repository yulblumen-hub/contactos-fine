#!/usr/bin/env python3
"""Genera el PDF de tarjetas de presentación listo para imprenta.

Lee las personas de contactos.json y arma una tarjeta por cada una, mas una
generica de la empresa. Cada tarjeta ocupa dos paginas: frente y dorso.

    python3 tarjetas.py

Salida: tarjetas/tarjetas-fine.pdf
"""
import json
import pathlib
import re
import unicodedata

import qrcode
from PIL import Image
from reportlab.lib.colors import Color, white
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF

RAIZ = pathlib.Path(__file__).parent
URL = "https://yulblumen-hub.github.io/contactos-fine/"

# Medida estandar en Argentina, con 3 mm de sangrado por lado.
ANCHO, ALTO = 90 * mm, 50 * mm
SANGRADO = 3 * mm
HOJA = (ANCHO + SANGRADO * 2, ALTO + SANGRADO * 2)

TINTA = Color(2 / 255, 24 / 255, 31 / 255)
PETROLEO = Color(2 / 255, 50 / 255, 63 / 255)
LIMA = Color(201 / 255, 201 / 255, 73 / 255)
GRIS = Color(143 / 255, 168 / 255, 174 / 255)

pdfmetrics.registerFont(TTFont("Jost", str(RAIZ / ".fuentes/Jost.ttf")))
pdfmetrics.registerFont(TTFont("Inter", str(RAIZ / ".fuentes/Inter.ttf")))


def slug(texto):
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def espaciado(c, x, y, texto, fuente, cuerpo, track, color, centrado=False):
    """Dibuja texto con tracking manual: reportlab no lo trae de fabrica."""
    c.setFont(fuente, cuerpo)
    c.setFillColor(color)
    ancho = sum(pdfmetrics.stringWidth(ch, fuente, cuerpo) + track for ch in texto) - track
    cursor = x - ancho / 2 if centrado else x
    for ch in texto:
        c.drawString(cursor, y, ch)
        cursor += pdfmetrics.stringWidth(ch, fuente, cuerpo) + track
    return ancho


def qr_imagen(url, escala=30):
    """QR con la mayor correccion de errores para aguantar el logo al centro."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                      box_size=escala, border=0)
    q.add_data(url)
    q.make(fit=True)
    img = q.make_image(fill_color=(2, 24, 31), back_color="white").convert("RGB")

    logo = Image.open(RAIZ.parent / "LOGO-FINE-OSCURO.png").convert("RGBA")
    destino = int(img.width * 0.2)
    logo = logo.resize((destino, int(logo.height * (destino / logo.width))), Image.LANCZOS)
    pad = int(destino * 0.14)
    caja = Image.new("RGB", (logo.width + pad * 2, logo.height + pad * 2), "white")
    caja.paste(logo, (pad, pad), logo)
    img.paste(caja, ((img.width - caja.width) // 2, (img.height - caja.height) // 2))
    return ImageReader(img)


QR = qr_imagen(URL)
LOGO = svg2rlg(str(RAIZ / "assets/logo.svg"))


def fondo(c):
    """Fondo a sangre, con un halo suave arriba como en la web."""
    c.setFillColor(TINTA)
    c.rect(0, 0, HOJA[0], HOJA[1], stroke=0, fill=1)
    pasos = 60
    for i in range(pasos):
        t = i / pasos
        c.setFillColor(Color(
            TINTA.red + (PETROLEO.red - TINTA.red) * (1 - t) * 0.55,
            TINTA.green + (PETROLEO.green - TINTA.green) * (1 - t) * 0.55,
            TINTA.blue + (PETROLEO.blue - TINTA.blue) * (1 - t) * 0.55,
        ))
        alto = HOJA[1] * 0.5
        c.rect(0, HOJA[1] - alto * (i + 1) / pasos, HOJA[0], alto / pasos + 0.6,
               stroke=0, fill=1)


def marcas(c):
    """Marcas de corte fuera del sangrado."""
    c.setStrokeColor(Color(1, 1, 1, alpha=0.55))
    c.setLineWidth(0.25)
    largo = 2 * mm
    for x in (SANGRADO, SANGRADO + ANCHO):
        for y in (0, HOJA[1]):
            signo = 1 if y == 0 else -1
            c.line(x, y, x, y + largo * signo)
    for y in (SANGRADO, SANGRADO + ALTO):
        for x in (0, HOJA[0]):
            signo = 1 if x == 0 else -1
            c.line(x, y, x + largo * signo, y)


def logo_en(c, x_centro, y_base, ancho_deseado):
    escala = ancho_deseado / LOGO.width
    LOGO.scale(escala, escala)
    LOGO.width *= escala
    LOGO.height *= escala
    renderPDF.draw(LOGO, c, x_centro - LOGO.width / 2, y_base)
    alto = LOGO.height
    # Se restaura para que el siguiente dibujo parta del tamano original.
    LOGO.scale(1 / escala, 1 / escala)
    LOGO.width /= escala
    LOGO.height /= escala
    return alto


def telefono_legible(numero):
    """+5491159628940 -> +54 9 11 5962-8940, que es como se lee en voz alta."""
    digitos = re.sub(r"\D", "", numero)
    if digitos.startswith("549") and len(digitos) == 13:
        area, resto = digitos[3:5], digitos[5:]
        return f"+54 9 {area} {resto[:4]}-{resto[4:]}"
    return numero


def frente(c, titular):
    fondo(c)
    cx = HOJA[0] / 2
    cy = HOJA[1] / 2

    # El bloque se centra a ojo: logo al medio, rotulo arriba y dominio abajo.
    alto_logo = 42 * mm * (LOGO.height / LOGO.width)
    base_logo = cy - alto_logo / 2 + 1 * mm

    espaciado(c, cx, base_logo + alto_logo + 6 * mm,
              titular.upper(), "Jost", 5.2, 2.1, LIMA, centrado=True)
    logo_en(c, cx, base_logo, 42 * mm)
    espaciado(c, cx, base_logo - 7 * mm,
              "THEFINECOMPANY.COM.AR", "Jost", 5, 1.5, GRIS, centrado=True)

    marcas(c)
    c.showPage()


def dorso(c, persona):
    fondo(c)
    izq = SANGRADO + 7 * mm
    lado = 25 * mm
    qx = SANGRADO + ANCHO - 7 * mm - lado
    qy = (HOJA[1] - lado) / 2

    # Fondo blanco con aire: el QR necesita contraste y zona muda.
    c.setFillColor(white)
    c.roundRect(qx - 2 * mm, qy - 2 * mm, lado + 4 * mm, lado + 4 * mm,
                2 * mm, stroke=0, fill=1)
    c.drawImage(QR, qx, qy, lado, lado)

    espaciado(c, izq, HOJA[1] - 15 * mm, "ESCANEÁ Y GUARDÁ", "Jost", 4.6, 1.4, LIMA)

    c.setFont("Inter", 10.5)
    c.setFillColor(white)
    c.drawString(izq, HOJA[1] - 22 * mm, persona["nombre_completo"])

    c.setFont("Inter", 6.6)
    c.setFillColor(GRIS)
    y = HOJA[1] - 26.5 * mm
    for linea in persona["lineas"]:
        c.drawString(izq, y, linea)
        y -= 3.4 * mm

    c.setStrokeColor(Color(1, 1, 1, alpha=0.16))
    c.setLineWidth(0.4)
    c.line(izq, 13 * mm, izq + 30 * mm, 13 * mm)

    espaciado(c, izq, 9 * mm, "TODOS LOS CONTACTOS DE F!NE", "Jost", 4.4, 1.2, GRIS)

    marcas(c)
    c.showPage()


def main():
    datos = json.loads((RAIZ / "contactos.json").read_text(encoding="utf-8"))

    gente = {}
    for unidad in datos["unidades"]:
        for area in unidad["areas"]:
            for persona in area["personas"]:
                completo = f"{persona['nombre']} {persona.get('apellido', '')}".strip()
                if completo in gente:
                    continue
                lineas = [persona["cargo"]] if persona.get("cargo") else []
                if persona.get("telefono"):
                    lineas.append(telefono_legible(persona["telefono"]))
                if persona.get("mail"):
                    lineas.append(persona["mail"])
                gente[completo] = {
                    "nombre_completo": completo,
                    "lineas": lineas,
                    "slug": slug(completo),
                }

    salida = RAIZ / "tarjetas"
    salida.mkdir(exist_ok=True)

    titular = "LABORATORIO · PRODUCCIÓN · CORE"

    # Un PDF con todas, para mandar de una a la imprenta.
    c = canvas.Canvas(str(salida / "tarjetas-fine.pdf"), pagesize=HOJA)
    c.setTitle("Tarjetas F!NE")
    for persona in gente.values():
        frente(c, titular)
        dorso(c, persona)
    c.save()

    # Y una por persona, por si se imprimen en tandas distintas.
    for persona in gente.values():
        uno = canvas.Canvas(str(salida / f"tarjeta-{persona['slug']}.pdf"), pagesize=HOJA)
        uno.setTitle(f"Tarjeta {persona['nombre_completo']}")
        frente(uno, titular)
        dorso(uno, persona)
        uno.save()

    print(f"OK — {len(gente)} tarjetas en {salida}/")
    print(f"   {ANCHO/mm:.0f}x{ALTO/mm:.0f} mm + {SANGRADO/mm:.0f} mm de sangrado")


if __name__ == "__main__":
    main()
