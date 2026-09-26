#!/usr/bin/env python3
"""Pre-render the site's pages into static HTML.

Why: every page is rendered in the browser by support.js (the x-dc runtime).
Until React boots, a visitor sees nothing, and crawlers that do not run
JavaScript (Bing, social previews, AI assistants) see raw template text with
no <title>/description in <head> and no header or footer links.

What it does, per page:
  1. Loads the page in headless Chrome/Edge (desktop and mobile width) and
     captures what the runtime rendered into #dc-root.
  2. Writes that snapshot into the page as <div id="ms-pre">, placed just
     before <x-dc>. It is visible immediately, and stays if JavaScript never
     runs, so the page works without JS.
  3. Copies the page's <helmet> tags (title, meta, canonical, JSON-LD, page
     CSS) into <head>, so they are there before any script runs.
  4. Adds a tiny script: once the runtime has rendered the real page
     (header and footer present), it removes the snapshot and any <head>
     copy that the runtime has duplicated, in the same frame.

Safety: the <x-dc> template is never modified — the runtime behaves exactly
as before. Every run first strips previous output, so it is idempotent.
`--limpiar` removes everything this tool added.

Usage (from the repo root):
    python herramientas/prerender.py              # all eligible pages
    python herramientas/prerender.py index.html   # only some pages
    python herramientas/prerender.py --limpiar    # undo everything
    python herramientas/prerender.py --comprobar  # fail if output is stale

Browser: set MS_BROWSER to a Chrome/Edge executable, or let the script find
one. Standard library only (runs on the stock GitHub Actions runner).
"""
import argparse, concurrent.futures, functools, glob, html.parser, http.server, io, os
import re, shutil, socket, subprocess, sys, tempfile, threading

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESKTOP = (1280, 1000)
MOBILE = (390, 844)          # the Header switches to its mobile layout below 1010px
EXCLUDE = re.compile(r'(^|/)(Header|Footer)\.html$|\.dc\.html$|^deploy-facturacion/|^tarjeta\.html$|^herramientas/')

# Markers — everything between them is generated and safe to replace.
HEAD_A, HEAD_B = '<!--ms-head:inicio-->', '<!--ms-head:fin-->'
PRE_A, PRE_B = '<!--ms-pre:inicio-->', '<!--ms-pre:fin-->'

BASE_CSS = ('x-dc{display:none!important}'
            '@media (min-width:1010px){.ms-hd-m{display:none!important}}'
            '@media (max-width:1009px){.ms-hd-d{display:none!important}}'
            'html.ms-pre-on #dc-root{position:absolute!important;left:0;right:0;top:0;'
            'visibility:hidden!important;pointer-events:none!important}')

SWAP_JS = r'''<script>(function(){
var de=document.documentElement;de.classList.add('ms-pre-on');
function ready(){var r=document.getElementById('dc-root');return r&&r.querySelector('header')&&r.querySelector('footer');}
function norm(el){var c=el.cloneNode(true);for(var i=c.attributes.length-1;i>=0;i--){if(/^data-/.test(c.attributes[i].name))c.removeAttribute(c.attributes[i].name);}return c.outerHTML;}
function swap(){if(done)return;done=true;if(mo)mo.disconnect();
var p=document.getElementById('ms-pre');if(p)p.parentNode.removeChild(p);de.classList.remove('ms-pre-on');
var twins={},kids=document.head.children,i;for(i=0;i<kids.length;i++){if(!kids[i].hasAttribute('data-ms-head'))twins[norm(kids[i])]=1;}
var mine=document.head.querySelectorAll('[data-ms-head]');for(i=0;i<mine.length;i++){if(twins[norm(mine[i])])mine[i].parentNode.removeChild(mine[i]);}}
var done=false,mo=null;
if(window.MutationObserver){mo=new MutationObserver(function(){if(ready())swap();});mo.observe(document,{childList:true,subtree:true});}
setTimeout(function(){if(document.getElementById('dc-root'))swap();},6000);
})();</script>'''

VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param',
        'source', 'track', 'wbr'}


# ------------------------------------------------------------------ strip / restore
def strip(src):
    """Remove everything a previous run added, returning the pristine source."""
    for a, b in ((HEAD_A, HEAD_B), (PRE_A, PRE_B)):
        while a in src:
            i = src.index(a)
            j = src.index(b, i) + len(b)
            # also swallow one line break we added after the block
            if src[j:j + 2] == '\r\n': j += 2
            elif src[j:j + 1] == '\n': j += 1
            src = src[:i] + src[j:]
    return src


def xdc_block(src):
    i = src.find('<x-dc')
    j = src.rfind('</x-dc>')
    return src[i:j + len('</x-dc>')] if i > -1 and j > i else None


def eligible(rel, src):
    if EXCLUDE.search(rel):
        return False
    return ('support.js' in src and '<x-dc' in src
            and 'dc-import name="Header"' in src and 'dc-import name="Footer"' in src)


# ------------------------------------------------------------------ local server
class Handler(http.server.SimpleHTTPRequestHandler):
    """Serves the repo, but always the *pristine* version of .html files."""
    def log_message(self, *a):
        pass

    def send_head(self):
        path = self.translate_path(self.path)
        if path.endswith('.html') and os.path.isfile(path):
            data = strip(io.open(path, encoding='utf-8', newline='').read()).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return io.BytesIO(data)
        return super().send_head()


def serve():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); port = s.getsockname()[1]; s.close()
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', port), functools.partial(Handler, directory=ROOT))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port


# ------------------------------------------------------------------ browser
def find_browser():
    env = os.environ.get('MS_BROWSER')
    if env:
        return shutil.which(env) or env
    for name in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'microsoft-edge'):
        p = shutil.which(name)
        if p:
            return p
    for p in (r'C:\Program Files\Google\Chrome\Application\chrome.exe',
              r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
              os.path.expandvars(r'%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe'),
              r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe',
              r'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
              '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'):
        if os.path.isfile(p):
            return p
    sys.exit('No encontré Chrome ni Edge. Define MS_BROWSER con la ruta del ejecutable.')


