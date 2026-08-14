#!/usr/bin/env python3
"""Genera el PDF de tarjetas de presentación listo para imprenta.

Lee las personas de contactos.json y arma una tarjeta por cada una.
Cada tarjeta son dos paginas: frente y dorso.

Diseño: corte diagonal. Lado oscuro con el león y el logotipo, lado claro
con el QR. El dorso invierte los pesos: datos sobre el oscuro, marca sobre
el claro.

    python3 tarjetas.py

Salida: tarjetas/tarjetas-fine.pdf y una por persona.
"""
import json
import pathlib
import re
import unicodedata

import qrcode
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.lib.colors import Color, white
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from svglib.svglib import svg2rlg

RAIZ = pathlib.Path(__file__).parent
DESCARGAS = RAIZ.parent

DATOS = json.loads((RAIZ / "contactos.json").read_text(encoding="utf-8"))
URL = DATOS["empresa"]["url"]
DOMINIO = "THEFINECOMPANY.COM.AR"

# Medida estandar en Argentina, con 3 mm de sangrado por lado.
ANCHO, ALTO = 90 * mm, 50 * mm
SANGRADO = 3 * mm
HOJA = (ANCHO + SANGRADO * 2, ALTO + SANGRADO * 2)

# El corte diagonal, en milimetros medidos desde el borde izquierdo del corte.
DIAG_ARRIBA, DIAG_ABAJO = 58, 66

TINTA = Color(2 / 255, 24 / 255, 31 / 255)
PETROLEO = Color(3 / 255, 56 / 255, 70 / 255)
LIMA = Color(201 / 255, 201 / 255, 73 / 255)
GRIS = Color(120 / 255, 140 / 255, 146 / 255)
GRIS_CLARO = Color(150 / 255, 168 / 255, 173 / 255)

pdfmetrics.registerFont(TTFont("Jost", str(RAIZ / ".fuentes/Jost.ttf")))
pdfmetrics.registerFont(TTFont("Inter", str(RAIZ / ".fuentes/Inter.ttf")))


# --------------------------------------------------------------- utilidades

def slug(texto):
    base = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")


def xy(x_mm, y_mm):
    """Del area de corte a coordenadas de la hoja (que incluye sangrado)."""
    return SANGRADO + x_mm * mm, SANGRADO + y_mm * mm


def ancho_espaciado(texto, fuente, cuerpo, track):
    if not texto:
        return 0
    return sum(pdfmetrics.stringWidth(ch, fuente, cuerpo) + track for ch in texto) - track


def espaciado(c, x, y, texto, fuente, cuerpo, track, color, centrado=False):
    """Texto con tracking manual: reportlab no lo trae de fabrica."""
    c.setFont(fuente, cuerpo)
    c.setFillColor(color)
    ancho = ancho_espaciado(texto, fuente, cuerpo, track)
    cursor = x - ancho / 2 if centrado else x
    for ch in texto:
        c.drawString(cursor, y, ch)
        cursor += pdfmetrics.stringWidth(ch, fuente, cuerpo) + track
    return ancho


def espaciado_ajustado(c, x, y, texto, fuente, cuerpo, track, color, ancho_max):
    """Achica cuerpo y tracking hasta entrar en la columna.

    Los cargos varian mucho de largo y no pueden cruzar la diagonal.
    """
    while ancho_espaciado(texto, fuente, cuerpo, track) > ancho_max and cuerpo > 3.6:
        track = max(track - 0.05, 0.5)
        cuerpo -= 0.1
    espaciado(c, x, y, texto, fuente, cuerpo, track, color)


def telefono_legible(numero):
    """+5491159628940 -> +54 9 11 5962-8940, que es como se lee en voz alta."""
    digitos = re.sub(r"\D", "", numero)
    if digitos.startswith("549") and len(digitos) == 13:
        area, resto = digitos[3:5], digitos[5:]
        return f"+54 9 {area} {resto[:4]}-{resto[4:]}"
    return numero


# ------------------------------------------------------------------ recursos

