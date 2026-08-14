#!/usr/bin/env python3
"""Genera los QR a partir de la URL que figura en contactos.json.

    python3 qr.py

Salida: qr/qr-contactos-fine.png (con el logo al centro) y
        qr/qr-contactos-fine-simple.png (sin logo, para lectores viejos).
"""
import json
import pathlib

import qrcode
from PIL import Image

RAIZ = pathlib.Path(__file__).parent
TINTA = (2, 24, 31)


def con_logo(url, escala=40):
    """Correccion H: aguanta que le tapen el centro con el logotipo."""
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                      box_size=escala, border=4)
    q.add_data(url)
    q.make(fit=True)
    img = q.make_image(fill_color=TINTA, back_color="white").convert("RGB")

    logo = Image.open(RAIZ.parent / "LOGO-FINE-OSCURO.png").convert("RGBA")
    destino = int(img.width * 0.22)
    logo = logo.resize((destino, int(logo.height * (destino / logo.width))), Image.LANCZOS)
    pad = int(destino * 0.12)
    caja = Image.new("RGB", (logo.width + pad * 2, logo.height + pad * 2), "white")
    caja.paste(logo, (pad, pad), logo)
    img.paste(caja, ((img.width - caja.width) // 2, (img.height - caja.height) // 2))
    return img


def simple(url, escala=40):
    q = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_Q,
                      box_size=escala, border=4)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color=TINTA, back_color="white").convert("RGB")


def main():
    datos = json.loads((RAIZ / "contactos.json").read_text(encoding="utf-8"))
    url = datos["empresa"]["url"]

    salida = RAIZ / "qr"
    salida.mkdir(exist_ok=True)
    con_logo(url).save(salida / "qr-contactos-fine.png")
    simple(url).save(salida / "qr-contactos-fine-simple.png")

    # Verificacion: un QR que no decodifica no sirve de nada.
    try:
        import cv2
        import numpy as np
        det = cv2.QRCodeDetector()
        for archivo in sorted(salida.glob("*.png")):
            img = cv2.imread(str(archivo))
            leido = det.detectAndDecode(img)[0]
            estado = "OK" if leido == url else f"FALLA ({leido or 'no decodifica'})"
            print(f"  {archivo.name}: {estado}")
    except ImportError:
        print("  (sin opencv: no se verifico la lectura)")

    print(f"OK — QR apuntando a {url}")


if __name__ == "__main__":
    main()
