#!/usr/bin/env python3
"""Páginas de servicio nuevas, convertidor de medidas y página 404.

- /deslinde-de-propiedad y /desmembracion-de-terrenos: se clonan de
  levantamiento-catastral.html y se les cambia cabecera, schema, textos y preguntas.
- /convertidor-de-medidas: herramienta interactiva sobre la plantilla de las guías.
- /404.html: página de error con la marca y enlaces (Vercel la sirve sola).

Añade las URLs al sitemap y al mapa del sitio. Es idempotente.

    python herramientas/paginas.py
    python herramientas/prerender.py

Reglas del contenido: sin precios, sin clientes inventados, sin citar leyes.
"""
import io, os, re, sys, json, html
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'herramientas'))
import prerender as p

SITE = 'https://martinezseguramultiserviciosni.com'
HOY = '2026-10-13'
V2 = 0.698737
MZ = 10000 * V2
INETER = ('<a href="https://consultacf.ineter.gob.ni/Servicio/ConsultaTopografo" target="_blank" rel="noopener">'
          'portal de Catastro Físico de INETER</a>')
H2 = "font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:22px;color:#2B1F15;margin:0 0 8px;"
LEAD = "font-size:15.5px;color:#6B5844;line-height:1.6;max-width:720px;margin:0 0 20px;"


def rd(f):
    raw = io.open(os.path.join(ROOT, f), encoding='utf-8', newline='').read()
    return p.strip(raw).replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def wr(f, s, nl='\r\n'):
    io.open(os.path.join(ROOT, f), 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))


def esc(s):
    return html.escape(s, quote=True)


def ld(obj):
    return '<script type="application/ld+json">\n%s\n</script>' % json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def sub1(pat, rep, s, flags=re.S):
    out, k = re.subn(pat, (lambda m: rep) if isinstance(rep, str) else rep, s, count=1, flags=flags)
    assert k == 1, pat[:80]
    return out


def lista(items):
    return ('<ul style="display:flex;flex-direction:column;gap:10px;margin:0;padding:0;list-style:none;max-width:820px;">' + ''.join(
        '<li style="display:flex;gap:10px;align-items:flex-start;margin:0;"><span aria-hidden="true" style="flex:none;width:8px;height:8px;border-radius:50%%;'
        'background:#B0512B;margin-top:8px;"></span><span style="font-size:15.5px;color:#34261A;line-height:1.55;">%s</span></li>' % t for t in items) + '</ul>')


def seccion(ident, titulo, cuerpo):
    return '<section aria-labelledby="%s" style="margin-top:44px;"><h2 id="%s" style="%s">%s</h2>%s</section>' % (ident, ident, H2, titulo, cuerpo)


