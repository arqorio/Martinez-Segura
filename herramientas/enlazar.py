#!/usr/bin/env python3
"""Enlaza las páginas nuevas con el resto del sitio y añade "Compartir" a las guías.

Trabaja sobre las fuentes (sin bloques de pre-render) y es idempotente.

    python herramientas/enlazar.py
"""
import io, os, re, sys, glob, json, html
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'herramientas'))
import prerender as p

SITE = 'https://martinezseguramultiserviciosni.com'
os.chdir(ROOT)


def rd(f):
    raw = io.open(f, encoding='utf-8', newline='').read()
    return p.strip(raw).replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def wr(f, s, nl):
    io.open(f, 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))


WA = ('<svg width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 00-8.6 15L2 22l5.1-1.3A10 10 0 1012 2zm5.8 14.2c-.2.7-1.4 1.3-2 1.4-.5.1-1.2.1-1.9-.1-.4-.1-1-.3-1.7-.6-3-1.3-4.9-4.3-5-4.5'
      '-.1-.2-1.2-1.6-1.2-3s.7-2.1 1-2.4c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 1.9c.1.1.1.3 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.5.1.3.7 1.1 1.4 1.8 1 .8 1.7 1.1 2 1.2.2.1.4.1.5-.1l.6-.8c.2-.2.4-.2.6-.1'
      'l1.8.9c.3.1.4.2.5.3.1.2.1.6-.1 1.2z"></path></svg>')
FB = ('<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M13.5 22v-8.2h2.8l.4-3.2h-3.2V8.5c0-.9.3-1.6 1.6-1.6h1.7V4.1c-.3 0-1.3-.1-2.5-.1-2.5 0-4.2 1.5-4.2 4.3v2.3H7.3v3.2h2.8V22h3.4z"></path></svg>')


def compartir(titulo, slug):
    """Share row for a guide. wa.me without a number is not intercepted by contacto.js."""
    url = SITE + '/' + slug
    btn = ('display:inline-flex;align-items:center;gap:8px;text-decoration:none;border-radius:999px;padding:10px 18px;'
           'font-weight:700;font-size:14.5px;min-height:44px;')
    return ('  <div data-compartir style="margin-top:clamp(28px,4vw,40px);display:flex;flex-wrap:wrap;align-items:center;gap:12px;">\n'
            '    <span style="font-weight:700;font-size:12px;letter-spacing:0.18em;text-transform:uppercase;color:#7A664A;">¿Te sirvió? Compártela</span>\n'
            '    <a href="https://wa.me/?text=%s" target="_blank" rel="noopener" style="%sbackground:#25D366;color:#08301C;" style-hover="background:#1FBF5B;">%sWhatsApp</a>\n'
            '    <a href="https://www.facebook.com/sharer/sharer.php?u=%s" target="_blank" rel="noopener" style="%sbackground:#FFFDF6;color:#2B1F15;border:1px solid rgba(43,31,21,0.2);" '
            'style-hover="border-color:#B0512B;color:#B0512B;">%sFacebook</a>\n'
            '  </div>\n' % (quote(titulo + ' ' + url), btn, WA, quote(url, safe=''), btn, FB))


def guias():
    n = 0
    for f in sorted(glob.glob('guia-*.html')):
        s, nl = rd(f)
        if 'data-compartir' in s: continue
        titulo = html.unescape(re.search(r'<h1 [^>]*>(.*?)</h1>', s, re.S).group(1))
        ancla = '  <section aria-label="Más guías"'
        assert s.count(ancla) == 1, f
        wr(f, s.replace(ancla, compartir(titulo, f[:-5]) + ancla), nl); n += 1
    print('guías con Compartir:', n)


def tarjeta(base, href, titulo, texto):
    c = re.sub(r'href="/levantamiento-catastral"', 'href="%s"' % href, base, count=1)
    c = re.sub(r'(<h3 [^>]*>)[^<]*(</h3>)', lambda m: m.group(1) + titulo + m.group(2), c, count=1)
    c = re.sub(r'(</h3>\s*<p [^>]*>)[^<]*(</p>)', lambda m: m.group(1) + texto + m.group(2), c, count=1)
    return c


NUEVOS = [('/deslinde-de-propiedad', 'Deslinde de propiedad', 'Ubicamos tus linderos reales en el terreno, con mojones y plano, para cercar, comprar o aclarar una duda con el vecino.'),
          ('/desmembracion-de-terrenos', 'Desmembración y lotificación', 'Dividimos tu terreno en lotes, con el plano y la descripción técnica de cada uno para tu trámite.')]


def servicios():
    s, nl = rd('servicios.html')
    if '/deslinde-de-propiedad' in s: return
    base = re.search(r'<a href="/levantamiento-catastral"[^>]*>.*?</a>', s, re.S).group(0)
    topo = re.search(r'<a href="/levantamiento-topografico"[^>]*>.*?</a>', s, re.S)
    nuevas = ''.join('\n      ' + tarjeta(base, h, t, d) for h, t, d in NUEVOS)
    s = s[:topo.end()] + nuevas + s[topo.end():]
    # renumber the big corner numbers in order of appearance
    k = [0]
    def num(m):
        k[0] += 1
        return m.group(1) + '%02d' % k[0] + m.group(2)
    s = re.sub(r'(<span style="position:absolute;top:18px;right:24px;[^"]*">)\d\d(</span>)', num, s)
    wr('servicios.html', s, nl); print('servicios.html: tarjetas', k[0])