def dump(browser, url, size, profile, budget=12000):
    args = [browser, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check',
            '--disable-extensions', '--hide-scrollbars', '--mute-audio', '--disable-sync',
            '--user-data-dir=' + profile, '--window-size=%d,%d' % size,
            '--force-prefers-reduced-motion',      # counters at final value, nothing left mid-animation
            '--virtual-time-budget=%d' % budget, '--dump-dom', url]
    if sys.platform.startswith('linux'):
        args.insert(1, '--no-sandbox')
    if os.name != 'nt':
        r = subprocess.run(args, capture_output=True, timeout=120)
        return r.stdout.decode('utf-8', 'replace')
    # Windows: Chrome/Edge only write --dump-dom when the parent owns a real
    # console, which Python under Git Bash does not. PowerShell does; tell it
    # to read the output as UTF-8 and hand it back through a file.
    out = os.path.join(profile, 'dump.html')
    q = lambda s: "'" + s.replace("'", "''") + "'"
    script = ('[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); '
              '$o = & %s %s | Out-String -Width 2147483647; '
              '[IO.File]::WriteAllText(%s, $o, [Text.UTF8Encoding]::new($false))'
              % (q(args[0]), ' '.join(q(x) for x in args[1:]), q(out)))
    subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script],
                   capture_output=True, timeout=180)
    try:
        with io.open(out, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''
    finally:
        try: os.remove(out)
        except OSError: pass


# ------------------------------------------------------------------ extraction
class ElementRange(html.parser.HTMLParser):
    """Finds the [start, end) character range of the element with a given id."""
    def __init__(self, text, elem_id):
        super().__init__(convert_charrefs=False)
        self.text, self.id = text, elem_id
        self.lines = [0]
        for m in re.finditer('\n', text):
            self.lines.append(m.end())
        self.stack, self.start, self.end, self.inner = [], None, None, None

    def off(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        if self.end is not None or tag in VOID:
            return
        if self.start is None and dict(attrs).get('id') == self.id:
            self.start = self.off()
            self.inner = self.off() + len(self.get_starttag_text())
            self.stack = [tag]
        elif self.start is not None:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if self.start is None or self.end is not None:
            return
        while self.stack:
            top = self.stack.pop()
            if top == tag:
                break
        if not self.stack:
            self.end = self.off()


def inner_of(text, elem_id):
    p = ElementRange(text, elem_id)
    p.feed(text)
    if p.inner is None or p.end is None:
        return None
    return text[p.inner:p.end]


def clean_snapshot(s):
    s = re.sub(r'<script\b[^>]*>.*?</script>', '', s, flags=re.S | re.I)   # never re-run page scripts
    s = re.sub(r'\sdata-dc-tpl="[^"]*"', '', s)
    return s


def tag_header(header_html, cls):
    m = re.match(r'<header\b([^>]*)>', header_html)
    attrs = m.group(1)
    if re.search(r'\sclass="', attrs):
        attrs = re.sub(r'\sclass="([^"]*)"', lambda k: ' class="%s %s"' % (k.group(1), cls), attrs, count=1)
    else:
        attrs = ' class="%s"' % cls + attrs
    return '<header' + attrs + '>' + header_html[m.end():]


def build_snapshot(desk_dom, mob_dom):
    body = inner_of(desk_dom, 'dc-root')
    mob = inner_of(mob_dom, 'dc-root')
    if not body or not mob:
        return None, 'el runtime no renderizó #dc-root'
    body, mob = clean_snapshot(body), clean_snapshot(mob)
    hd = re.search(r'<header\b.*?</header>', body, re.S)
    hm = re.search(r'<header\b.*?</header>', mob, re.S)
    if not hd or not hm or '<footer' not in body:
        return None, 'faltan el header o el footer (¿no cargaron los componentes?)'
    both = tag_header(hd.group(0), 'ms-hd-d') + tag_header(hm.group(0), 'ms-hd-m')
    body = body[:hd.start()] + both + body[hd.end():]
    return body, None


def helmet_copy(src):
    m = re.search(r'<helmet>(.*?)</helmet>', src, re.S)
    if not m:
        return ''
    out = []
    # top-level elements of the helmet, each marked so the swap can find it
    for el in re.finditer(r'<(title|style|script|noscript)\b[^>]*>.*?</\1>|<(meta|link)\b[^>]*>', m.group(1), re.S | re.I):
        tag = el.group(0)
        if re.match(r'<meta\s+charset', tag, re.I):
            continue                          # we emit our own, first in <head>
        out.append(re.sub(r'^<(\w+)', r'<\1 data-ms-head', tag, count=1))
    return '\n'.join(out)


def render_page(src, snapshot, nl):
    head_block = (HEAD_A + nl + '<meta charset="utf-8">' + nl + '<style data-ms-head-keep>' + BASE_CSS + '</style>'
                  + nl + helmet_copy(src) + nl + HEAD_B + nl)
    pre_block = (PRE_A + nl + '<div id="ms-pre">' + snapshot + '</div>' + nl + SWAP_JS + nl + PRE_B + nl)
    i = src.index('<head>') + len('<head>')
    src = src[:i] + nl + head_block + src[i:].lstrip('\r\n')
    i = src.index('<x-dc')
    return src[:i] + pre_block + src[i:]


# ------------------------------------------------------------------ main
def pages(selected):
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'en', '*.html'))):
        rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
        if selected and rel not in selected:
            continue
        src = strip(io.open(path, encoding='utf-8', newline='').read())
        if eligible(rel, src):
            out.append(rel)
    return out