def mascara(img):
    """Saca el dibujo del PNG, venga como venga el original.

    leon.png trae todo el trazo a 30 % de opacidad (alfa maximo 77): si se usa
    tal cual, sobre el petroleo queda un verde sucio. avatar leon.png en cambio
    es opaco entero, con el dibujo en oscuro sobre blanco.
    """
    alfa = img.getchannel("A")
    maximo = alfa.getextrema()[1]
    if maximo and maximo < 250:
        return alfa.point(lambda v: min(255, int(v * 255 / maximo)))
    gris = img.convert("L")
    return gris.point(lambda v: 255 - v)


def tenir(ruta, color):
    """Recorta el PNG al contenido real y lo pinta de un color plano."""
    img = Image.open(ruta).convert("RGBA")
    caja = img.getbbox()
    if caja:
        img = img.crop(caja)
    rgb = tuple(int(v * 255) for v in (color.red, color.green, color.blue))
    plano = Image.new("RGBA", img.size, rgb + (0,))
    plano.putalpha(mascara(img))
    return ImageReader(plano)


LEON_LIMA = tenir(DESCARGAS / "leon.png", LIMA)
LEON_OSCURO = tenir(DESCARGAS / "avatar leon.png", TINTA)
LOGO = svg2rlg(str(RAIZ / "assets/logo.svg"))


def recolorear(nodo, color):
    """Pinta todo el dibujo vectorial de un color (el SVG viene en blanco)."""
    if hasattr(nodo, "contents"):
        for hijo in nodo.contents:
            recolorear(hijo, color)
    if hasattr(nodo, "fillColor") and nodo.fillColor is not None:
        nodo.fillColor = color
    if hasattr(nodo, "strokeColor") and nodo.strokeColor is not None:
        nodo.strokeColor = color


def logo_en(c, x_centro, y_base, ancho_deseado, color=None):
    if color is not None:
        recolorear(LOGO, color)
    escala = ancho_deseado / LOGO.width
    LOGO.scale(escala, escala)
    LOGO.width *= escala
    LOGO.height *= escala
    renderPDF.draw(LOGO, c, x_centro - LOGO.width / 2, y_base)
    alto = LOGO.height
    LOGO.scale(1 / escala, 1 / escala)
    LOGO.width /= escala
    LOGO.height /= escala
    if color is not None:
        recolorear(LOGO, white)
    return alto


def alto_logo(ancho):
    return ancho * (LOGO.height / LOGO.width)


def leon_en(c, imagen, x_centro, y_centro, alto_deseado):
    ancho_img, alto_img = imagen.getSize()
    ancho = alto_deseado * (ancho_img / alto_img)
    c.drawImage(imagen, x_centro - ancho / 2, y_centro - alto_deseado / 2,
                ancho, alto_deseado, mask="auto")