SERVICIOS = [
 dict(slug='deslinde-de-propiedad', nombre='Deslinde de propiedad',
      title='Deslinde de Propiedad en Nicaragua | Medición de Linderos',
      desc='Deslinde de propiedad en Nicaragua: ubicamos tus linderos reales con estación total, colocamos mojones y entregamos el plano. Cotiza por WhatsApp.',
      og='Deslinde de propiedad y medición de linderos',
      h1='Deslinde de propiedad y medición de linderos en Nicaragua',
      hero='Ubicamos en el terreno dónde termina tu propiedad, con estación total y GPS, y lo dejamos marcado en el sitio y en un plano.',
      wa='Hola, quiero cotizar un deslinde de propiedad.',
      intro='El deslinde define en el sitio la línea que separa tu terreno del vecino. Partimos de tu escritura y de los planos que existan, medimos los '
            'puntos reales con estación total y marcamos el lindero para que los dos colindantes vean lo mismo. Lo realiza un topógrafo con licencia '
            'catastral (Lic. Cat. SSL101483), que puedes verificar en el ' + INETER + '.',
      caption='Plano de ejemplo: cada lindero queda con su distancia y su rumbo, y cada vértice con sus coordenadas.',
      incluye=['Revisión de la escritura y de los planos anteriores', 'Medición de linderos con estación total y GPS',
               'Mojones en los vértices, cuando los colindantes están de acuerdo', 'Plano con rumbos, distancias, área y coordenadas'],
      ideal='Para cercar, construir junto al lindero, comprar un terreno o aclarar una duda con el vecino.',
      pasos=[('Documentos y visita', 'Revisamos tu escritura y coordinamos la medición.'),
             ('Medición en sitio', 'Ubicamos los linderos, de preferencia con los colindantes presentes.'),
             ('Plano y mojones', 'Entregamos el plano y dejamos el lindero marcado.')],
      extra=seccion('des-cuando', 'Cuándo conviene un deslinde',
                    '<p style="%s">Un deslinde cuesta mucho menos que mover un muro. Estos son los momentos en que más se nota.</p>' % LEAD +
                    lista(['Antes de levantar un muro o una cerca en el borde del terreno.',
                           'Antes de comprar, para saber que lo que te muestran es lo que dice la escritura.',
                           'Cuando una cerca o un mojón se movió con los años.',
                           'Cuando tú y tu vecino no coinciden sobre dónde pasa la línea.']) +
                    '<p style="font-size:15.5px;color:#4E3D2C;line-height:1.6;margin:18px 0 0;max-width:780px;">Medir no es pelear: un plano con coordenadas les da a los '
                    'dos el mismo dato. Si el desacuerdo sigue, el plano es la evidencia técnica que tu abogado puede presentar.</p>'),
      faqs=[('¿Cuánto cuesta un deslinde de propiedad?',
             'Depende del tamaño del terreno, del número de linderos y de la ubicación. Escríbenos por WhatsApp con la ubicación y te enviamos un presupuesto sin compromiso.'),
            ('¿Tiene que estar presente el vecino?',
             'No es obligatorio para medir, pero sí muy recomendable: si los dos ven la medición, es mucho más fácil llegar a un acuerdo.'),
            ('¿Colocan mojones?',
             'Sí. Cuando las partes están de acuerdo con la línea medida, colocamos mojones en los vértices para que el lindero quede marcado.'),
            ('¿El plano de deslinde sirve en un juicio?',
             'Es evidencia técnica que tu abogado puede presentar. Lo firma un topógrafo con licencia catastral.'),
            ('¿Qué diferencia hay con un levantamiento catastral?',
             'El deslinde ubica y marca el lindero en el terreno. El levantamiento catastral es el plano con el formato que piden los trámites. Muchas veces se hacen juntos.')],
      guias=[('/guia-deslinde-problemas-de-linderos', 'Problemas de linderos'), ('/guia-area-de-escritura-vs-terreno', 'Área de escritura vs. terreno'),
             ('/guia-antes-de-comprar-un-terreno', 'Antes de comprar un terreno')],
      otros=[('/levantamiento-catastral', 'Levantamiento catastral'), ('/desmembracion-de-terrenos', 'Desmembración de terrenos'),
             ('/levantamiento-topografico', 'Levantamiento topográfico'), ('/instalacion-mojones-geodesicos', 'Mojones geodésicos')],
      cta=('¿Necesitas ubicar tus linderos?', 'Mándanos la ubicación y lo que diga tu escritura, y coordinamos la medición.')),

 dict(slug='desmembracion-de-terrenos', nombre='Desmembración de terrenos',
      title='Desmembración y Lotificación de Terrenos en Nicaragua',
      desc='Desmembración y lotificación en Nicaragua: dividimos tu terreno en lotes con plano, área y descripción técnica de cada uno para tu trámite.',
      og='Desmembración y lotificación de terrenos',
      h1='Desmembración y lotificación de terrenos en Nicaragua',
      hero='Dividimos tu propiedad en dos o más lotes, con el plano y la descripción técnica de cada uno, listos para tu notario y catastro.',
      wa='Hola, quiero cotizar una desmembración de terreno.',
      intro='Desmembrar es separar una parte de un terreno para venderla, heredarla o donarla; lotificar es dividirlo en varios lotes con sus accesos. '
            'En los dos casos el trabajo técnico es el mismo: medir el terreno completo, trazar la división y dejar cada lote con su área, sus linderos '
            'y su descripción. Lo firma un topógrafo con licencia catastral (Lic. Cat. SSL101483), que puedes verificar en el ' + INETER + '.',
      caption='Cada lote se entrega como este plano de ejemplo: linderos con rumbo y distancia, y el área en m², varas² y manzanas.',
      incluye=['Levantamiento del terreno completo', 'Diseño de la división: lotes, accesos y áreas',
               'Plano y descripción técnica de cada lote y del resto', 'Marcado de los nuevos linderos en el terreno'],
      ideal='Para herencias, ventas parciales, donaciones a hijos y proyectos de lotificación.',
      pasos=[('Medición completa', 'Levantamos todo el terreno, con lo que tenga adentro.'),
             ('Propuesta de división', 'Dibujamos los lotes y la ajustamos contigo.'),
             ('Planos y marcado', 'Entregamos el plano de cada lote y lo marcamos en sitio.')],
      extra=seccion('desm-antes', 'Qué definir antes de dividir',
                    '<p style="%s">La división se dibuja una vez y se vive con ella muchos años. Conviene tener esto claro antes de medir.</p>' % LEAD +
                    lista(['Cuántos lotes quieres y de qué tamaño aproximado cada uno.',
                           'Por dónde entra cada lote: frente a calle, callejón o servidumbre de paso.',
                           'Qué pasa con lo que ya existe: casas, pozos, cercas y árboles.',
                           'Los requisitos de tu alcaldía sobre frente y área mínima de lote.']) +
                    '<p style="font-size:15.5px;color:#4E3D2C;line-height:1.6;margin:18px 0 0;max-width:780px;">Si la escritura está en varas o manzanas, usa el '
                    '<a href="/convertidor-de-medidas">convertidor de medidas</a> para llevar todo a metros antes de repartir.</p>'),
      faqs=[('¿Cuánto cuesta desmembrar un terreno?',
             'Depende del tamaño del terreno y de cuántos lotes resulten. Escríbenos por WhatsApp con la ubicación y lo que quieres dividir, y te enviamos un presupuesto sin compromiso.'),
            ('¿Qué recibo por cada lote?',
             'Un plano con el área en metros cuadrados, varas cuadradas y manzanas, los rumbos y distancias de cada lindero, las coordenadas y la descripción técnica.'),
            ('¿Pueden marcar los lotes en el terreno?',
             'Sí. Después de aprobar la división, marcamos los vértices de cada lote en el sitio.'),
            ('¿Ustedes hacen la escritura?',
             'La escritura la hace tu notario. Nosotros entregamos el plano y la descripción técnica que necesita, y te acompañamos en la gestión ante catastro.'),
            ('¿Se puede dividir una herencia entre varios hermanos?',
             'Sí. Medimos el terreno completo y calculamos cada parte con el área que acuerden, cuidando que todos los lotes tengan acceso.')],
      guias=[('/guia-varas-manzanas-y-metros', 'Varas, manzanas y metros'), ('/guia-area-de-escritura-vs-terreno', 'Área de escritura vs. terreno'),
             ('/guia-documentos-para-medir-un-terreno', 'Documentos para medir tu terreno')],
      otros=[('/levantamiento-catastral', 'Levantamiento catastral'), ('/deslinde-de-propiedad', 'Deslinde de propiedad'),
             ('/levantamiento-topografico', 'Levantamiento topográfico'), ('/diseno-vialidad', 'Vialidad y movimiento de tierra')],
      cta=('¿Vas a dividir un terreno?', 'Cuéntanos dónde está y en cuántas partes lo quieres dividir.')),
]


