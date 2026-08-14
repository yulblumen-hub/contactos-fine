#!/usr/bin/env python3
"""Arte para los stickers NFC: redondo, para pegar arriba del tag.

El chip NFC no se ve: el sticker es lo que le avisa a la gente que ahi hay
algo que tocar. Lleva el QR chico como respaldo para el que tenga NFC
apagado o un Android viejo.

    python3 etiquetas.py

Salida: etiquetas/sticker-nfc-38mm.pdf (con QR) y sticker-nfc-38mm-limpio.pdf
"""
import json
import math
import pathlib

from reportlab.graphics import renderPDF
from reportlab.lib.colors import Color, white
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfgen import canvas

import qrcode
from reportlab.lib.utils import ImageReader

import tarjetas as T

RAIZ = pathlib.Path(__file__).parent

# QR chico: sin logo y con correccion Q usa menos modulos, asi cada modulo
# queda mas grande y el telefono lo lee sin pelear.
_q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q,
                   box_size=30, border=0)
_q.add_data(T.URL)
_q.make(fit=True)
QR_CHICO = ImageReader(_q.make_image(fill_color=(2, 24, 31),
                                     back_color="white").convert("RGB"))
MODULOS = _q.modules_count

SANGRADO = 2 * mm

# Los dos tamanos son distintos a proposito: el sticker con QR necesita mas
# diametro para que cada modulo del codigo llegue al minimo imprimible.
CON_QR = 45 * mm
SOLO_NFC = 38 * mm

# Estado de la lamina que se esta dibujando, para no arrastrarlo por firma.
HOJA = (0, 0)
CENTRO = (0, 0)
RADIO = 0


def medidas(diametro):
    global HOJA, CENTRO, RADIO
    HOJA = (diametro + SANGRADO * 2, diametro + SANGRADO * 2)
    CENTRO = (HOJA[0] / 2, HOJA[1] / 2)
    RADIO = diametro / 2
    return HOJA


def lado_qr(diametro):
    """El QR mas grande que entra dejando lugar a los dos textos en arco."""
    return diametro - 30 * mm


def texto_en_arco(c, texto, radio, fuente, cuerpo, track, color, arriba=True):
    """Escribe letra por letra siguiendo una circunferencia.

    Arriba se lee de izquierda a derecha yendo en sentido horario (el angulo
    baja); abajo es al reves. Confundir el sentido deja el texto espejado.
    """
    c.setFont(fuente, cuerpo)
    c.setFillColor(color)

    anchos = [pdfmetrics.stringWidth(ch, fuente, cuerpo) + track for ch in texto]
    barrido = (sum(anchos) - track) / radio      # radianes que ocupa el texto
    centro = math.pi / 2 if arriba else -math.pi / 2
    angulo = centro + barrido / 2 if arriba else centro - barrido / 2

    for ch, ancho in zip(texto, anchos):
        paso = ancho / radio
        a = angulo - paso / 2 if arriba else angulo + paso / 2
        c.saveState()
        c.translate(CENTRO[0] + radio * math.cos(a), CENTRO[1] + radio * math.sin(a))
        c.rotate(math.degrees(a) + (-90 if arriba else 90))
        c.drawCentredString(0, -cuerpo * 0.92 if arriba else cuerpo * 0.16, ch)
        c.restoreState()
        angulo += -paso if arriba else paso


def sticker(c, con_qr, diametro):
    medidas(diametro)

    # Fondo circular a sangre.
    c.setFillColor(T.TINTA)
    c.rect(0, 0, HOJA[0], HOJA[1], stroke=0, fill=1)

    c.saveState()
    p = c.beginPath()
    p.circle(CENTRO[0], CENTRO[1], RADIO + SANGRADO)
    c.clipPath(p, stroke=0, fill=0)
    c.linearGradient(0, HOJA[1], HOJA[0], 0, [T.PETROLEO, T.TINTA], [0, 1])
    c.restoreState()

    # Aro lima por dentro del corte.
    c.setStrokeColor(T.LIMA)
    c.setLineWidth(0.9)
    c.circle(CENTRO[0], CENTRO[1], RADIO - 2.2 * mm, stroke=1, fill=0)

    texto_en_arco(c, "ACERCÁ TU CELULAR", RADIO - 4.6 * mm,
                  "Jost", 5.4, 1.5, T.LIMA, arriba=True)
    texto_en_arco(c, "CONTACTOS F!NE", RADIO - 4.6 * mm,
                  "Jost", 4.8, 1.4, T.GRIS_CLARO, arriba=False)

    if con_qr:
        # Sin leon: el QR necesita todo el espacio disponible para leerse bien.
        lado = lado_qr(diametro)
        base = CENTRO[1] - lado / 2
        c.setFillColor(white)
        c.roundRect(CENTRO[0] - lado / 2 - 1.6 * mm, base - 1.6 * mm,
                    lado + 3.2 * mm, lado + 3.2 * mm, 1.4 * mm, stroke=0, fill=1)
        c.drawImage(QR_CHICO, CENTRO[0] - lado / 2, base, lado, lado)
    else:
        T.leon_en(c, T.LEON_LIMA, CENTRO[0], CENTRO[1] + 3.5 * mm, 14 * mm)
        T.logo_en(c, CENTRO[0], CENTRO[1] - 8.5 * mm, 17 * mm, white)

    # Linea de corte, para que la troqueladora sepa donde cortar.
    c.setStrokeColor(Color(0.5, 0.5, 0.5))
    c.setLineWidth(0.25)
    c.setDash(2, 2)
    c.circle(CENTRO[0], CENTRO[1], RADIO, stroke=1, fill=0)
    c.setDash()

    c.showPage()


def main():
    salida = RAIZ / "etiquetas"
    salida.mkdir(exist_ok=True)

    variantes = [
        ("sticker-nfc-con-qr", True, CON_QR),
        ("sticker-nfc", False, SOLO_NFC),
    ]
    for nombre, con_qr, diametro in variantes:
        hoja = medidas(diametro)
        c = canvas.Canvas(str(salida / f"{nombre}.pdf"), pagesize=hoja)
        c.setTitle(f"Sticker NFC F!NE — {nombre}")
        sticker(c, con_qr, diametro)
        c.save()
        print(f"  {nombre}.pdf — {diametro/mm:.0f} mm")

    url = json.loads((RAIZ / "contactos.json").read_text(encoding="utf-8"))["empresa"]["url"]
    modulo_mm = (lado_qr(CON_QR) / mm) / MODULOS
    print(f"OK — stickers en {salida}/")
    print(f"   El QR apunta a {url}")
    print(f"   QR de {lado_qr(CON_QR)/mm:.0f} mm, {MODULOS}x{MODULOS} modulos = "
          f"{modulo_mm:.2f} mm cada uno "
          f"({'ok' if modulo_mm >= 0.45 else 'CHICO: agrandar el sticker'})")


if __name__ == "__main__":
    main()