def qr_imagen(url, escala=30):
    """QR con la mayor correccion de errores para aguantar el logo al centro."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                      box_size=escala, border=0)
    q.add_data(url)
    q.make(fit=True)
    img = q.make_image(fill_color=(2, 24, 31), back_color="white").convert("RGB")

    logo = Image.open(DESCARGAS / "LOGO-FINE-OSCURO.png").convert("RGBA")
    destino = int(img.width * 0.2)
    logo = logo.resize((destino, int(logo.height * (destino / logo.width))), Image.LANCZOS)
    pad = int(destino * 0.14)
    caja = Image.new("RGB", (logo.width + pad * 2, logo.height + pad * 2), "white")
    caja.paste(logo, (pad, pad), logo)
    img.paste(caja, ((img.width - caja.width) // 2, (img.height - caja.height) // 2))
    return ImageReader(img)


QR = qr_imagen(URL)


# ------------------------------------------------------------------- fondos

def borde_diagonal(y_hoja):
    """X de la diagonal a una altura dada, en coordenadas de hoja."""
    t = (y_hoja - SANGRADO) / ALTO           # 0 abajo del corte, 1 arriba
    x_mm = DIAG_ABAJO + (DIAG_ARRIBA - DIAG_ABAJO) * t
    return SANGRADO + x_mm * mm


def poligono_oscuro():
    """El area oscura, extendida hasta el sangrado para que corte limpio."""
    holgura = SANGRADO + 2 * mm
    return [
        (-holgura, -holgura),
        (borde_diagonal(-holgura), -holgura),
        (borde_diagonal(HOJA[1] + holgura), HOJA[1] + holgura),
        (-holgura, HOJA[1] + holgura),
    ]


def fondo(c):
    """Blanco a sangre, area oscura en degradado y filo lima en la diagonal."""
    c.setFillColor(white)
    c.rect(0, 0, HOJA[0], HOJA[1], stroke=0, fill=1)

    puntos = poligono_oscuro()

    c.saveState()
    p = c.beginPath()
    p.moveTo(*puntos[0])
    for punto in puntos[1:]:
        p.lineTo(*punto)
    p.close()
    c.clipPath(p, stroke=0, fill=0)
    # Degradado real de PDF: no banda al imprimir.
    c.linearGradient(0, HOJA[1], HOJA[0] * 0.75, 0, [PETROLEO, TINTA], [0, 1])
    c.restoreState()

    # Filo lima sobre el corte, del ancho de un pelo.
    c.setStrokeColor(LIMA)
    c.setLineWidth(1.1)
    c.line(puntos[1][0], puntos[1][1], puntos[2][0], puntos[2][1])


def marcas(c):
    """Marcas de corte fuera del sangrado."""
    c.setStrokeColor(Color(0.45, 0.45, 0.45))
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


# ------------------------------------------------------------------- caras

def frente(c):
    fondo(c)

    # Lado oscuro: leon arriba y logotipo abajo, ambos al eje de su area.
    eje = xy(27, 0)[0]
    leon_en(c, LEON_LIMA, eje, xy(0, 31)[1], 20 * mm)
    logo_en(c, eje, xy(0, 11)[1], 34 * mm, white)

    # Lado claro: el QR sin recuadro, que el papel ya es blanco.
    lado = 21
    qx, qy = xy(78 - lado / 2, 28 - lado / 2)
    c.drawImage(QR, qx, qy, lado * mm, lado * mm)
    espaciado(c, xy(78, 0)[0], xy(0, 12.5)[1], "ESCANEÁ Y GUARDÁ",
              "Jost", 4.2, 1.1, GRIS, centrado=True)

    marcas(c)
    c.showPage()


def dorso(c, persona):
    fondo(c)

    izq = xy(8, 0)[0]
    # La columna termina antes de la diagonal, con aire de sobra.
    ancho_col = (DIAG_ARRIBA - 8 - 9) * mm

    c.setFont("Inter", 10)
    c.setFillColor(white)
    c.drawString(izq, xy(0, 32)[1], persona["nombre_completo"])

    if persona["cargo"]:
        espaciado_ajustado(c, izq, xy(0, 28)[1], persona["cargo"].upper(),
                           "Jost", 4.8, 1.1, LIMA, ancho_col)

    c.setStrokeColor(LIMA)
    c.setLineWidth(0.7)
    c.line(izq, xy(0, 24.5)[1], izq + 9 * mm, xy(0, 24.5)[1])

    c.setFont("Inter", 6.9)
    c.setFillColor(Color(1, 1, 1, alpha=0.85))
    y = 20.5
    for linea in persona["contacto"]:
        c.drawString(izq, xy(0, y)[1], linea)
        y -= 3.6

    espaciado(c, izq, xy(0, 8)[1], DOMINIO, "Jost", 4.2, 1.1, GRIS_CLARO)

    # Lado claro: la marca, en oscuro sobre el papel.
    # El ancho esta acotado por la diagonal a la izquierda y el corte a la derecha.
    eje = xy(76, 0)[0]
    leon_en(c, LEON_OSCURO, eje, xy(0, 33)[1], 13 * mm)
    logo_en(c, eje, xy(0, 18)[1], 19 * mm, TINTA)

    marcas(c)
    c.showPage()


# -------------------------------------------------------------------- main

def main():
    gente = {}
    for unidad in DATOS["unidades"]:
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

    c = canvas.Canvas(str(salida / "tarjetas-fine.pdf"), pagesize=HOJA)
    c.setTitle("Tarjetas F!NE")
    for persona in gente.values():
        frente(c)
        dorso(c, persona)
    c.save()

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
