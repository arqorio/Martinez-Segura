#!/usr/bin/env python3
"""Auditoría SEO y de enlaces del sitio.

Revisa títulos (<= 60), descripciones (<= 160), canonical, Open Graph, schema,
sitemap, enlaces rotos, páginas poco enlazadas e imágenes. Solo lee; no cambia nada.

    python herramientas/auditar_seo.py

Ojo: mapa-del-sitio.html, tarjeta.html, Header.html y Footer.html quedan fuera del
sitemap a propósito (ver git log de cada uno antes de "arreglarlos").
"""
import io, os, re, sys, glob, json, collections
sys.stdout.reconfigure(encoding='utf-8')
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://martinezseguramultiserviciosni.com'
os.chdir(REPO)
sys.path.insert(0, 'herramientas')
import prerender as p

pages = sorted(f.replace('\\', '/') for f in glob.glob('*.html') + glob.glob('en/*.html')
               if not f.endswith('.dc.html') and not f.startswith('google'))
sm = io.open('sitemap.xml', encoding='utf-8').read()
sm_urls = set(re.findall(r'<loc>([^<]+)</loc>', sm))


def url_of(f):
    f = f[:-5]
    if f == 'index': return SITE + '/'
    if f == 'en/index': return SITE + '/en'
    return SITE + '/' + f


