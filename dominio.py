#!/usr/bin/env python3
"""Pasa el sitio a un dominio propio, de punta a punta.

    python3 dominio.py contactos.thefinecompany.com.ar

Antes de correrlo tiene que existir el registro DNS, si no GitHub deja de
servir la URL vieja y el sitio queda caido hasta que el DNS resuelva.
El script lo verifica solo y no avanza si falta.

Hace, en orden:
  1. comprueba que el dominio apunte a GitHub Pages
  2. escribe el archivo CNAME (asi lo lee GitHub Pages)
  3. actualiza la URL en contactos.json
  4. regenera los QR y las tarjetas con la direccion nueva
  5. commitea, pushea y configura Pages con HTTPS obligatorio
"""
import json
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).parent
REPO = "yulblumen-hub/contactos-fine"
DESTINO_ESPERADO = "yulblumen-hub.github.io"


def correr(comando, **kw):
    return subprocess.run(comando, cwd=RAIZ, text=True, capture_output=True, **kw)


def dns_listo(dominio, intentos=3):
    """El CNAME tiene que resolver a la pagina de GitHub antes de tocar nada."""
    ultimo = ""
    for _ in range(intentos):
        salida = correr(["dig", "+short", "CNAME", dominio]).stdout.strip()
        if DESTINO_ESPERADO in salida:
            return True, salida
        ultimo = salida or correr(["dig", "+short", dominio]).stdout.strip()
    return False, ultimo or "(no resuelve)"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    dominio = sys.argv[1].strip().lower().rstrip(".")

    ok, visto = dns_listo(dominio)
    if not ok:
        print(f"FRENO: {dominio} todavia no apunta a {DESTINO_ESPERADO}.")
        print(f"       Ahora resuelve a: {visto}")
        print("       Carga el CNAME en Route 53 y volve a correr esto.")
        sys.exit(2)
    print(f"1/5  DNS ok: {dominio} -> {visto}")

    (RAIZ / "CNAME").write_text(dominio + "\n", encoding="utf-8")
    print("2/5  CNAME escrito")

    archivo = RAIZ / "contactos.json"
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    datos["empresa"]["url"] = f"https://{dominio}/"
    archivo.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    print(f"3/5  contactos.json apunta a https://{dominio}/")

    for paso in ("build.py", "qr.py", "tarjetas.py"):
        r = correr([sys.executable, paso])
        if r.returncode:
            print(f"FALLO {paso}:\n{r.stderr}")
            sys.exit(3)
    print("4/5  QR y tarjetas regenerados")

    correr(["git", "add", "-A"])
    correr(["git", "-c", "user.email=customer@thefinecompany.com.ar",
            "-c", "user.name=Yul", "commit", "-q", "-m",
            f"Paso el sitio a {dominio}"])
    push = correr(["git", "push", "-q", "origin", "main"])
    if push.returncode:
        print(f"FALLO el push:\n{push.stderr}")
        sys.exit(4)

    correr(["gh", "api", "-X", "PUT", f"repos/{REPO}/pages",
            "-f", f"cname={dominio}", "-F", "https_enforced=true"])
    print(f"5/5  Listo — https://{dominio}/")
    print("     El certificado HTTPS puede tardar unos minutos en emitirse.")


if __name__ == "__main__":
    main()
