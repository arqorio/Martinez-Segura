# Herramientas

Estos archivos no se publican en el sitio (están en `.vercelignore`).

## prerender.py — HTML pre-renderizado

Cada página del sitio la dibuja `support.js` en el navegador. Hasta que arranca,
el visitante no ve nada, y los buscadores o asistentes que no ejecutan JavaScript
(Bing, vistas previas de WhatsApp/Facebook, asistentes de IA) ven la plantilla sin
título en `<head>` y sin los enlaces del menú.

El script abre cada página en Chrome/Edge sin ventana, guarda lo que se dibujó y lo
incrusta en la misma página. El resultado:

- La página se ve al instante, antes de que cargue React, y funciona aunque el
  JavaScript falle.
- Título, descripción, canonical, `hreflang`, JSON-LD y fuentes quedan en `<head>`.
- Cuando el runtime termina de dibujar, la copia se quita en el mismo cuadro,
  sin salto visual.

La plantilla `<x-dc>` nunca se toca: el sitio se comporta igual que antes.

### Normalmente no tienes que hacer nada

La acción de GitHub `.github/workflows/prerender.yml` lo ejecuta sola cada vez que
subes archivos a `main`, y guarda el resultado con un commit "Pre-render automático".
Vercel publica ese commit como siempre.

### A mano

```
python herramientas/prerender.py              # todas las páginas
python herramientas/prerender.py index.html   # solo algunas
python herramientas/prerender.py --comprobar  # avisa si algo está desactualizado
python herramientas/prerender.py --limpiar    # quita todo lo generado
```

Necesita Chrome o Edge instalado (o la variable `MS_BROWSER` con su ruta).
Solo usa la biblioteca estándar de Python.

### Qué páginas procesa

Las que usan `support.js` con los componentes `Header` y `Footer`. Por ahora quedan
fuera `arquitectura.html`, `arquitectura-fotos.html`, las páginas de PARCON
(`construccion-*`, `parajon-construcciones`), `tarjeta.html` y la facturación:
tienen encabezado propio o animaciones que conviene revisar aparte.