info = {}
for f in pages:
    s = io.open(f, encoding='utf-8').read()
    head = s[:s.find('</head>')] if '</head>' in s else s
    src = p.strip(s)
    d = {}
    full = s
    t = re.search(r'<title>(.*?)</title>', full, re.S)
    d['title'] = t.group(1).strip() if t else ''
    m = re.search(r'<meta name="description" content="([^"]*)"', full)
    d['desc'] = m.group(1) if m else ''
    m = re.search(r'<link rel="canonical" href="([^"]*)"', full)
    d['canon'] = m.group(1) if m else ''
    m = re.search(r'<meta name="robots" content="([^"]*)"', full)
    d['robots'] = m.group(1) if m else ''
    d['og_image'] = bool(re.search(r'property="og:image"', full))
    d['og_title'] = bool(re.search(r'property="og:title"', full))
    d['og_desc'] = bool(re.search(r'property="og:description"', full))
    d['og_url'] = bool(re.search(r'property="og:url"', full))
    d['og_type'] = bool(re.search(r'property="og:type"', full))
    d['og_site'] = bool(re.search(r'property="og:site_name"', full))
    d['tw'] = bool(re.search(r'name="twitter:card"', full))
    d['h1'] = len(re.findall(r'<h1[\s>]', src))
    d['ld'] = re.findall(r'"@type":\s*"([A-Za-z]+)"', ' '.join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', src, re.S)))
    d['links'] = set(re.findall(r'<a [^>]*href="(/[^"#?]*)', src))
    d['imgs'] = re.findall(r'<img\b[^>]*>', src)
    d['xdc'] = '<x-dc' in src
    d['pre'] = 'ms-pre:inicio' in s
    d['head_has_title'] = '<title' in head
    d['lang'] = (re.search(r'<html lang="([^"]*)"', s) or [None, ''])[1]
    info[f] = d

print('páginas:', len(pages), ' en sitemap:', len(sm_urls))
idx = [f for f in pages if 'noindex' not in info[f]['robots']]
# sitemap coverage
missing = [f for f in idx if url_of(f) not in sm_urls and info[f]['canon'] in ('', url_of(f))]
print('\nINDEXABLES FUERA DEL SITEMAP:', missing)
extra = [u for u in sm_urls if not any(url_of(f) == u for f in pages)]
print('EN SITEMAP SIN ARCHIVO:', extra)
noidx_in = [f for f in pages if 'noindex' in info[f]['robots'] and url_of(f) in sm_urls]
print('NOINDEX DENTRO DEL SITEMAP:', noidx_in)
print('CANONICAL != URL:', [(f, info[f]['canon']) for f in idx if info[f]['canon'] and info[f]['canon'] != url_of(f)])
print('SIN CANONICAL:', [f for f in idx if not info[f]['canon']])

# titles / descriptions
def dup(key):
    c = collections.defaultdict(list)
    for f in idx: c[info[f][key]].append(f)
    return {k: v for k, v in c.items() if len(v) > 1}
print('\nTÍTULOS DUPLICADOS:', {k: v for k, v in dup('title').items()})
dd = dup('desc')
print('DESCRIPCIONES DUPLICADAS: %d grupos' % len(dd))
for k, v in list(dd.items())[:8]: print('   ', len(v), v[:4], '|', k[:70])
print('TÍTULO >60:', [(f, len(info[f]['title'])) for f in idx if len(info[f]['title']) > 62])
print('TÍTULO <25:', [(f, info[f]['title']) for f in idx if len(info[f]['title']) < 25])
print('DESC >165:', [(f, len(info[f]['desc'])) for f in idx if len(info[f]['desc']) > 165])
print('DESC <70:', [(f, len(info[f]['desc'])) for f in idx if len(info[f]['desc']) < 70])
print('H1 != 1:', [(f, info[f]['h1']) for f in idx if info[f]['h1'] != 1])
print('SIN PRE-RENDER (con x-dc):', [f for f in idx if info[f]['xdc'] and not info[f]['pre']])
print('SIN x-dc:', [f for f in idx if not info[f]['xdc']])
print('TITLE NO EN HEAD:', [f for f in idx if not info[f]['head_has_title']])

# social
for k in ('og_image', 'og_title', 'og_desc', 'og_url', 'og_type', 'og_site', 'tw'):
    miss = [f for f in idx if not info[f][k]]
    print('SIN %s: %d %s' % (k, len(miss), miss[:6]))

# schema
c = collections.Counter()
for f in idx:
    for t in set(info[f]['ld']): c[t] += 1
print('\nSCHEMA TYPES:', dict(c))
print('SIN SCHEMA:', [f for f in idx if not info[f]['ld']])

# links
exist = set()
for f in pages:
    exist.add('/' + f[:-5]); exist.add('/' + f)
exist |= {'/', '/en', '/en/'}
broken = collections.defaultdict(list)
inbound = collections.Counter()
for f in pages:
    for l in info[f]['links']:
        l2 = l.rstrip('/') or '/'
        if l2.startswith('/assets') or l2.startswith('/deploy-facturacion') or l2.startswith('/facturacion'):
            if l2.startswith('/assets') and not os.path.exists(l2[1:]): broken[l].append(f)
            continue
        if l2 not in exist: broken[l].append(f)
        else: inbound[l2] += 1
print('\nENLACES ROTOS:', {k: v[:3] for k, v in broken.items()})
# inbound counts exclude shared Header/Footer (they are dc-imports, not in src)
orph = [f for f in idx if inbound['/' + f[:-5]] == 0 and f not in ('index.html',)]
print('SIN ENLACES ENTRANTES DESDE EL CUERPO (%d):' % len(orph), orph)
low = sorted(((inbound['/' + f[:-5]], f) for f in idx))[:25]
print('MENOS ENLAZADAS:', low)

# images
noalt = collections.Counter(); nodim = collections.Counter(); nolazy = collections.Counter()
big = []
for f in idx:
    for im in info[f]['imgs']:
        if not re.search(r'\balt="[^"]', im): noalt[f] += 1
        if 'width=' not in im or 'height=' not in im: nodim[f] += 1
seen = set()
for f in idx:
    for im in info[f]['imgs']:
        m = re.search(r'src="(/?assets/[^"]+)"', im)
        if m and m.group(1) not in seen:
            seen.add(m.group(1)); pth = m.group(1).lstrip('/')
            if os.path.exists(pth) and os.path.getsize(pth) > 250000: big.append((os.path.getsize(pth) // 1024, pth))
print('\nIMG SIN ALT:', dict(noalt.most_common(8)))
print('IMG SIN DIMENSIONES:', dict(nodim.most_common(8)), 'total', sum(nodim.values()))
print('IMÁGENES >250 KB:', sorted(big, reverse=True)[:15])
print('LANG:', collections.Counter(info[f]['lang'] for f in pages))