def servicio(t, g):
    slug, url = g['slug'], SITE + '/' + g['slug']
    assert len(g['title']) <= 60 and len(g['desc']) <= 160, (slug, len(g['title']), len(g['desc']))
    t = sub1(r'<title>.*?</title>', '<title>%s</title>' % esc(g['title']), t)
    t = sub1(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % esc(g['desc']), t)
    t = t.replace(SITE + '/levantamiento-catastral', url)
    for prop in ('property="og:title"', 'name="twitter:title"'):
        t = sub1(r'<meta %s content="[^"]*">' % prop, '<meta %s content="%s">' % (prop, esc(g['og'])), t)
    for prop in ('property="og:description"', 'name="twitter:description"'):
        t = sub1(r'<meta %s content="[^"]*">' % prop, '<meta %s content="%s">' % (prop, esc(g['desc'])), t)
    schemas = [
        {'@context': 'https://schema.org', '@type': 'Service', 'name': g['nombre'], 'serviceType': g['nombre'],
         'areaServed': {'@type': 'Country', 'name': 'Nicaragua'},
         'provider': {'@type': 'ProfessionalService', '@id': SITE + '/#business', 'name': 'Martínez-Segura Multiservicios',
                      'telephone': '+505 8866 3659', 'url': SITE + '/'},
         'description': g['desc'], 'url': url},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': 1, 'name': 'Inicio', 'item': SITE + '/'},
            {'@type': 'ListItem', 'position': 2, 'name': 'Servicios', 'item': SITE + '/servicios'},
            {'@type': 'ListItem', 'position': 3, 'name': g['nombre'], 'item': url}]},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in g['faqs']]},
    ]
    blocks = list(re.finditer(r'<script type="application/ld\+json">.*?</script>', t, re.S))
    assert len(blocks) == 3      # Service, Breadcrumb, FAQ
    t = t[:blocks[0].start()] + '\n'.join(ld(x) for x in schemas) + t[blocks[2].end():]
    t = sub1(r'(<span aria-current="page"[^>]*>)[^<]*(</span></nav>)', lambda m: m.group(1) + esc(g['nombre']) + m.group(2), t)
    t = sub1(r'(<h1 [^>]*>)[^<]*(</h1>)', lambda m: m.group(1) + esc(g['h1']) + m.group(2), t)
    t = sub1(r'(</h1>\s*<p [^>]*>)[^<]*(</p>)', lambda m: m.group(1) + g['hero'] + m.group(2), t)
    t = t.replace('href="https://wa.me/50588663659"', 'href="https://wa.me/50588663659?text=%s"' % quote(g['wa']))
    t = sub1(r'(<p data-seo-intro[^>]*>).*?(</p>)', lambda m: m.group(1) + g['intro'] + m.group(2), t)
    t = sub1(r'(<figure data-grafico.*?<figcaption[^>]*>)[^<]*(</figcaption>)', lambda m: m.group(1) + g['caption'] + m.group(2), t)
    # "Qué incluye": reuse the first <li> as the pattern
    ul = re.search(r'(>Qué incluye</h2>\s*<ul [^>]*>)(.*?)(</ul>\s*<p [^>]*>)([^<]*)(</p>)', t, re.S)
    li = re.match(r'(<li .*?<span style="font-size:16px;[^"]*">)[^<]*(</span></li>)', ul.group(2), re.S)
    t = t[:ul.start()] + ul.group(1) + ''.join(li.group(1) + esc(x) + li.group(2) for x in g['incluye']) + ul.group(3) + g['ideal'] + ul.group(5) + t[ul.end():]
    # "Cómo trabajamos": three steps
    ol = re.search(r'(>Cómo trabajamos</h2>\s*<ol [^>]*>)(.*?)(</ol>)', t, re.S)
    items = re.findall(r'<li .*?</li>', ol.group(2), re.S)
    assert len(items) == 3
    nuevos = ''
    for it, (a, b) in zip(items, g['pasos']):
        m = re.match(r'(.*?<span><span [^>]*>)[^<]*(</span><span [^>]*>)[^<]*(</span></span></li>)', it, re.S)
        nuevos += m.group(1) + esc(a) + m.group(2) + esc(b) + m.group(3)
    t = t[:ol.start()] + ol.group(1) + nuevos + ol.group(3) + t[ol.end():]
    # extra section + FAQ
    faq_open = re.search(r'  <div style="margin-top:40px;">\n    <h2 [^>]*>Preguntas frecuentes</h2>\n    <div style="display:flex;flex-direction:column;gap:12px;">', t)
    end = t.index('</details></div>', faq_open.end()) + len('</details></div>')
    one = re.search(r'<details class="faq-item".*?</details>', t[faq_open.end():end], re.S).group(0)
    m = re.match(r'(<details [^>]*><summary [^>]*>)[^<]*(<span.*?</span></summary><p [^>]*>)[^<]*(</p></details>)', one, re.S)
    faqs = ''.join(m.group(1) + esc(q) + m.group(2) + esc(a) + m.group(3) for q, a in g['faqs'])
    t = t[:faq_open.start()] + '  ' + g['extra'] + '\n' + faq_open.group(0) + faqs + '</div>' + t[end:]
    # pills
    for label, links in (('Guías relacionadas', g['guias']), ('Otros servicios', g['otros'])):
        blk = re.search(r'(>%s</p>\s*<div [^>]*>)(.*?)(</div>)' % label, t, re.S)
        a = re.match(r'(<a href=")[^"]*("[^>]*>)[^<]*(</a>)', blk.group(2), re.S)
        t = t[:blk.start()] + blk.group(1) + ''.join(a.group(1) + h + a.group(2) + esc(x) + ' →' + a.group(3) for h, x in links) + blk.group(3) + t[blk.end():]
    t = sub1(r'(<section aria-label="Contacto".*?<h2 [^>]*>)[^<]*(</h2>\s*<p [^>]*>)[^<]*(</p>)',
             lambda m: m.group(1) + g['cta'][0] + m.group(2) + g['cta'][1] + m.group(3), t)
    return t


