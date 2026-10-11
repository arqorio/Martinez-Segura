#!/usr/bin/env python3
"""Tarjetas 1200x630 para Facebook, WhatsApp, Instagram y X (og:image).

Una por servicio, con su diagrama, más una general con la foto de campo.
Dibuja cada tarjeta en HTML, la captura con Chrome/Edge sin ventana y la guarda
como JPG en assets/social/.

    python herramientas/tarjetas_sociales.py            # todas
    python herramientas/tarjetas_sociales.py control    # solo las que contengan "control"

Si cambias una tarjeta ya publicada, cámbiale el nombre al archivo: /assets/ se
sirve con caché de un año y Facebook guarda su propia copia por URL.
"""
import io, os, subprocess, sys, tempfile, shutil
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'herramientas'))
import prerender as p

OUT = os.path.join(ROOT, 'assets', 'social')

# nombre -> (rótulo, título, bajada, imagen relativa a la raíz, 'svg' | 'foto')
CARDS = {
    'general': ('Topografía · Ingeniería · Arquitectura', 'Medimos tu terreno. Entregamos planos con validez catastral.',
                'Nicaragua · 12 departamentos · Lic. catastral SSL101483', 'assets/portfolio/03-estacion-total-leica.jpeg', 'foto'),
    'levantamiento-topografico': ('Servicio', 'Levantamiento topográfico', 'Curvas de nivel, planimetría y plano con estación total y GPS',
                                  'assets/graficos/levantamiento-topografico.svg', 'svg'),
    'levantamiento-catastral': ('Servicio', 'Levantamiento catastral', 'Deslinde, linderos y plano con validez ante catastro',
                                'assets/graficos/levantamiento-catastral.svg', 'svg'),
    'control-de-obras': ('Servicio', 'Control topográfico de obra', 'Replanteo de ejes, niveles, plomo y volúmenes en cada etapa',
                         'assets/graficos/control-de-obras.svg', 'svg'),
    'diseno-vialidad': ('Servicio', 'Vialidad y movimiento de tierra', 'Calles, accesos y parqueos con volúmenes de corte y relleno',
                        'assets/graficos/diseno-vialidad.svg', 'svg'),
    'costos-presupuestos': ('Servicio', 'Costos y presupuestos', 'Presupuesto por partidas y cronograma antes de construir',
                            'assets/graficos/costos-presupuestos.svg', 'svg'),
    'diseno-arquitectonico': ('Servicio', 'Diseño arquitectónico y estructural', 'Casas, remodelaciones y oficinas, con planos para el permiso',
                              'assets/graficos/diseno-arquitectonico.svg', 'svg'),
    'mojones-geodesicos': ('Servicio', 'Mojones geodésicos', 'Puntos de control georreferenciados con GNSS',
                           'assets/graficos/mojones-geodesicos.svg', 'svg'),
    'modelado-bim': ('Servicio', 'Modelado BIM', 'Modelo 3D coordinado, interferencias y cantidades',
                     'assets/graficos/modelado-bim.svg', 'svg'),
    'soldadura': ('Servicio', 'Soldadura y estructuras metálicas', 'Fabricación y montaje en sitio',
                  'assets/graficos/soldadura.svg', 'svg'),
    'guias': ('Guías', 'Guías de topografía para terrenos y obras', 'Precios, linderos, documentos, control de obra y replanteo',
              'assets/graficos/levantamiento-catastral.svg', 'svg'),
}