def process(rel, browser, port, profile_root, write):
    path = os.path.join(ROOT, rel)
    raw = io.open(path, encoding='utf-8', newline='').read()
    nl = '\r\n' if '\r\n' in raw else '\n'
    src = strip(raw)
    url = 'http://127.0.0.1:%d/%s' % (port, rel)
    profile = tempfile.mkdtemp(prefix='ms-pre-', dir=profile_root)
    snap, err = None, None
    # Under load a headless render can come back empty or before the Header and
    # Footer components arrive; retry with more time before giving up.
    for budget in (12000, 20000, 30000):
        snap, err = build_snapshot(dump(browser, url, DESKTOP, profile, budget),
                                   dump(browser, url, MOBILE, profile, budget))
        if snap:
            break
    if not snap:
        # never leave a stale snapshot behind: fall back to the plain page
        if write and raw != src:
            io.open(path, 'w', encoding='utf-8', newline='').write(src)
        return rel, 'OMITIDA', err, raw != src
    out = render_page(src, snap.replace('\r\n', '\n').replace('\n', nl), nl)
    # safety checks: the runtime template must be untouched, and the result must be sane
    if xdc_block(out) != xdc_block(src):
        return rel, 'ERROR', 'la plantilla <x-dc> cambió', False
    for need in ('<title', 'rel="canonical"', '<header class="ms-hd-d', '<footer'):
        if need not in out:
            return rel, 'ERROR', 'falta %s' % need, False
    if '{{' in snap:
        return rel, 'ERROR', 'quedaron {{ }} sin resolver', False
    changed = out != raw
    if write and changed:
        io.open(path, 'w', encoding='utf-8', newline='').write(out)
    return rel, 'OK', '%d KB de snapshot' % (len(snap) // 1024), changed


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('paginas', nargs='*', help='rutas relativas; por defecto todas')
    ap.add_argument('--limpiar', action='store_true', help='quitar todo lo generado')
    ap.add_argument('--comprobar', action='store_true', help='no escribir; salir con error si algo cambiaría')
    # Each Windows render goes through PowerShell, which is heavier; keep it lower there.
    ap.add_argument('--hilos', type=int, default=3 if os.name == 'nt' else 4)
    a = ap.parse_args()
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    if a.limpiar:
        n = 0
        for path in glob.glob(os.path.join(ROOT, '*.html')) + glob.glob(os.path.join(ROOT, 'en', '*.html')):
            raw = io.open(path, encoding='utf-8', newline='').read()
            clean = strip(raw)
            if clean != raw:
                io.open(path, 'w', encoding='utf-8', newline='').write(clean); n += 1
        print('limpias: %d páginas' % n)
        return

    todo = pages(set(a.paginas))
    if not todo:
        sys.exit('No hay páginas elegibles.')
    browser = find_browser()
    httpd, port = serve()
    profile_root = tempfile.mkdtemp(prefix='ms-prerender-')
    print('navegador: %s\npáginas: %d\n' % (browser, len(todo)))
    results = []
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=a.hilos) as ex:
            futs = [ex.submit(process, rel, browser, port, profile_root, not a.comprobar) for rel in todo]
            for f in concurrent.futures.as_completed(futs):
                rel, status, info, changed = f.result()
                results.append((rel, status, changed))
                print('  %-8s %-58s %s%s' % (status, rel, info, '  (cambió)' if changed else ''))
    finally:
        httpd.shutdown()
        shutil.rmtree(profile_root, ignore_errors=True)

    bad = [r for r in results if r[1] == 'ERROR']
    skipped = [r for r in results if r[1] == 'OMITIDA']
    changed = [r for r in results if r[2]]
    print('\nlistas: %d  omitidas: %d  errores: %d  con cambios: %d'
          % (len(results) - len(bad) - len(skipped), len(skipped), len(bad), len(changed)))
    if bad:
        sys.exit(1)
    if a.comprobar and changed:
        sys.exit('Hay páginas desactualizadas: ejecuta herramientas/prerender.py')


if __name__ == '__main__':
    main()