# ---------------------------------------------------------------- convertidor
CONV_JS = r'''<script>
(function(){
  if (window.__msConvWired) return; window.__msConvWired = true;
  var M2 = { m2: 1, v2: 0.698737, mz: 6987.37, ha: 10000 };
  function num(v){
    v = String(v == null ? '' : v).replace(/\s/g, '');
    if (!v) return NaN;
    if (/^\d{1,3}(,\d{3})+(\.\d+)?$/.test(v)) v = v.replace(/,/g, '');   // 1,430 = mil cuatrocientos treinta
    else v = v.replace(',', '.');                                        // 2,5 = dos y medio
    return /^\d*\.?\d+$/.test(v) ? parseFloat(v) : NaN;
  }
  function fmt(x, d){ return x.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d }); }
  function put(key, text){
    var l = document.querySelectorAll('[data-cv="' + key + '"]');
    for (var i = 0; i < l.length; i++) l[i].textContent = text;
  }
  function el(id){ return document.getElementById(id); }
  function render(){
    var v = el('cv-valor'), u = el('cv-unidad');
    if (!v || !u) return;
    var m2 = num(v.value) * (M2[u.value] || 1), ok = isFinite(m2) && m2 >= 0;
    put('m2', ok ? fmt(m2, 2) : '—'); put('v2', ok ? fmt(m2 / M2.v2, 2) : '—');
    put('mz', ok ? fmt(m2 / M2.mz, 4) : '—'); put('ha', ok ? fmt(m2 / M2.ha, 4) : '—');
    var f = num(el('cv-frente').value), g = num(el('cv-fondo').value), lu = el('cv-lado').value;
    var a = f * g * (lu === 'v' ? M2.v2 : 1), ok2 = isFinite(a) && a > 0;
    put('lm2', ok2 ? fmt(a, 2) : '—'); put('lv2', ok2 ? fmt(a / M2.v2, 2) : '—'); put('lmz', ok2 ? fmt(a / M2.mz, 4) : '—');
  }
  function on(e){ if (e.target && e.target.id && e.target.id.indexOf('cv-') === 0) render(); }
  document.addEventListener('input', on, true);
  document.addEventListener('change', on, true);
  // The runtime renders over the parse-time DOM; render once it is in place.
  var ticks = 0, t = setInterval(function(){ render(); if (++ticks > 40) clearInterval(t); }, 80);
})();
</script>'''