HTML = '''<!doctype html><html lang="es"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Hanken+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0}
html,body{width:1200px;height:630px;overflow:hidden}
body{background:linear-gradient(155deg,#17333D 0%%,#102229 68%%,#14303A 100%%);color:#F7EFDC;font-family:'Hanken Grotesk',sans-serif;position:relative}
.grid{position:absolute;inset:0;background-image:linear-gradient(rgba(244,234,210,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(244,234,210,.05) 1px,transparent 1px);background-size:48px 48px}
.wrap{position:absolute;inset:0;display:grid;grid-template-columns:%(cols)s;gap:44px;padding:56px 60px;align-items:center}
.brand{display:flex;align-items:center;gap:14px}
.brand svg{width:46px;height:46px}
.brand b{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:25px;letter-spacing:.04em;display:block;line-height:1}
.brand span{font-size:12.5px;letter-spacing:.3em;color:#F2A81E;font-weight:700;display:block;margin-top:6px}
.k{margin-top:46px;font-weight:700;font-size:16px;letter-spacing:.24em;text-transform:uppercase;color:#F2A81E}
h1{font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:%(size)spx;line-height:1.04;letter-spacing:-.018em;margin-top:14px;text-wrap:balance}
.s{font-size:24px;line-height:1.38;color:#C6D5D9;margin-top:20px;max-width:520px}
.u{margin-top:34px;font-size:19px;font-weight:600;color:#9FB2B7}
.pic{background:#FFFDF6;border-radius:18px;overflow:hidden;box-shadow:0 24px 60px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;height:%(pich)s}
.pic img{display:block;%(imgcss)s}
</style></head><body><div class="grid"></div><div class="wrap">
<div>
  <div class="brand"><svg viewBox="0 0 64 64"><path d="M32 12 L54 49 C55.4 51.4 54 53 51.4 53 L12.6 53 C10 53 8.6 51.4 10 49 Z" fill="none" stroke="#E0703F" stroke-width="4.5" stroke-linejoin="round"/><circle cx="32" cy="41" r="3.8" fill="#E0703F"/></svg>
  <div><b>MARTÍNEZ-SEGURA</b><span>TOPOGRAFÍA · NICARAGUA</span></div></div>
  <p class="k">%(k)s</p>
  <h1>%(t)s</h1>
  <p class="s">%(s)s</p>
  <p class="u">martinezseguramultiserviciosni.com</p>
</div>
<div class="pic"><img src="%(img)s" alt=""></div>
</div></body></html>'''


def shot(browser, url, png, profile):
    args = [browser, '--headless=new', '--disable-gpu', '--no-first-run', '--no-default-browser-check', '--disable-extensions',
            '--hide-scrollbars', '--user-data-dir=' + profile, '--window-size=1200,630', '--force-device-scale-factor=1',
            '--virtual-time-budget=8000', '--screenshot=' + png, url]
    if sys.platform.startswith('linux'):
        args.insert(1, '--no-sandbox')
    if os.name != 'nt':
        subprocess.run(args, capture_output=True, timeout=120)
    else:
        # Same quirk as prerender.dump(): under Git Bash the browser only produces output when PowerShell owns the console.
        q = lambda s: "'" + s.replace("'", "''") + "'"
        script = '& %s %s | Out-Null' % (q(args[0]), ' '.join(q(x) for x in args[1:]))
        subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', script], capture_output=True, timeout=180)
    return os.path.isfile(png)


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ''
    os.makedirs(OUT, exist_ok=True)
    browser = p.find_browser()
    tmp = tempfile.mkdtemp(prefix='ms-social-')
    try:
        for name, (k, t, s, img, kind) in CARDS.items():
            if only not in name:
                continue
            foto = kind == 'foto'
            page = HTML % dict(
                k=k, t=t, s=s, img='file:///' + os.path.join(ROOT, img).replace('\\', '/'),
                cols='1fr 400px' if foto else '470px 1fr', size=50 if foto else (58 if len(t) < 24 else 50),
                pich='518px' if foto else 'auto',
                imgcss='width:100%;height:100%;object-fit:cover;object-position:50% 35%' if foto else 'width:100%;height:auto')
            src = os.path.join(tmp, name + '.html')
            io.open(src, 'w', encoding='utf-8').write(page)
            png = os.path.join(tmp, name + '.png')
            if not shot(browser, 'file:///' + src.replace('\\', '/'), png, os.path.join(tmp, 'perfil')):
                print('  FALLÓ   ', name); continue
            im = Image.open(png).convert('RGB')
            if im.size != (1200, 630):
                im = im.crop((0, 0, 1200, 630))
            dst = os.path.join(OUT, name + '.jpg')
            im.save(dst, 'JPEG', quality=88, optimize=True, progressive=True)
            print('  OK      %-28s %d KB' % (name + '.jpg', os.path.getsize(dst) // 1024))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
