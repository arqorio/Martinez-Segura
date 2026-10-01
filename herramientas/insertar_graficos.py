#!/usr/bin/env python3
"""Insert each service's diagram (assets/graficos/*.svg) into its pages.

Only the <x-dc> template is edited; run prerender.py afterwards. Idempotent:
a page that already shows a diagram is left alone.

    python herramientas/insertar_graficos.py
"""
import glob, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'herramientas'))
import prerender as p

# page-name pattern -> (svg, alt, caption)
G = [
    (r'^(levantamiento-topografico(-costa-rica)?|topografo-[a-z-]+)\.html$', 'levantamiento-topografico',
     'Plano topográfico de ejemplo con curvas de nivel cada metro y la cota de cada punto medido con estación total',
     'Así se ve un levantamiento topográfico: curvas de nivel cada metro, curvas maestras cada cinco y la cota de cada punto '
     'medido con estación total. Terreno de ejemplo de 110 × 58 m.'),
    (r'^levantamiento-catastral(-costa-rica)?\.html$', 'levantamiento-catastral',
     'Plano catastral de ejemplo con la distancia y el rumbo de cada lindero y el área del terreno',
     'Plano catastral de ejemplo: la distancia y el rumbo de cada lindero, y el área en m², varas² y manzanas, salen de las '
     'coordenadas medidas en campo.'),
    (r'^control-de-obras(-[a-z-]+)?\.html$', 'control-de-obras',
     'Replanteo de ejes y zapatas con estación total y control de niveles contra un banco de nivel',
     'Replanteo de ejes y zapatas: la estación total marca el centro de cada zapata desde un punto de control, y el nivel de '
     'piso se verifica contra el banco de nivel.'),
    (r'^diseno-vialidad(-[a-z-]+)?\.html$', 'diseno-vialidad',
     'Planta y perfil longitudinal de un camino con curva horizontal, rasante y zonas de corte y relleno',
     'Planta y perfil de un camino de ejemplo: curva de 60 m de radio, estaciones cada 20 m y las zonas de corte y relleno '
     'entre el terreno natural y la rasante.'),
    (r'^costos-presupuestos(-[a-z-]+)?\.html$', 'costos-presupuestos',
     'Cronograma de obra con el peso de cada partida y la curva S del avance acumulado del costo',
     'Presupuesto y cronograma de ejemplo: el peso de cada partida en el costo total y la curva S del avance acumulado, '
     'la herramienta para controlar el gasto semana a semana.'),
    (r'^diseno-arquitectonico(-[a-z-]+)?\.html$', 'diseno-arquitectonico',
     'Planta arquitectónica de una vivienda con cotas, puertas, ventanas y el área de cada espacio',
     'Planta arquitectónica de ejemplo con cotas a ejes y el área libre de cada espacio.'),
    (r'^instalacion-mojones-geodesicos(-costa-rica)?\.html$', 'mojones-geodesicos',
     'Posicionamiento GNSS de un mojón geodésico con una estación base y un receptor que observan los mismos satélites',
     'La base GNSS y el receptor sobre el mojón observan los mismos satélites al mismo tiempo; con eso se calcula la línea '
     'base y la posición del mojón.'),
    (r'^modelado-bim(-costa-rica)?\.html$', 'modelado-bim',
     'Modelo BIM con las capas de arquitectura, estructura e instalaciones y una interferencia detectada',
     'En BIM, arquitectura, estructura e instalaciones viven en un mismo modelo, y los choques se detectan antes de llegar a la obra.'),
    (r'^soldadura(-[a-z-]+)?\.html$', 'soldadura',
     'Junta a tope con ranura en V y junta en T con soldadura de filete, con sus símbolos AWS',
     'Dos uniones típicas en estructuras de acero, dibujadas a escala con su símbolo de soldadura AWS.'),
    (r'^(construccion-[a-z-]+|parajon-construcciones)\.html$', 'construccion',
     'Corte de una edificación de dos niveles con zapatas, columnas, losas y niveles de piso',
     'Corte de una edificación de dos niveles: zapatas, columnas a cada 5 m, losas y niveles de piso.'),
]

GRID = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));'


def size(svg_name):
    t = io.open(os.path.join(ROOT, 'assets', 'graficos', svg_name + '.svg'), encoding='utf-8').read(400)
    w, h = re.search(r'viewBox="0 0 (\d+) (\d+)"', t).groups()
    return int(w), int(h)


def figure(svg_name, alt, cap, parcon=False):
    w, h = size(svg_name)
    border = 'rgba(31,31,31,0.12)' if parcon else 'rgba(43,31,21,0.12)'
    capc = '#5F5F5F' if parcon else '#6B5844'
    return ('<figure data-grafico style="margin:0 0 34px;max-width:880px;">'
            '<img src="/assets/graficos/%s.svg" width="%d" height="%d" alt="%s" loading="lazy" decoding="async" '
            'style="display:block;width:100%%;height:auto;border:1px solid %s;border-radius:12px;">'
            '<figcaption style="font-size:14px;color:%s;line-height:1.55;margin-top:10px;">%s</figcaption></figure>'
            % (svg_name, w, h, alt, border, capc, cap))


def insert(src, fig, name):
    x = p.xdc_block(src)
    if not x or 'data-grafico' in x:
        return None
    i = x.find(GRID)
    if i > -1:
        new_x = x[:i] + fig + x[i:]
    elif name.startswith('topografo-'):
        j = x.index('</section>') + len('</section>')
        new_x = (x[:j] + '\n<div style="max-width:1180px;margin:0 auto;padding:clamp(30px,4.5vw,46px) clamp(16px,5vw,32px) 0;">'
                 + fig.replace('margin:0 0 34px', 'margin:0') + '</div>' + x[j:])
    elif name == 'parajon-construcciones.html':
        j = x.index('<section id="servicios"')
        new_x = (x[:j] + '<div style="max-width:1180px;margin:0 auto;padding:clamp(40px,6vw,60px) clamp(16px,5vw,32px) 0;">'
                 + fig.replace('margin:0 0 34px', 'margin:0') + '</div>\n\n' + x[j:])
    else:
        return None
    return src.replace(x, new_x, 1)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    done, skipped = 0, []
    for path in sorted(glob.glob(os.path.join(ROOT, '*.html'))):
        name = os.path.basename(path)
        for pat, svg_name, alt, cap in G:
            if re.match(pat, name):
                raw = io.open(path, encoding='utf-8', newline='').read()
                nl = '\r\n' if '\r\n' in raw else '\n'
                src = p.strip(raw).replace('\r\n', '\n')
                out = insert(src, figure(svg_name, alt, cap, name == 'parajon-construcciones.html'), name)
                if out is None:
                    skipped.append(name)
                else:
                    io.open(path, 'w', encoding='utf-8', newline='').write(out.replace('\n', nl))
                    done += 1
                break
    print('con gráfico nuevo: %d' % done)
    print('omitidas (sin plantilla o ya tenían): %s' % (', '.join(skipped) or 'ninguna'))


if __name__ == '__main__':
    main()