CONV_CSS = '''
  .cv-card { background:#FFFDF6; border:1px solid rgba(43,31,21,0.12); border-radius:14px; padding:clamp(20px,3vw,28px); }
  .cv-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; align-items:end; }
  .cv-l { display:block; font-weight:700; font-size:13px; letter-spacing:0.04em; color:#5C4A36; margin:0 0 6px; }
  .cv-f { width:100%; min-height:50px; border:1.5px solid rgba(43,31,21,0.22); border-radius:9px; background:#fff; padding:12px 14px; font:600 17px 'Hanken Grotesk',system-ui,sans-serif; color:#2B1F15; }
  .cv-f:focus-visible { outline:3px solid rgba(47,93,104,0.55); outline-offset:2px; }
  .cv-out { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-top:18px; }
  .cv-o { background:#F4EAD2; border-radius:10px; padding:14px 16px; min-width:0; }
  .cv-o b { display:block; font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:clamp(20px,2.6vw,26px); color:#2B1F15; font-variant-numeric:tabular-nums; overflow-wrap:anywhere; }
  .cv-o span { font-size:13.5px; color:#6B5844; }
'''


def convertidor(t):
    slug, url = 'convertidor-de-medidas', SITE + '/convertidor-de-medidas'
    title = 'Convertidor de Manzanas, Varas y Metros | Nicaragua'
    desc = 'Convierte manzanas, varas cuadradas, metros cuadrados y hectáreas con las equivalencias de Nicaragua, y calcula el área de un lote por frente y fondo.'
    assert len(title) <= 60 and len(desc) <= 160, (len(title), len(desc))
    faqs = [('¿Cuántos metros cuadrados tiene una manzana en Nicaragua?', 'Una manzana tiene 10,000 varas cuadradas, que equivalen a 6,987.37 m².'),
            ('¿Cuánto mide una vara cuadrada?', 'Una vara cuadrada equivale a 0.698737 m². La vara lineal mide 0.8359 m.'),
            ('¿El resultado sirve para un trámite?', 'No. El convertidor solo cambia de unidad la cifra que escribas. Para un trámite se necesita el área medida en campo y un plano firmado por un topógrafo con licencia.')]
    crumbs = [('Inicio', SITE + '/'), ('Guías', SITE + '/guias'), ('Convertidor de medidas', url)]
    schemas = [
        {'@context': 'https://schema.org', '@type': 'WebApplication', 'name': 'Convertidor de medidas de terreno', 'url': url, 'description': desc,
         'applicationCategory': 'UtilitiesApplication', 'operatingSystem': 'Web', 'inLanguage': 'es-NI',
         'offers': {'@type': 'Offer', 'price': '0', 'priceCurrency': 'USD'},
         'provider': {'@type': 'ProfessionalService', '@id': SITE + '/#business', 'name': 'Martínez-Segura Multiservicios', 'url': SITE + '/'}},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': a, 'item': b} for i, (a, b) in enumerate(crumbs)]},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in faqs]},
    ]
    t = sub1(r'<title>.*?</title>', '<title>%s</title>' % esc(title), t)
    t = sub1(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % esc(desc), t)
    t = t.replace(SITE + '/guia-replanteo-de-obra', url)
    for prop in ('property="og:title"', 'name="twitter:title"'):
        t = sub1(r'<meta %s content="[^"]*">' % prop, '<meta %s content="%s">' % (prop, 'Convertidor de manzanas, varas y metros'), t)
    for prop in ('property="og:description"', 'name="twitter:description"'):
        t = sub1(r'<meta %s content="[^"]*">' % prop, '<meta %s content="%s">' % (prop, esc(desc)), t)
    t = sub1(r'<meta property="og:type" content="[^"]*">', '<meta property="og:type" content="website">', t)
    t = t.replace(SITE + '/assets/social/control-de-obras.jpg', SITE + '/assets/social/levantamiento-catastral.jpg')
    t = sub1(r'<meta property="og:image:alt" content="[^"]*">', '<meta property="og:image:alt" content="Convertidor de manzanas, varas y metros">', t)
    blocks = list(re.finditer(r'<script type="application/ld\+json">.*?</script>', t, re.S))
    assert len(blocks) == 3
    t = t[:blocks[0].start()] + '\n'.join(ld(x) for x in schemas) + t[blocks[2].end():]
    t = sub1(r'(<style>)', lambda m: m.group(1) + CONV_CSS, t)
    t = sub1(r'(<span aria-current="page"[^>]*>)[^<]*(</span></nav>)', lambda m: m.group(1) + 'Convertidor de medidas' + m.group(2), t)
    t = sub1(r'>Guía · Obra</p>', '>Herramienta gratuita</p>', t)
    t = sub1(r'(<h1 [^>]*>)[^<]*(</h1>)', lambda m: m.group(1) + 'Convertidor de manzanas, varas y metros' + m.group(2), t)
    t = sub1(r'(</h1>\s*<p [^>]*>)[^<]*(</p>)', lambda m: m.group(1) +
             'Escribe el área como la diga tu escritura o el anuncio, y la verás en las cuatro unidades con las equivalencias que se usan en Nicaragua.' + m.group(2), t)
    t = sub1(r'<p class="g-meta">[^<]*</p>', '', t)
    faq = ''.join('<details class="faq-item" style="background:#FFFDF6;border:1px solid rgba(43,31,21,0.12);border-radius:10px;padding:2px 22px;">'
                  '<summary style="font-family:\'Bricolage Grotesque\',sans-serif;font-weight:700;font-size:16.5px;color:#2B1F15;padding:18px 34px 18px 0;position:relative;min-height:24px;">%s'
                  '<span aria-hidden="true" class="faq-plus" style="position:absolute;right:2px;top:26px;color:#B0512B;font-weight:800;font-size:20px;">+</span></summary>'
                  '<p style="font-size:15.5px;color:#4E3D2C;line-height:1.6;margin:0 0 20px;">%s</p></details>' % (esc(q), esc(a)) for q, a in faqs)
    h2 = "font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:clamp(21px,2.4vw,26px);color:#2B1F15;margin:0 0 14px;"
    cuerpo = ('''<div class="g-wrap" style="padding-top:clamp(30px,4.5vw,48px);">
  <div style="max-width:860px;">
    <section class="cv-card" aria-labelledby="cv-h1">
      <h2 id="cv-h1" style="''' + h2 + '''">Convertir un área</h2>
      <div class="cv-row">
        <div><label class="cv-l" for="cv-valor">Área</label><input class="cv-f" id="cv-valor" inputmode="decimal" autocomplete="off" value="1" aria-describedby="cv-nota"></div>
        <div><label class="cv-l" for="cv-unidad">Unidad</label>
          <select class="cv-f" id="cv-unidad"><option value="mz">Manzanas</option><option value="v2">Varas cuadradas</option><option value="m2">Metros cuadrados</option><option value="ha">Hectáreas</option></select></div>
      </div>
      <div class="cv-out" aria-live="polite">
        <div class="cv-o"><b data-cv="m2">6,987.37</b><span>metros cuadrados</span></div>
        <div class="cv-o"><b data-cv="v2">10,000.00</b><span>varas cuadradas</span></div>
        <div class="cv-o"><b data-cv="mz">1.0000</b><span>manzanas</span></div>
        <div class="cv-o"><b data-cv="ha">0.6987</b><span>hectáreas</span></div>
      </div>
      <p id="cv-nota" style="font-size:13.5px;color:#6B5844;margin:14px 0 0;line-height:1.5;">Puedes escribir 1,430 o 2.5. Equivalencias: 1 vara² = 0.698737 m² · 1 manzana = 10,000 varas² = 6,987.37 m².</p>
    </section>

    <section class="cv-card" aria-labelledby="cv-h2" style="margin-top:20px;">
      <h2 id="cv-h2" style="''' + h2 + '''">Área de un lote por frente y fondo</h2>
      <div class="cv-row">
        <div><label class="cv-l" for="cv-frente">Frente</label><input class="cv-f" id="cv-frente" inputmode="decimal" autocomplete="off" value="10"></div>
        <div><label class="cv-l" for="cv-fondo">Fondo</label><input class="cv-f" id="cv-fondo" inputmode="decimal" autocomplete="off" value="30"></div>
        <div><label class="cv-l" for="cv-lado">Medido en</label>
          <select class="cv-f" id="cv-lado"><option value="v">Varas</option><option value="m">Metros</option></select></div>
      </div>
      <div class="cv-out" aria-live="polite">
        <div class="cv-o"><b data-cv="lm2">209.62</b><span>metros cuadrados</span></div>
        <div class="cv-o"><b data-cv="lv2">300.00</b><span>varas cuadradas</span></div>
        <div class="cv-o"><b data-cv="lmz">0.0300</b><span>manzanas</span></div>
      </div>
      <p style="font-size:13.5px;color:#6B5844;margin:14px 0 0;line-height:1.5;">Vale para lotes rectangulares. Si el terreno tiene otra forma, el área solo sale de medir cada lindero.</p>
    </section>

    <div class="g-note" style="margin-top:26px;font-size:16px;line-height:1.65;"><p style="margin:0;"><strong>El convertidor cambia de unidad, no mide.</strong> El área de una escritura antigua puede no coincidir con la del terreno. Si la cifra importa para comprar, vender o dividir, hay que medir: lee <a href="/guia-area-de-escritura-vs-terreno">por qué tu terreno puede medir otra cosa</a>.</p></div>

    <section style="margin-top:36px;">
      <h2 style="''' + h2 + '''">Equivalencias</h2>
      <div class="g-scroll"><table class="g-table">
        <thead><tr><th>Medida</th><th>Metros cuadrados</th><th>Hectáreas</th></tr></thead>
        <tbody>''' + ''.join('<tr><td>%s</td><td>%s m²</td><td>%s ha</td></tr>' % (a, '{:,.2f}'.format(m), '{:,.4f}'.format(m / 10000)) for a, m in [
            ('500 v²', 500 * V2), ('1,000 v²', 1000 * V2), ('¼ de manzana', MZ / 4), ('½ manzana', MZ / 2), ('1 manzana', MZ), ('5 manzanas', 5 * MZ), ('10 manzanas', 10 * MZ)]) + '''</tbody>
      </table></div>
      <p style="font-size:15.5px;color:#4E3D2C;line-height:1.6;margin:0;">La explicación completa, con ejemplos, está en la guía de <a href="/guia-varas-manzanas-y-metros">varas, manzanas y metros</a>.</p>
    </section>

    <section style="margin-top:36px;">
      <h2 id="preguntas" style="''' + h2 + '''">Preguntas frecuentes</h2>
      <div style="display:flex;flex-direction:column;gap:12px;">''' + faq + '''</div>
    </section>
  </div>
</div>
''' + CONV_JS + '\n')
    a = t.index('<div class="g-wrap" style="padding-top:clamp(30px,4.5vw,48px);">')
    b = t.index('<section aria-label="Contacto"')
    t = t[:a] + cuerpo + t[b:]
    t = sub1(r'(<section aria-label="Contacto".*?<h2 [^>]*>)[^<]*(</h2>\s*<p [^>]*>)[^<]*(</p>)',
             lambda m: m.group(1) + '¿Quieres saber cuánto mide de verdad?' + m.group(2) +
             'Medimos tu terreno y te entregamos el área en metros, varas y manzanas. Respuesta por WhatsApp en menos de 2 horas.' + m.group(3), t)
    return t


