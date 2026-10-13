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

Todas las que usan `support.js` (114). Quedan fuera `tarjeta.html` y la carpeta
`deploy-facturacion/`: son paquetes con su propio runtime, y la facturación es una
herramienta interna marcada `noindex`.

La copia se retira cuando el runtime ya dibujó la página y no queda ningún componente
pendiente (`.sc-placeholder`). En las páginas con el `Header` compartido se captura
el encabezado a 1280 y a 390 px, porque ese componente elige entre menú y hamburguesa
con JavaScript; las páginas con encabezado propio (arquitectura, PARCON) lo resuelven
con CSS y basta una captura.

## Las demás herramientas

Todas trabajan sobre las fuentes (sin los bloques de pre-render) y se pueden correr
varias veces sin duplicar nada. El orden es:

| Paso | Herramienta | Qué hace |
|---|---|---|
| 1 | `graficos.py` + `insertar_graficos.py` | Dibuja los diagramas de `assets/graficos/` y los coloca en las páginas de servicio. |
| 1 | `guias.py` | Crea guías nuevas y la página `/no-minimal`; las añade al hub, al sitemap y al mapa del sitio. |
| 1 | `paginas.py` | Crea páginas de servicio (deslinde, desmembración), el convertidor de medidas y `404.html`. |
| 2 | `enlazar.py` | Enlaza las páginas nuevas, pone "Compartir" en las guías y sube el `?v=` de `contacto.js`. |
| 3 | `prerender.py` | Regenera los snapshots (arriba). |
| 4 | `auditar_seo.py` | Revisa títulos, descripciones, schema, sitemap y enlaces. Solo lee. |
| — | `tarjetas_sociales.py` | Genera las tarjetas 1200×630 de `assets/social/` para Facebook y WhatsApp. |

Reglas que conviene no romper:

- Títulos de 60 caracteres o menos y descripciones de 160 o menos.
- Siempre "Ing. Steven Segura" y "Arq. Orelio Martínez" en el texto visible.
- `mapa-del-sitio.html` no es pública: va con `noindex`, fuera del sitemap y sin enlace en el pie.
- `/assets/` se sirve con caché de un año: al cambiar un archivo ya publicado, cámbiale el nombre o el `?v=`.
