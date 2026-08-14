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


def ancho_espaciado(texto, fuente, cuerpo, track):
    if not texto:
        return 0
    return sum(pdfmetrics.stringWidth(ch, fuente, cuerpo) + track for ch in texto) - track


def espaciado_ajustado(c, x, y, texto, fuente, cuerpo, track, color, ancho_max):
    """Achica cuerpo y tracking hasta que el texto entre en la columna.

    Los cargos varian mucho de largo y no puede pisar el QR.
    """
    while ancho_espaciado(texto, fuente, cuerpo, track) > ancho_max and cuerpo > 3.6:
        track = max(track - 0.05, 0.5)
        cuerpo -= 0.1
    espaciado(c, x, y, texto, fuente, cuerpo, track, color)


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
    """Fondo a sangre. Degradado real de PDF: no banda al imprimir."""
    medio = Color(
        (TINTA.red + PETROLEO.red) / 2,
        (TINTA.green + PETROLEO.green) / 2,
        (TINTA.blue + PETROLEO.blue) / 2,
    )
    c.saveState()
    p = c.beginPath()
    p.rect(0, 0, HOJA[0], HOJA[1])
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(0, HOJA[1], 0, 0, [PETROLEO, medio, TINTA], [0, 0.45, 1])
    c.restoreState()


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


def xy(x_mm, y_mm):
    """Convierte coordenadas del area de corte a coordenadas de la hoja."""
    return SANGRADO + x_mm * mm, SANGRADO + y_mm * mm


def frente(c):
    """Solo el logotipo. La cara limpia es la que se recuerda."""
    fondo(c)
    x, y = xy(45, 25)
    alto = 40 * mm * (LOGO.height / LOGO.width)
    logo_en(c, x, y - alto / 2, 40 * mm)
    marcas(c)
    c.showPage()


def dorso(c, persona):
    fondo(c)

    MARGEN = 7        # aire hasta el corte
    LADO_QR = 22      # el QR y su recuadro blanco
    AIRE_QR = 2

    # --- QR, alineado a la derecha y centrado en vertical ---
    qx, qy = xy(90 - MARGEN - LADO_QR, 25 - LADO_QR / 2 + 1.5)
    c.setFillColor(white)
    c.roundRect(qx - AIRE_QR * mm, qy - AIRE_QR * mm,
                (LADO_QR + AIRE_QR * 2) * mm, (LADO_QR + AIRE_QR * 2) * mm,
                1.6 * mm, stroke=0, fill=1)
    c.drawImage(QR, qx, qy, LADO_QR * mm, LADO_QR * mm)

    cx_qr = qx + LADO_QR * mm / 2
    espaciado(c, cx_qr, xy(0, 8.5)[1], "ESCANEÁ Y GUARDÁ",
              "Jost", 4.3, 1.15, GRIS, centrado=True)

    # --- Columna de datos ---
    izq = xy(MARGEN, 0)[0]

    c.setFont("Inter", 10)
    c.setFillColor(white)
    c.drawString(izq, xy(0, 32.5)[1], persona["nombre_completo"])

    # La columna termina donde arranca el recuadro blanco del QR.
    ancho_col = (90 - MARGEN - LADO_QR - AIRE_QR - 3 - MARGEN) * mm

    if persona["cargo"]:
        espaciado_ajustado(c, izq, xy(0, 28.5)[1], persona["cargo"].upper(),
                           "Jost", 4.8, 1.1, LIMA, ancho_col)

    c.setStrokeColor(Color(1, 1, 1, alpha=0.18))
    c.setLineWidth(0.4)
    c.line(izq, xy(0, 25)[1], izq + 14 * mm, xy(0, 25)[1])

    c.setFont("Inter", 7)
    c.setFillColor(Color(1, 1, 1, alpha=0.82))
    y = 21
    for linea in persona["contacto"]:
        c.drawString(izq, xy(0, y)[1], linea)
        y -= 3.6

    espaciado(c, izq, xy(0, 8.5)[1], "THEFINECOMPANY.COM.AR",
              "Jost", 4.3, 1.15, GRIS)

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
                contacto = []
                if persona.get("telefono"):
                    contacto.append(telefono_legible(persona["telefono"]))
                if persona.get("mail"):
                    contacto.append(persona["mail"])
                gente[completo] = {
                    "nombre_completo": completo,
                    "cargo": persona.get("cargo", ""),
                    "contacto": contacto,
                    "slug": slug(completo),
                }

    salida = RAIZ / "tarjetas"
    salida.mkdir(exist_ok=True)

    # Un PDF con todas, para mandar de una a la imprenta.
    c = canvas.Canvas(str(salida / "tarjetas-fine.pdf"), pagesize=HOJA)
    c.setTitle("Tarjetas F!NE")
    for persona in gente.values():
        frente(c)
        dorso(c, persona)
    c.save()

    # Y una por persona, por si se imprimen en tandas distintas.
    for persona in gente.values():
        uno = canvas.Canvas(str(salida / f"tarjeta-{persona['slug']}.pdf"), pagesize=HOJA)
        uno.setTitle(f"Tarjeta {persona['nombre_completo']}")
        frente(uno)
        dorso(uno, persona)
        uno.save()

    print(f"OK — {len(gente)} tarjetas en {salida}/")
    print(f"   {ANCHO/mm:.0f}x{ALTO/mm:.0f} mm + {SANGRADO/mm:.0f} mm de sangrado")


if __name__ == "__main__":
    main()