# ---------------------------------------------------------------- 404
P404 = '''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Página no encontrada | Martínez-Segura</title>
<meta name="robots" content="noindex">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  * { box-sizing:border-box; }
  html,body { margin:0; min-height:100%; }
  body { font-family:'Hanken Grotesk',system-ui,sans-serif; color:#EAF1F3; background:linear-gradient(160deg,#17333D 0%,#102229 70%,#14303A 100%); display:flex; flex-direction:column; min-height:100vh; -webkit-font-smoothing:antialiased; }
  a { color:inherit; }
  :focus-visible { outline:3px solid #F2A81E; outline-offset:3px; border-radius:4px; }
  .top { padding:20px clamp(16px,5vw,32px); }
  .brand { display:inline-flex; align-items:center; gap:12px; text-decoration:none; }
  .brand b { font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:19px; letter-spacing:.04em; display:block; line-height:1; color:#F7EFDC; }
  .brand span { font-size:10.5px; letter-spacing:.28em; color:#F2A81E; font-weight:700; display:block; margin-top:5px; }
  main { flex:1; display:flex; align-items:center; padding:24px clamp(16px,5vw,32px) 56px; }
  .in { max-width:760px; margin:0 auto; width:100%; }
  .k { font-weight:700; font-size:12px; letter-spacing:.22em; text-transform:uppercase; color:#F2A81E; margin:0; }
  h1 { font-family:'Bricolage Grotesque',sans-serif; font-weight:800; font-size:clamp(30px,5vw,50px); line-height:1.06; color:#F7EFDC; margin:14px 0 0; text-wrap:balance; }
  p.l { font-size:18px; line-height:1.6; color:#C6D5D9; margin:18px 0 0; max-width:560px; }
  .btns { display:flex; flex-wrap:wrap; gap:12px; margin-top:28px; }
  .b { display:inline-flex; align-items:center; justify-content:center; min-height:50px; padding:14px 24px; border-radius:8px; font-weight:700; font-size:15px; text-decoration:none; }
  .b1 { background:#B0512B; color:#FBF2E0; } .b1:hover { background:#8E3F20; }
  .b2 { border:1.5px solid rgba(242,168,30,.55); color:#F2A81E; } .b2:hover { background:rgba(242,168,30,.12); }
  nav.links { margin-top:40px; border-top:1px solid rgba(244,234,210,.14); padding-top:24px; display:grid; grid-template-columns:repeat(auto-fit,minmax(200px,1fr)); gap:6px 24px; }
  nav.links a { color:#C9D6DA; text-decoration:none; padding:8px 0; font-size:15.5px; } nav.links a:hover { color:#F7EFDC; text-decoration:underline; }
</style>
<script src="/assets/js/contacto.js?v=3" defer></script>
</head>
<body>
<div class="top"><a class="brand" href="/" aria-label="Martínez-Segura — Inicio">
  <svg width="38" height="38" viewBox="0 0 64 64" aria-hidden="true"><path d="M32 12 L54 49 C55.4 51.4 54 53 51.4 53 L12.6 53 C10 53 8.6 51.4 10 49 Z" fill="none" stroke="#E0703F" stroke-width="4.5" stroke-linejoin="round"/><circle cx="32" cy="41" r="3.8" fill="#E0703F"/></svg>
  <span style="margin:0;letter-spacing:0;color:inherit;font-weight:inherit;font-size:inherit;"><b>MARTÍNEZ-SEGURA</b><span>TOPOGRAFÍA · NICARAGUA</span></span></a></div>
<main><div class="in">
  <p class="k">Error 404</p>
  <h1>Este punto no está en el plano</h1>
  <p class="l">La página que buscas no existe o cambió de dirección. Desde aquí llegas a lo más buscado.</p>
  <div class="btns">
    <a class="b b1" href="/">Ir al inicio</a>
    <a class="b b2" href="/cotizador">Armar una cotización</a>
    <a class="b b2" href="https://wa.me/50588663659" target="_blank" rel="noopener">Escribir por WhatsApp</a>
  </div>
  <nav class="links" aria-label="Páginas principales">
    <a href="/servicios">Servicios</a>
    <a href="/levantamiento-topografico">Levantamiento topográfico</a>
    <a href="/levantamiento-catastral">Levantamiento catastral</a>
    <a href="/deslinde-de-propiedad">Deslinde de propiedad</a>
    <a href="/control-de-obras">Control de obra</a>
    <a href="/arquitectura">Arquitectura</a>
    <a href="/cobertura">Cobertura por departamento</a>
    <a href="/guias">Guías</a>
    <a href="/convertidor-de-medidas">Convertidor de medidas</a>
    <a href="/contacto">Contacto</a>
  </nav>
</div></main>
</body>
</html>
'''


