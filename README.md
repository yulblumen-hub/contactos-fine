# Contactos · The F!NE Company

Página pública de contactos por área. Se comparte con un QR, un link o un sticker NFC:
todo apunta a la misma URL.

Una sola web con dos unidades de negocio en solapas:

- **F!NE** — laboratorio y producción de suplementos.
- **F!NE CORE** — el sistema de gestión integral que ofrecemos a otras empresas.

Se puede linkear directo a una: `.../#lab` o `.../#core`.

## Cómo cambiar los datos

Todo sale de un solo archivo: **`contactos.json`**.

1. Editá `contactos.json` (nombre, cargo, mail, teléfono, WhatsApp de cada persona).
2. Corré el generador:

   ```bash
   python3 build.py
   ```

3. Subí los cambios:

   ```bash
   git add -A && git commit -m "actualizo contactos" && git push
   ```

En un minuto la web queda actualizada. El QR y los stickers NFC **no hay que
rehacerlos nunca**: apuntan a la URL, no a los datos.

## Formato de los teléfonos

Poné el número completo con código de país, sin espacios ni signos:

```
"telefono": "+5491122334455"
"whatsapp": "5491122334455"
```

Si dejás un campo vacío, el botón correspondiente no aparece — no se rompe nada.

## Qué genera `build.py`

- `data.js` — los datos que lee la web.
- `vcf/*.vcf` — un archivo de contacto por persona, el que se descarga con
  "Guardar contacto" y entra directo a la agenda del celular.

Ninguno de esos dos se edita a mano.

## Pasar a un dominio propio

1. Cargar en el DNS del dominio (está en **AWS Route 53**):

   ```
   Tipo: CNAME   Nombre: contactos   Valor: yulblumen-hub.github.io   TTL: 300
   ```

2. Cuando resuelva, correr:

   ```bash
   python3 dominio.py contactos.thefinecompany.com.ar
   ```

Eso escribe el `CNAME`, actualiza la URL, **regenera los QR y las tarjetas**,
publica y activa HTTPS. Si el DNS todavía no está, el script frena y no toca
nada: es importante, porque configurar el dominio antes de tiempo deja el
sitio caído.

## Otros generadores

- `python3 qr.py` — regenera los QR sueltos (`qr/`).
- `python3 tarjetas.py` — regenera las tarjetas de presentación (`tarjetas/`).

Los dos leen la URL de `contactos.json`, así que nunca quedan desfasados.

## Ver la web en local

```bash
python3 -m http.server 4323
```

Y abrir http://localhost:4323