def portada():
    s, nl = rd('index.html')
    if '/deslinde-de-propiedad' not in s:
        base = re.search(r'<a href="/levantamiento-catastral"[^>]*>.*?</a>', s, re.S)
        h, t, d = NUEVOS[0]
        s = s[:base.end()] + '\n      ' + tarjeta(base.group(0), h, t, 'Ubicamos tus linderos reales en el terreno, con mojones y plano.') + s[base.end():]
    # opening hours in the business node (same hours as the contact page)
    m = re.search(r'<script type="application/ld\+json">\s*(\{[^<]*?"@id":\s*"%s/#business".*?)\s*</script>' % re.escape(SITE), s, re.S)
    d = json.loads(m.group(1))
    if 'openingHoursSpecification' not in d:
        d['openingHoursSpecification'] = [
            {'@type': 'OpeningHoursSpecification', 'dayOfWeek': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], 'opens': '07:00', 'closes': '18:00'},
            {'@type': 'OpeningHoursSpecification', 'dayOfWeek': 'Saturday', 'opens': '08:00', 'closes': '13:00'}]
        s = s[:m.start(1)] + json.dumps(d, ensure_ascii=False, separators=(',', ':')) + s[m.end(1):]
    wr('index.html', s, nl); print('index.html: tarjeta de deslinde y horario en el schema')


def pastillas(f, etiqueta, nuevos, al_inicio=True):
    s, nl = rd(f)
    blk = re.search(r'(>%s</p>\s*<div [^>]*>)(.*?)(</div>)' % etiqueta, s, re.S)
    a = re.match(r'(<a href=")[^"]*("[^>]*>)[^<]*(</a>)', blk.group(2), re.S)
    add = ''.join(a.group(1) + h + a.group(2) + t + ' →' + a.group(3) for h, t in nuevos if 'href="%s"' % h not in s)
    if not add: return
    cuerpo = add + blk.group(2) if al_inicio else blk.group(2) + add
    wr(f, s[:blk.start()] + blk.group(1) + cuerpo + blk.group(3) + s[blk.end():], nl); print(f, '+', etiqueta)


def footer():
    f = 'Footer.dc.html'
    raw = io.open(f, encoding='utf-8', newline='').read()
    if '/convertidor-de-medidas' in raw: return
    m = re.search(r'(\s*)<a href="/guias"([^>]*)>Guías</a>', raw)
    raw = raw[:m.end()] + m.group(1) + '<a href="/convertidor-de-medidas"%s>Convertidor de medidas</a>' % m.group(2) + raw[m.end():]
    io.open(f, 'w', encoding='utf-8', newline='').write(raw); print('Footer: convertidor')


def hub():
    s, nl = rd('guias.html')
    if '/convertidor-de-medidas' in s: return
    card = ('<a class="g-card" href="/convertidor-de-medidas"><span class="g-tag">Herramienta</span><h2>Convertidor de manzanas, varas y metros</h2>'
            '<p>Escribe el área como la diga tu escritura y la verás en metros cuadrados, varas cuadradas, manzanas y hectáreas.</p></a>')
    last = s.rindex('</a>', 0, s.index('¿No encuentras tu pregunta?'))
    wr('guias.html', s[:last + 4] + card + s[last + 4:], nl); print('guias.html: tarjeta del convertidor')


def version_script():
    n = 0
    for f in glob.glob('*.html') + glob.glob('en/*.html') + ['herramientas/guias.py']:
        raw = io.open(f, encoding='utf-8', newline='').read()
        if 'contacto.js?v=2' in raw:
            io.open(f, 'w', encoding='utf-8', newline='').write(raw.replace('contacto.js?v=2', 'contacto.js?v=3')); n += 1
    print('contacto.js?v=3 en', n)


def main():
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    guias(); servicios(); portada(); footer(); hub()
    pastillas('levantamiento-catastral.html', 'Otros servicios', [('/deslinde-de-propiedad', 'Deslinde de propiedad'), ('/desmembracion-de-terrenos', 'Desmembración de terrenos')])
    pastillas('levantamiento-topografico.html', 'Otros servicios', [('/deslinde-de-propiedad', 'Deslinde de propiedad'), ('/desmembracion-de-terrenos', 'Desmembración de terrenos')])
    pastillas('levantamiento-topografico.html', 'Guías relacionadas', [('/guia-como-leer-un-plano-topografico', 'Cómo leer un plano topográfico'), ('/convertidor-de-medidas', 'Convertidor de medidas')], al_inicio=False)
    pastillas('levantamiento-catastral.html', 'Guías relacionadas', [('/guia-area-de-escritura-vs-terreno', 'Área de escritura vs. terreno'), ('/convertidor-de-medidas', 'Convertidor de medidas')], al_inicio=False)
    version_script()


if __name__ == '__main__':
    main()