def main():
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    base, nl = rd('levantamiento-catastral.html')
    for g in SERVICIOS:
        wr(g['slug'] + '.html', servicio(base, g), nl); print('  ' + g['slug'] + '.html')
    guia, gnl = rd('guia-replanteo-de-obra.html')
    wr('convertidor-de-medidas.html', convertidor(guia), gnl); print('  convertidor-de-medidas.html')
    wr('404.html', P404, '\r\n'); print('  404.html')

    nuevas = [g['slug'] for g in SERVICIOS] + ['convertidor-de-medidas']
    sm_raw = io.open(os.path.join(ROOT, 'sitemap.xml'), encoding='utf-8', newline='').read()
    snl = '\r\n' if '\r\n' in sm_raw else '\n'
    sm = sm_raw.replace('\r\n', '\n')
    add = ''.join('  <url><loc>%s/%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.8</priority></url>\n' % (SITE, x, HOY)
                  for x in nuevas if '<loc>%s/%s</loc>' % (SITE, x) not in sm)
    wr('sitemap.xml', sm.replace('</urlset>', add + '</urlset>'), snl)

    s, mnl = rd('mapa-del-sitio.html')
    m = re.search(r'<a href="/levantamiento-catastral"([^>]*)>[^<]*</a>', s)
    etiquetas = {'deslinde-de-propiedad': 'Deslinde de propiedad', 'desmembracion-de-terrenos': 'Desmembración de terrenos', 'convertidor-de-medidas': 'Convertidor de medidas'}
    extra = ''.join('\n<a href="/%s"%s>%s</a>' % (x, m.group(1), etiquetas[x]) for x in nuevas if '/%s"' % x not in s)
    wr('mapa-del-sitio.html', s[:m.end()] + extra + s[m.end():], mnl)
    print('sitemap y mapa del sitio actualizados')


if __name__ == '__main__':
    main()
