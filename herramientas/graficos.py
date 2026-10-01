#!/usr/bin/env python3
"""Generate the technical diagrams shown on each service page.

Every number drawn is computed from the geometry below — distances, bearings,
areas, contour elevations, grades, cut/fill — so the figures are exact for the
example they show. Output: assets/graficos/<servicio>.svg (static, no scripts).

Style: thin lines, brand palette, few labels. Text uses a system font stack
because an SVG loaded through <img> cannot see the page's web fonts.

    python herramientas/graficos.py
"""
import math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'graficos')

INK, INK2, MUTED = '#2B1F15', '#5C4A36', '#8A7A62'
RUST, TEAL, GOLD, PAPER, LINE = '#B0512B', '#2F5D68', '#D9982A', '#FFFDF6', '#D8CBB0'
FONT = "system-ui,-apple-system,'Segoe UI',Roboto,Arial,sans-serif"
MONO = "ui-monospace,'SFMono-Regular',Consolas,'Liberation Mono',monospace"


def fmt(x, d=2):
    return ('%.' + str(d) + 'f') % x


def svg(w, h, body, title, desc):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
            'aria-labelledby="t d" font-family="%s">\n<title id="t">%s</title>\n<desc id="d">%s</desc>\n'
            '<rect width="%d" height="%d" fill="%s"/>\n%s\n</svg>\n') % (w, h, w, h, FONT, title, desc, w, h, PAPER, body)


def text(x, y, s, size=12, fill=INK2, anchor='start', weight=400, mono=False, rot=None, extra=''):
    fam = ' font-family="%s"' % MONO if mono else ''
    tr = ' transform="rotate(%s %s %s)"' % (fmt(rot, 1), fmt(x, 1), fmt(y, 1)) if rot is not None else ''
    return ('<text x="%s" y="%s" font-size="%s" fill="%s" text-anchor="%s" font-weight="%d"%s%s%s>%s</text>'
            % (fmt(x, 1), fmt(y, 1), size, fill, anchor, weight, fam, tr, extra, s))


def north_arrow(x, y, s=1.0):
    return ('<g transform="translate(%s %s) scale(%s)"><path d="M0 -22 L7 6 L0 1 L-7 6 Z" fill="%s"/>'
            '<path d="M0 -22 L0 1 L-7 6 Z" fill="%s"/>%s</g>'
            % (fmt(x, 1), fmt(y, 1), s, INK, PAPER, text(0, -28, 'N', 12, INK, 'middle', 700)))


def scale_bar(x, y, px_per_m, meters, label=None):
    """A bar exactly `meters` long at the drawing scale, split in halves."""
    w = px_per_m * meters
    half = w / 2
    return ('<g><rect x="%s" y="%s" width="%s" height="5" fill="%s"/><rect x="%s" y="%s" width="%s" height="5" fill="%s" stroke="%s" stroke-width="0.8"/>'
            '%s%s%s</g>' % (fmt(x, 1), fmt(y, 1), fmt(half, 1), INK, fmt(x + half, 1), fmt(y, 1), fmt(half, 1), PAPER, INK,
                            text(x, y + 18, '0', 10, MUTED, 'middle'),
                            text(x + half, y + 18, fmt(meters / 2, 0), 10, MUTED, 'middle'),
                            text(x + w, y + 18, (label or fmt(meters, 0)) + ' m', 10, MUTED, 'middle')))


# ------------------------------------------------------------------ geometry helpers
def azimuth(p, q):
    """Azimuth from north, clockwise, in degrees, for local E/N coordinates."""
    return (math.degrees(math.atan2(q[0] - p[0], q[1] - p[1])) + 360) % 360


def bearing(az):
    """Quadrant bearing, e.g. N 72°15' E (surveyors' 'rumbo')."""
    if az <= 90:   ns, ew, a = 'N', 'E', az
    elif az <= 180: ns, ew, a = 'S', 'E', 180 - az
    elif az <= 270: ns, ew, a = 'S', 'O', az - 180
    else:           ns, ew, a = 'N', 'O', 360 - az
    d = int(a); m = int(round((a - d) * 60))
    if m == 60: d, m = d + 1, 0
    return "%s %d°%02d' %s" % (ns, d, m, ew)


def shoelace(pts):
    return abs(sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                   for i in range(len(pts)))) / 2


def dist(p, q):
    return math.hypot(q[0] - p[0], q[1] - p[1])


V2 = 0.698737    # 1 vara cuadrada in m² (vara = 0.8359 m)
MZ = 6987.37     # 1 manzana = 10 000 varas² in m²


# ================================================================== 1. topographic survey
def terrain(x, y):
    """Smooth hill + gentle slope; elevations in metres for x, y in metres."""
    return (100 + 0.045 * x + 0.02 * y
            + 6.5 * math.exp(-(((x - 58) / 26) ** 2 + ((y - 30) / 18) ** 2))
            - 2.0 * math.exp(-(((x - 18) / 14) ** 2 + ((y - 12) / 10) ** 2)))


def contours(f, x0, x1, y0, y1, step, levels):
    """Marching squares; returns {level: [segments ((x,y),(x,y))]}."""
    nx, ny = int((x1 - x0) / step), int((y1 - y0) / step)
    xs = [x0 + i * step for i in range(nx + 1)]
    ys = [y0 + j * step for j in range(ny + 1)]
    grid = [[f(x, y) for x in xs] for y in ys]
    out = {}
    for lv in levels:
        segs = []
        for j in range(ny):
            for i in range(nx):
                c = [(xs[i], ys[j], grid[j][i]), (xs[i + 1], ys[j], grid[j][i + 1]),
                     (xs[i + 1], ys[j + 1], grid[j + 1][i + 1]), (xs[i], ys[j + 1], grid[j + 1][i])]
                pts = []
                for a in range(4):
                    p, q = c[a], c[(a + 1) % 4]
                    if (p[2] - lv) * (q[2] - lv) < 0:
                        t = (lv - p[2]) / (q[2] - p[2])
                        pts.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
                if len(pts) == 2:
                    segs.append(tuple(pts))
                elif len(pts) == 4:          # saddle: pair by the cell centre value
                    segs += [(pts[0], pts[1]), (pts[2], pts[3])]
        out[lv] = segs
    return out


def chain(segs, tol=1e-6):
    """Join contour segments into polylines."""
    lines, segs = [], [list(s) for s in segs]
    key = lambda p: (round(p[0], 5), round(p[1], 5))
    while segs:
        line = segs.pop()
        grown = True
        while grown:
            grown = False
            for k, s in enumerate(segs):
                if key(s[0]) == key(line[-1]): line.append(s[1])
                elif key(s[1]) == key(line[-1]): line.append(s[0])
                elif key(s[1]) == key(line[0]): line.insert(0, s[0])
                elif key(s[0]) == key(line[0]): line.insert(0, s[1])
                else: continue
                segs.pop(k); grown = True; break
        lines.append(line)
    return lines


def g_topografico():
    W, H = 820, 420
    S = 6.0                      # px per metre
    ox, oy = 40, 385             # drawing origin (x right, y up)
    X = lambda x: ox + x * S
    Y = lambda y: oy - y * S
    x0, x1, y0, y1 = 0, 110, 0, 58
    lo = math.ceil(min(terrain(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)))
    hi = math.floor(max(terrain(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)))
    levels = list(range(lo, hi + 1))            # 1 m interval
    cs = contours(terrain, x0, x1, y0, y1, 1.0, levels)
    body = ['<rect x="%s" y="%s" width="%s" height="%s" fill="none" stroke="%s" stroke-width="1"/>'
            % (X(x0), Y(y1), (x1 - x0) * S, (y1 - y0) * S, LINE)]
    for lv in levels:
        major = lv % 5 == 0
        for line in chain(cs[lv]):
            d = 'M' + ' L'.join('%s %s' % (fmt(X(p[0]), 1), fmt(Y(p[1]), 1)) for p in line)
            body.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s"/>'
                        % (d, RUST if major else '#C9A58A', 1.6 if major else 0.8))
        if major and cs[lv]:
            # label near the middle of the longest polyline, sitting on the line
            line = max(chain(cs[lv]), key=len)
            p = line[len(line) // 2]
            body.append('<rect x="%s" y="%s" width="34" height="14" fill="%s"/>' % (fmt(X(p[0]) - 17, 1), fmt(Y(p[1]) - 8, 1), PAPER))
            body.append(text(X(p[0]), Y(p[1]) + 4, '%d m' % lv, 10.5, RUST, 'middle', 700))
    # total station and observed points: the elevation shown is the model's value
    st = (30.0, 40.0)
    pts = [(12, 50), (48, 52), (58, 30), (85, 45), (96, 12), (70, 8), (40, 14)]
    body.append('<g stroke="%s" stroke-width="0.9" stroke-dasharray="3 3">' % TEAL +
                ''.join('<line x1="%s" y1="%s" x2="%s" y2="%s"/>' % (fmt(X(st[0]), 1), fmt(Y(st[1]), 1), fmt(X(p[0]), 1), fmt(Y(p[1]), 1)) for p in pts)
                + '</g>')
    for i, p in enumerate(pts, 1):
        z = terrain(*p)
        body.append('<circle cx="%s" cy="%s" r="3" fill="%s"/>' % (fmt(X(p[0]), 1), fmt(Y(p[1]), 1), TEAL))
        body.append(text(X(p[0]) + 6, Y(p[1]) - 5, 'P%d · %s' % (i, fmt(z, 2)), 10, TEAL, mono=True))
    body.append('<path d="M%s %s l-7 12 h14 z" fill="%s"/>' % (fmt(X(st[0]), 1), fmt(Y(st[1]) - 6, 1), INK))
    body.append(text(X(st[0]), Y(st[1]) + 20, 'Estación total', 10.5, INK, 'middle', 700))
    body.append(north_arrow(X(x1) - 22, Y(y1) + 42))
    body.append(scale_bar(X(x1) - 20 * S - 10, Y(0) + 16 - 30, S, 20))
    body.append(text(X(0), 22, 'Curvas de nivel cada 1 m · maestras cada 5 m', 12, INK, weight=700))
    body.append(text(X(0) + 330, 22, 'Cotas de los puntos medidos en metros', 11, MUTED))
    return svg(W, H, '\n'.join(body), 'Levantamiento topográfico: curvas de nivel y puntos medidos',
               'Plano de un terreno de 110 por 58 metros con curvas de nivel cada metro, curvas maestras cada cinco metros, '
               'la estación total y siete puntos medidos con su cota.')


# ================================================================== 2. cadastral survey
def g_catastral():
    W, H = 820, 432
    # parcel vertices in local E/N metres (clockwise from V1)
    V = [(0.0, 0.0), (6.2, 31.5), (38.9, 36.8), (47.6, 9.4), (27.0, -4.8)]
    S = 7.4
    ox, oy = 250, 355
    X = lambda e: ox + e * S
    Y = lambda n: oy - n * S
    body = []
    body.append('<polygon points="%s" fill="#F4EAD2" stroke="%s" stroke-width="1.8"/>'
                % (' '.join('%s,%s' % (fmt(X(e), 1), fmt(Y(n), 1)) for e, n in V), INK))
    per = 0
    for i in range(len(V)):
        p, q = V[i], V[(i + 1) % len(V)]
        d, az = dist(p, q), azimuth(p, q)
        per += d
        mx, my = X((p[0] + q[0]) / 2), Y((p[1] + q[1]) / 2)
        ang = -math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
        if ang > 90: ang -= 180
        if ang < -90: ang += 180
        # push the label outward from the centroid
        cx = sum(v[0] for v in V) / len(V); cy = sum(v[1] for v in V) / len(V)
        vx, vy = (p[0] + q[0]) / 2 - cx, (p[1] + q[1]) / 2 - cy
        n = math.hypot(vx, vy)
        lx, ly = mx + vx / n * 16, my - vy / n * 16
        body.append(text(lx, ly, '%s m · %s' % (fmt(d, 2), bearing(az)), 10.5, INK2, 'middle', mono=True, rot=ang))
    for i, (e, n) in enumerate(V, 1):
        body.append('<circle cx="%s" cy="%s" r="4" fill="%s" stroke="%s" stroke-width="1.5"/>' % (fmt(X(e), 1), fmt(Y(n), 1), PAPER, RUST))
        cx = sum(v[0] for v in V) / len(V); cy = sum(v[1] for v in V) / len(V)
        vx, vy = e - cx, n - cy; nn = math.hypot(vx, vy)
        body.append(text(X(e) + vx / nn * 14, Y(n) - vy / nn * 14 + 4, 'V%d' % i, 11, RUST, 'middle', 700))
    A = shoelace(V)
    cx = sum(v[0] for v in V) / len(V); cy = sum(v[1] for v in V) / len(V)
    body.append(text(X(cx), Y(cy) - 6, 'Área', 12, MUTED, 'middle'))
    body.append(text(X(cx), Y(cy) + 12, '%s m²' % '{:,.2f}'.format(A), 16, INK, 'middle', 700))
    body.append(text(X(cx), Y(cy) + 30, '%s v² · %s mz' % ('{:,.2f}'.format(A / V2), fmt(A / MZ, 4)), 11, MUTED, 'middle', mono=True))
    for lab, xx, yy in (('Colinda al norte', X(22), Y(36.8) - 26), ('Colinda al sur', X(22), Y(-4.8) + 26)):
        body.append(text(xx, yy, lab, 11, MUTED, 'middle'))
    body.append(text(X(-4) - 30, Y(16), 'Colinda al oeste', 11, MUTED, 'middle', rot=-90))
    body.append(text(X(47.6) + 44, Y(16), 'Colinda al este', 11, MUTED, 'middle', rot=90))
    body.append(north_arrow(760, 70))
    body.append(scale_bar(640, 380, S, 10))
    body.append(text(30, 28, 'Plano catastral', 13, INK, weight=700))
    body.append(text(30, 48, 'Distancia y rumbo de cada lindero', 11.5, MUTED))
    body.append(text(30, 66, 'calculados de las coordenadas', 11.5, MUTED))
    body.append(text(30, 96, 'Perímetro  %s m' % fmt(per, 2), 11.5, INK2, mono=True))
    return svg(W, H, '\n'.join(body), 'Levantamiento catastral: linderos, rumbos y área',
               'Polígono de un terreno de cinco vértices con la distancia y el rumbo de cada lindero, los colindantes '
               'y el área en metros cuadrados, varas cuadradas y manzanas.'), dict(area=A, per=per)


# ================================================================== 3. construction control (layout)
def g_control_obra():
    W, H = 820, 462
    sx, sy = [0, 5, 10, 15], [0, 4.5, 9]          # axis positions in metres (A-D, 1-3)
    S = 26.0
    ox, oy = 150, 382
    X = lambda x: ox + x * S
    Y = lambda y: oy - y * S
    body = []
    for i, x in enumerate(sx):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.9" stroke-dasharray="10 4 2 4"/>'
                    % (X(x), Y(-1.2), X(x), Y(sy[-1] + 1.2), TEAL))
        body.append('<circle cx="%s" cy="%s" r="11" fill="%s" stroke="%s" stroke-width="1.2"/>' % (X(x), Y(sy[-1] + 1.9), PAPER, TEAL))
        body.append(text(X(x), Y(sy[-1] + 1.9) + 4, 'ABCD'[i], 11, TEAL, 'middle', 700))
    for j, y in enumerate(sy):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.9" stroke-dasharray="10 4 2 4"/>'
                    % (X(-1.2), Y(y), X(sx[-1] + 1.2), Y(y), TEAL))
        body.append('<circle cx="%s" cy="%s" r="11" fill="%s" stroke="%s" stroke-width="1.2"/>' % (X(-1.9), Y(y), PAPER, TEAL))
        body.append(text(X(-1.9), Y(y) + 4, '123'[j], 11, TEAL, 'middle', 700))
    fz = 1.2                                       # footing 1.20 x 1.20 m
    for x in sx:
        for y in sy:
            body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#F4EAD2" stroke="%s" stroke-width="1.3"/>'
                        % (fmt(X(x - fz / 2), 1), fmt(Y(y + fz / 2), 1), fmt(fz * S, 1), fmt(fz * S, 1), INK))
    # dimension chains
    yd = Y(-2.3)
    for a, b in zip(sx, sx[1:]):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (X(a), yd, X(b), yd, INK2))
        body.append(text((X(a) + X(b)) / 2, yd - 5, '%s m' % fmt(b - a, 2), 10.5, INK2, 'middle', mono=True))
    for x in sx:
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (X(x), yd - 5, X(x), yd + 5, INK2))
    xd = X(sx[-1] + 2.6)
    for a, b in zip(sy, sy[1:]):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (xd, Y(a), xd, Y(b), INK2))
        body.append(text(xd + 6, (Y(a) + Y(b)) / 2 + 4, '%s m' % fmt(b - a, 2), 10.5, INK2, mono=True))
    for y in sy:
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (xd - 5, Y(y), xd + 5, Y(y), INK2))
    # total station on a control point, staking two footing centres
    st = (-3.0, 1.2)          # chosen by search: both sight lines clear every footing by 0.46 m
    for tgt, tt in (((5, 4.5), 0.50), ((10, 9), 0.62)):
        d = dist(st, tgt)
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1" stroke-dasharray="4 3"/>'
                    % (X(st[0]), Y(st[1]), X(tgt[0]), Y(tgt[1]), RUST))
        body.append('<circle cx="%s" cy="%s" r="3" fill="%s"/>' % (X(tgt[0]), Y(tgt[1]), RUST))
        mx, my = X(st[0] + tt * (tgt[0] - st[0])), Y(st[1] + tt * (tgt[1] - st[1]))
        ang = -math.degrees(math.atan2(tgt[1] - st[1], tgt[0] - st[0]))
        body.append(text(mx, my - 5, fmt(d, 3) + ' m', 10, RUST, 'middle', mono=True, rot=ang))
    body.append('<path d="M%s %s l-7 12 h14 z" fill="%s"/>' % (X(st[0]), Y(st[1]) - 6, INK))
    body.append(text(X(st[0]), Y(st[1]) + 20, 'Estación', 10.5, INK, 'middle', 700))
    body.append(text(30, 28, 'Replanteo de ejes y zapatas', 13, INK, weight=700))
    body.append(text(30, 48, 'Zapatas de 1.20 × 1.20 m en la intersección de cada eje', 11.5, MUTED))
    body.append(text(30, 66, 'La estación marca cada centro desde un punto de control', 11.5, MUTED))
    # level check panel: benchmark and finished-floor level
    px = 660
    body.append('<rect x="%d" y="112" width="140" height="178" fill="none" stroke="%s"/>' % (px, LINE))
    body.append(text(px + 70, 132, 'Control de niveles', 11.5, INK, 'middle', 700))
    bm, npt = 100.000, 100.450
    body.append(text(px + 12, 162, 'BM', 11, MUTED)); body.append(text(px + 128, 162, fmt(bm, 3), 11, INK2, 'end', mono=True))
    body.append(text(px + 12, 186, 'NPT diseño', 11, MUTED)); body.append(text(px + 128, 186, fmt(npt, 3), 11, INK2, 'end', mono=True))
    body.append(text(px + 12, 210, 'Diferencia', 11, MUTED)); body.append(text(px + 128, 210, '+' + fmt(npt - bm, 3), 11, RUST, 'end', 700, True))
    body.append('<line x1="%d" y1="228" x2="%d" y2="228" stroke="%s"/>' % (px + 12, px + 128, LINE))
    body.append(text(px + 12, 250, 'Cotas en metros', 10, MUTED))
    body.append(text(px + 12, 266, 'BM: banco de nivel', 10, MUTED))
    body.append(text(px + 12, 282, 'NPT: nivel de piso', 10, MUTED))
    return svg(W, H, '\n'.join(body), 'Control de obra: replanteo de ejes, zapatas y niveles',
               'Planta con ejes A a D y 1 a 3 separados 5.00 y 4.50 metros, zapatas de 1.20 metros en cada intersección, '
               'una estación total replanteando dos centros de zapata con sus distancias y un cuadro de control de niveles.')


# ================================================================== 4. road design (plan + profile)
def g_vialidad():
    W, H = 820, 440
    body = []
    # ---- plan: tangent, circular curve R=60 m with deflection 40°, tangent
    R, delta = 60.0, math.radians(40)
    T = R * math.tan(delta / 2); Lc = R * delta
    S = 2.2
    ox, oy = 60, 170
    X = lambda e: ox + e * S
    Y = lambda n: oy - n * S
    # PC at (40,0) heading east; curve turns left
    pc = (40.0, 0.0)
    cen = (pc[0], pc[1] + R)
    pts = [(0.0, 0.0), pc]
    n = 30
    for k in range(1, n + 1):
        a = -math.pi / 2 + delta * k / n
        pts.append((cen[0] + R * math.cos(a), cen[1] + R * math.sin(a)))
    pt = pts[-1]
    hd = delta
    end = (pt[0] + 90 * math.cos(hd), pt[1] + 90 * math.sin(hd))
    pts.append(end)
    body.append('<path d="M%s" fill="none" stroke="%s" stroke-width="2"/>'
                % (' L'.join('%s %s' % (fmt(X(e), 1), fmt(Y(nn), 1)) for e, nn in pts), INK))
    # stations every 20 m along the alignment
    def point_at(s):
        if s <= 40: return (s, 0.0), 0.0
        if s <= 40 + Lc:
            a = -math.pi / 2 + (s - 40) / R
            return (cen[0] + R * math.cos(a), cen[1] + R * math.sin(a)), (s - 40) / R
        d = s - 40 - Lc
        return (pt[0] + d * math.cos(hd), pt[1] + d * math.sin(hd)), hd
    total = 40 + Lc + 90
    s = 0
    while s <= total + 1e-6:
        (e, nn), h = point_at(s)
        nx, ny = -math.sin(h), math.cos(h)
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1"/>'
                    % (fmt(X(e - nx * 3), 1), fmt(Y(nn - ny * 3), 1), fmt(X(e + nx * 3), 1), fmt(Y(nn + ny * 3), 1), INK))
        if s % 40 == 0:
            body.append(text(X(e + nx * 9), Y(nn + ny * 9), '0+%03d' % s, 9.5, INK2, 'middle', mono=True))
        s += 20
    for lab, p in (('PC', pc), ('PT', pt)):
        body.append('<circle cx="%s" cy="%s" r="3.5" fill="%s"/>' % (fmt(X(p[0]), 1), fmt(Y(p[1]), 1), RUST))
        body.append(text(X(p[0]) + 8, Y(p[1]) + 14, lab, 10.5, RUST, weight=700))
    body.append(text(X(112), Y(14), 'Curva: R = %s m · Δ = 40°' % fmt(R, 0), 10.5, RUST, mono=True))
    body.append(text(X(112), Y(14) + 15, 'L = %s m · T = %s m' % (fmt(Lc, 2), fmt(T, 2)), 10.5, RUST, mono=True))
    body.append(text(30, 26, 'Planta del eje', 13, INK, weight=700))
    body.append(text(140, 26, 'estaciones cada 20 m', 11, MUTED))
    # ---- profile
    px0, py0, pw, ph = 60, 280, 720, 130
    L = 200.0
    ground = lambda s: 52 + 3.2 * math.sin(s / 28) + 0.018 * s + 1.6 * math.sin(s / 9)
    g1 = 0.030                                          # grade +3.0 %
    z0 = 52.0
    grade = lambda s: z0 + g1 * s
    zmin, zmax = 48, 62
    PX = lambda s: px0 + s / L * pw
    PY = lambda z: py0 + ph - (z - zmin) / (zmax - zmin) * ph
    body.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s"/>' % (px0, py0, pw, ph, LINE))
    # cut (grade below ground) and fill (grade above ground), shaded exactly between the lines
    step = 1.0
    ss = [i * step for i in range(int(L / step) + 1)]
    for i in range(len(ss) - 1):
        a, b = ss[i], ss[i + 1]
        col = '#E7C8B3' if grade((a + b) / 2) < ground((a + b) / 2) else '#C9DCDF'
        body.append('<polygon points="%s,%s %s,%s %s,%s %s,%s" fill="%s"/>'
                    % (fmt(PX(a), 1), fmt(PY(ground(a)), 1), fmt(PX(b), 1), fmt(PY(ground(b)), 1),
                       fmt(PX(b), 1), fmt(PY(grade(b)), 1), fmt(PX(a), 1), fmt(PY(grade(a)), 1), col))
    body.append('<path d="M%s" fill="none" stroke="%s" stroke-width="1.4"/>'
                % (' L'.join('%s %s' % (fmt(PX(s_), 1), fmt(PY(ground(s_)), 1)) for s_ in ss), '#8B6B4E'))
    body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2"/>' % (PX(0), PY(grade(0)), PX(L), PY(grade(L)), RUST))
    for s_ in range(0, 201, 40):
        body.append(text(PX(s_), py0 + ph + 16, '0+%03d' % s_, 9.5, MUTED, 'middle', mono=True))
    body.append(text(30, py0 - 12, 'Perfil longitudinal', 13, INK, weight=700))
    body.append(text(PX(118), PY(grade(118)) - 10, 'Rasante +3.0 %', 11, RUST, weight=700))
    body.append(text(PX(96), PY(ground(96)) + 20, 'Terreno natural', 10.5, '#8B6B4E'))
    for z in (50, 55, 60):
        body.append('<line x1="%d" y1="%s" x2="%d" y2="%s" stroke="%s" stroke-width="0.6"/>' % (px0 - 4, fmt(PY(z), 1), px0, fmt(PY(z), 1), INK2))
        body.append(text(px0 - 8, PY(z) + 4, '%d m' % z, 9.5, MUTED, 'end', mono=True))
    lx = 560
    body.append('<rect x="%d" y="%d" width="12" height="10" fill="#E7C8B3"/>' % (lx, py0 - 22))
    body.append(text(lx + 17, py0 - 13, 'Corte', 10.5, INK2))
    body.append('<rect x="%d" y="%d" width="12" height="10" fill="#C9DCDF"/>' % (lx + 70, py0 - 22))
    body.append(text(lx + 87, py0 - 13, 'Relleno', 10.5, INK2))
    return svg(W, H, '\n'.join(body), 'Diseño de vialidad: planta del eje y perfil longitudinal',
               'Planta de un camino con curva horizontal de 60 metros de radio y estaciones cada 20 metros, y su perfil '
               'longitudinal con el terreno natural, la rasante al 3 por ciento y las zonas de corte y relleno.')


# ================================================================== 5. cost & budget (S-curve)
def g_costos():
    W, H = 820, 420
    # example schedule: activity, start week, duration (weeks), share of budget (%)
    acts = [('Preliminares', 0, 2, 4), ('Fundaciones', 1, 4, 16), ('Estructura', 4, 6, 28),
            ('Mampostería', 8, 5, 14), ('Techo', 11, 3, 12), ('Instalaciones', 9, 7, 11), ('Acabados', 13, 5, 15)]
    assert sum(a[3] for a in acts) == 100
    weeks = 18
    gx, gy, gw, rowh = 150, 70, 600, 24
    body = []
    WX = lambda w: gx + w / weeks * gw
    for w in range(0, weeks + 1, 2):
        body.append('<line x1="%s" y1="%d" x2="%s" y2="%d" stroke="%s" stroke-width="0.6"/>' % (fmt(WX(w), 1), gy - 6, fmt(WX(w), 1), gy + rowh * len(acts), LINE))
        body.append(text(WX(w), gy - 12, 'S%d' % w, 9.5, MUTED, 'middle', mono=True))
    for i, (name, st, du, pc) in enumerate(acts):
        y = gy + i * rowh
        body.append(text(gx - 12, y + 16, name, 11, INK2, 'end'))
        body.append('<rect x="%s" y="%d" width="%s" height="12" rx="2" fill="%s"/>' % (fmt(WX(st), 1), y + 6, fmt(WX(st + du) - WX(st), 1), TEAL))
        body.append(text(WX(st + du) + 6, y + 16, '%d %%' % pc, 10, MUTED, mono=True))
    # S-curve: cost spread evenly over each activity's weeks, accumulated
    cum, acc = [0.0], 0.0
    for w in range(weeks):
        acc += sum(pc / du for (_, st, du, pc) in acts if st <= w < st + du)
        cum.append(acc)
    assert abs(cum[-1] - 100) < 1e-9
    cy0, ch = 250, 130
    CY = lambda p: cy0 + ch - p / 100 * ch
    body.append('<rect x="%d" y="%d" width="%d" height="%d" fill="none" stroke="%s"/>' % (gx, cy0, gw, ch, LINE))
    for p in (25, 50, 75, 100):
        body.append('<line x1="%d" y1="%s" x2="%d" y2="%s" stroke="%s" stroke-width="0.6"/>' % (gx, fmt(CY(p), 1), gx + gw, fmt(CY(p), 1), LINE))
        body.append(text(gx - 8, CY(p) + 4, '%d %%' % p, 9.5, MUTED, 'end', mono=True))
    body.append('<path d="M%s" fill="none" stroke="%s" stroke-width="2.2"/>'
                % (' L'.join('%s %s' % (fmt(WX(w), 1), fmt(CY(c), 1)) for w, c in enumerate(cum)), RUST))
    mid = next(w for w, c in enumerate(cum) if c >= 50)
    body.append('<circle cx="%s" cy="%s" r="3.5" fill="%s"/>' % (fmt(WX(mid), 1), fmt(CY(cum[mid]), 1), RUST))
    body.append(text(WX(mid) + 8, CY(cum[mid]) + 14, '%s %% en la semana %d' % (fmt(cum[mid], 1), mid), 10.5, RUST, mono=True))
    body.append(text(30, 30, 'Presupuesto y cronograma', 13, INK, weight=700))
    body.append(text(250, 30, 'Ejemplo: peso de cada partida en el costo total', 11, MUTED))
    body.append(text(30, cy0 + 14, 'Curva S', 12, INK, weight=700))
    body.append(text(30, cy0 + 30, 'avance acumulado', 10.5, MUTED))
    body.append(text(30, cy0 + 44, 'del costo', 10.5, MUTED))
    return svg(W, H, '\n'.join(body), 'Costos y presupuestos: cronograma y curva S',
               'Cronograma de siete partidas de una obra de 18 semanas con el peso de cada una en el costo total, y la curva S '
               'del avance acumulado del costo calculada a partir de ese cronograma.')


# ================================================================== 6. architectural design (floor plan)
def g_arquitectonico():
    W, H = 820, 420
    S = 36.0
    ox, oy = 170, 360
    X = lambda x: ox + x * S
    Y = lambda y: oy - y * S
    wt = 0.15                                    # wall thickness 0.15 m
    Wd, Hd = 12.0, 8.0                            # outer dimensions 12.00 x 8.00 m
    body = []
    body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#F4EAD2" stroke="%s" stroke-width="%s"/>'
                % (X(0), Y(Hd), Wd * S, Hd * S, INK, wt * S))
    # interior walls: x=5 (full height), y=4.5 from x=5 to 12
    body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (X(5), Y(0), X(5), Y(Hd), INK, wt * S * 0.8))
    body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (X(5), Y(4.5), X(Wd), Y(4.5), INK, wt * S * 0.8))
    # door openings (0.90 m) with swing arcs
    def door(xh, yh, horizontal, flip=False):
        w = 0.9
        if horizontal:
            body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#F4EAD2" stroke-width="%s"/>' % (X(xh), Y(yh), X(xh + w), Y(yh), wt * S + 2))
            sgn = -1 if flip else 1
            body.append('<path d="M%s %s L%s %s A%s %s 0 0 %d %s %s" fill="none" stroke="%s" stroke-width="0.9"/>'
                        % (X(xh), Y(yh), X(xh), Y(yh + sgn * w), w * S, w * S, 1 if not flip else 0, X(xh + w), Y(yh), INK2))
        else:
            body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="#F4EAD2" stroke-width="%s"/>' % (X(xh), Y(yh), X(xh), Y(yh + w), wt * S + 2))
            body.append('<path d="M%s %s L%s %s A%s %s 0 0 0 %s %s" fill="none" stroke="%s" stroke-width="0.9"/>'
                        % (X(xh), Y(yh), X(xh + w), Y(yh), w * S, w * S, X(xh), Y(yh + w), INK2))
    door(2.0, 0.0, True)           # main entrance
    door(5.0, 2.2, False)          # living -> bedroom 2
    door(5.0, 6.0, False)          # living -> bedroom 1
    # windows (double line on the wall)
    for (x1_, y1_, x2_, y2_) in ((X(7.0), Y(Hd), X(9.5), Y(Hd)), (X(Wd), Y(1.5), X(Wd), Y(3.2)), (X(0), Y(3), X(0), Y(5.5))):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="%s"/>' % (x1_, y1_, x2_, y2_, PAPER, wt * S - 1))
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.9"/>' % (x1_, y1_, x2_, y2_, TEAL))
    # rooms: interior clear areas computed from wall centrelines minus half walls
    rooms = [('Sala-comedor-cocina', 0, 0, 5, Hd), ('Dormitorio 2', 5, 0, Wd, 4.5), ('Dormitorio 1', 5, 4.5, Wd, Hd)]
    for name, a, b, c, d in rooms:
        iw = (c - a) - wt; ih = (d - b) - wt
        area = iw * ih
        body.append(text(X((a + c) / 2), Y((b + d) / 2) - 2, name, 11.5, INK, 'middle', 700))
        body.append(text(X((a + c) / 2), Y((b + d) / 2) + 15, '%s m²' % fmt(area, 2), 11, INK2, 'middle', mono=True))
    # dimension lines
    def dim_h(a, b, y, label):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (X(a), y, X(b), y, INK2))
        for x in (a, b):
            body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (X(x) - 4, y + 4, X(x) + 4, y - 4, INK2))
        body.append(text((X(a) + X(b)) / 2, y - 5, label, 10.5, INK2, 'middle', mono=True))
    dim_h(0, 5, Y(Hd) - 18, '5.00'); dim_h(5, Wd, Y(Hd) - 18, '7.00'); dim_h(0, Wd, Y(Hd) - 38, '12.00')
    xl = X(Wd) + 20
    for a, b, lab in ((0, 4.5, '4.50'), (4.5, Hd, '3.50')):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (xl, Y(a), xl, Y(b), INK2))
        for yy in (a, b):
            body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (xl - 4, Y(yy) + 4, xl + 4, Y(yy) - 4, INK2))
        body.append(text(xl + 8, (Y(a) + Y(b)) / 2 + 4, lab, 10.5, INK2, mono=True))
    body.append(text(30, 30, 'Planta arquitectónica', 13, INK, weight=700))
    body.append(text(30, 50, 'Cotas a ejes en metros', 11, MUTED))
    body.append(text(30, 68, 'Áreas libres descontando', 11, MUTED))
    body.append(text(30, 84, 'muros de 0.15 m', 11, MUTED))
    body.append(text(30, 116, 'Construida  %s m²' % fmt((Wd + wt) * (Hd + wt), 2), 11, INK2, mono=True))
    return svg(W, H, '\n'.join(body), 'Diseño arquitectónico: planta con cotas y áreas',
               'Planta de una vivienda de 12 por 8 metros a ejes con sala-comedor-cocina y dos dormitorios, puertas, ventanas, '
               'cotas y el área libre de cada espacio.')


# ================================================================== 7. geodetic monuments (GNSS baseline)
def g_mojones():
    W, H = 820, 400
    body = []
    base, rover = (230, 300), (600, 300)
    # satellites common to both receivers
    sats = [(360, 58), (480, 40), (610, 52), (740, 80)]
    for sx_, sy_ in sats:
        body.append('<g transform="translate(%d %d)"><rect x="-7" y="-5" width="14" height="10" fill="%s"/>'
                    '<rect x="-24" y="-3" width="14" height="6" fill="%s"/><rect x="10" y="-3" width="14" height="6" fill="%s"/></g>'
                    % (sx_, sy_, INK2, TEAL, TEAL))
        for rx, ry in (base, rover):
            body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="0.7" stroke-dasharray="2 4"/>' % (sx_, sy_ + 6, rx, ry - 60, '#B9C9CC'))
    def tripod(x, y, label):
        body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4"/>' % (x, y - 58, x - 22, y, INK))
        body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4"/>' % (x, y - 58, x + 22, y, INK))
        body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.4"/>' % (x, y - 58, x, y, INK))
        body.append('<ellipse cx="%d" cy="%d" rx="14" ry="6" fill="%s"/>' % (x, y - 64, INK))
        body.append(text(x, y + 22, label, 11.5, INK, 'middle', 700))
    tripod(*base, 'Base GNSS'); tripod(*rover, 'Receptor sobre el mojón')
    body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.6"/>' % (base[0], base[1] - 30, rover[0], rover[1] - 30, RUST))
    body.append(text((base[0] + rover[0]) / 2, base[1] - 38, 'Línea base: el vector entre las dos antenas', 11, RUST, 'middle', 700))
    # monument in section under the rover
    mx, my = rover[0], rover[1]
    body.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#EFE3C7"/>' % (mx - 120, my, 240, 70))
    body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1"/>' % (mx - 120, my, mx + 120, my, '#8B6B4E'))
    body.append('<polygon points="%d,%d %d,%d %d,%d %d,%d" fill="#D9CDB4" stroke="%s" stroke-width="1"/>'
                % (mx - 14, my - 8, mx + 14, my - 8, mx + 20, my + 60, mx - 20, my + 60, INK2))
    body.append('<rect x="%d" y="%d" width="16" height="4" fill="%s"/>' % (mx - 8, my - 12, GOLD))
    body.append(text(mx + 32, my + 18, 'Mojón de concreto', 10.5, INK2))
    body.append(text(mx + 32, my + 34, 'placa con el punto marcado', 10.5, INK2))
    body.append(text(mx + 32, my + 50, 'en la cara superior', 10.5, INK2))
    body.append(text(30, 30, 'Mojones geodésicos con GNSS', 13, INK, weight=700))
    body.append(text(30, 50, 'Los dos receptores observan los mismos satélites', 11, MUTED))
    body.append(text(30, 68, 'al mismo tiempo; se calcula la posición del mojón', 11, MUTED))
    body.append(text(30, 86, 'respecto de la base', 11, MUTED))
    return svg(W, H, '\n'.join(body), 'Mojones geodésicos: posicionamiento GNSS con base y receptor',
               'Una estación base GNSS y un receptor sobre un mojón de concreto observan los mismos satélites; la línea base '
               'entre ambos da la posición del mojón. Corte del mojón con su placa.')


# ================================================================== 8. BIM (exploded layers, isometric)
def g_bim():
    W, H = 820, 420
    body = []
    c30, s30 = math.cos(math.radians(30)), math.sin(math.radians(30))
    S = 11.0
    def iso(x, y, z, ox, oy):
        return ox + (x - y) * c30 * S, oy - ((x + y) * s30 + z) * S
    Lx, Ly = 16, 10
    layers = [('Arquitectura', '#F4EAD2', INK, 17.0), ('Estructura', '#E7D2BF', RUST, 8.5), ('Instalaciones (MEP)', '#D5E4E6', TEAL, 0.0)]
    ox, oy = 420, 385
    for name, fill, stroke, z in layers:
        pts = [iso(0, 0, z, ox, oy), iso(Lx, 0, z, ox, oy), iso(Lx, Ly, z, ox, oy), iso(0, Ly, z, ox, oy)]
        body.append('<polygon points="%s" fill="%s" stroke="%s" stroke-width="1.2"/>' % (' '.join('%s,%s' % (fmt(a, 1), fmt(b, 1)) for a, b in pts), fill, stroke))
        if name == 'Estructura':
            for gx_ in (0, 5.33, 10.67, 16):
                for gy_ in (0, 5, 10):
                    a, b = iso(gx_, gy_, z, ox, oy)
                    body.append('<rect x="%s" y="%s" width="5" height="5" fill="%s"/>' % (fmt(a - 2.5, 1), fmt(b - 2.5, 1), RUST))
        if name == 'Instalaciones (MEP)':
            path = [iso(1, 2, z, ox, oy), iso(12, 2, z, ox, oy), iso(12, 8, z, ox, oy)]
            body.append('<polyline points="%s" fill="none" stroke="%s" stroke-width="2.2"/>' % (' '.join('%s,%s' % (fmt(a, 1), fmt(b, 1)) for a, b in path), TEAL))
        if name == 'Arquitectura':
            for seg in (((0, 6), (9, 6)), ((9, 0), (9, 10))):
                a = iso(seg[0][0], seg[0][1], z, ox, oy); b = iso(seg[1][0], seg[1][1], z, ox, oy)
                body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2"/>' % (fmt(a[0], 1), fmt(a[1], 1), fmt(b[0], 1), fmt(b[1], 1), INK))
        lx, ly = iso(Lx, 0, z, ox, oy)
        body.append(text(lx + 18, ly + 4, name, 12, stroke, weight=700))
    # vertical alignment guides at two corners
    for x, y in ((0, 0), (Lx, Ly)):
        a = iso(x, y, 0, ox, oy); b = iso(x, y, 17, ox, oy)
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8" stroke-dasharray="3 4"/>' % (fmt(a[0], 1), fmt(a[1], 1), fmt(b[0], 1), fmt(b[1], 1), MUTED))
    # clash: MEP pipe riser crossing a beam position (12, 5)
    a = iso(12, 5, 0, ox, oy); b = iso(12, 5, 8.5, ox, oy)
    body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="2.2"/>' % (fmt(a[0], 1), fmt(a[1], 1), fmt(b[0], 1), fmt(b[1], 1), TEAL))
    body.append('<circle cx="%s" cy="%s" r="11" fill="none" stroke="%s" stroke-width="2"/>' % (fmt(b[0], 1), fmt(b[1], 1), GOLD))
    body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (fmt(b[0] - 11, 1), fmt(b[1], 1), fmt(b[0] - 150, 1), fmt(b[1] + 60, 1), GOLD))
    body.append(text(b[0] - 154, b[1] + 64, 'Interferencia detectada', 11, '#9A6A10', 'end', 700))
    body.append(text(b[0] - 154, b[1] + 79, 'tubería contra viga', 10.5, '#9A6A10', 'end'))
    body.append(text(30, 30, 'Modelado BIM', 13, INK, weight=700))
    body.append(text(30, 50, 'Un solo modelo con arquitectura,', 11, MUTED))
    body.append(text(30, 68, 'estructura e instalaciones', 11, MUTED))
    body.append(text(30, 86, 'coordinados antes de construir', 11, MUTED))
    return svg(W, H, '\n'.join(body), 'Modelado BIM: disciplinas coordinadas en un modelo',
               'Vista isométrica separada de las capas de arquitectura, estructura e instalaciones de un mismo edificio, '
               'con una interferencia entre una tubería y una viga detectada en el modelo.')


# ================================================================== 9. welding (joints + AWS symbols)
def g_soldadura():
    W, H = 820, 380
    body = []
    # --- left: single-V groove butt joint. Groove angle 60° (each bevel 30°),
    #     root opening 3 mm, plate 12 mm. Drawn to scale.
    S = 9.0
    ox, oy = 185, 262
    t, gap, groove = 12.0, 3.0, 60.0
    run = math.tan(math.radians(groove / 2)) * t      # horizontal run of each bevel face
    L = 12.0
    lp = [(-L - gap / 2, 0), (-gap / 2, 0), (-gap / 2 - run, t), (-L - gap / 2, t)]
    rp = [(gap / 2, 0), (L + gap / 2, 0), (L + gap / 2, t), (gap / 2 + run, t)]
    PX = lambda p: ox + p[0] * S
    PY = lambda p: oy - p[1] * S
    P = lambda p: '%s,%s' % (fmt(PX(p), 1), fmt(PY(p), 1))
    for poly in (lp, rp):
        body.append('<polygon points="%s" fill="#E3DDD2" stroke="%s" stroke-width="1.2"/>' % (' '.join(P(p) for p in poly), INK))
    body.append('<polygon points="%s %s %s %s" fill="#E7B78F"/>' % (P((-gap / 2, 0)), P((gap / 2, 0)), P((gap / 2 + run, t)), P((-gap / 2 - run, t))))
    body.append(text(ox, oy + 22, 'Abertura de raíz %s mm' % fmt(gap, 0), 10.5, INK2, 'middle', mono=True))
    body.append(text(ox, PY((0, t)) - 12, 'Ángulo de ranura %d° (bisel de %d° por lado)' % (groove, groove / 2), 10.5, INK2, 'middle', mono=True))
    # plate thickness dimension on the left edge
    xe = PX((-L - gap / 2, 0)) - 12
    body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (fmt(xe, 1), fmt(PY((0, 0)), 1), fmt(xe, 1), fmt(PY((0, t)), 1), INK2))
    for yy in (0, t):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (fmt(xe - 4, 1), fmt(PY((0, yy)), 1), fmt(xe + 4, 1), fmt(PY((0, yy)), 1), INK2))
    body.append(text(xe - 8, (PY((0, 0)) + PY((0, t))) / 2 + 4, '%s mm' % fmt(t, 0), 10.5, INK2, 'end', mono=True))
    body.append(text(ox, 36, 'Junta a tope con bisel en V', 12.5, INK, 'middle', 700))
    # AWS A2.4: the arrow touches the joint; a symbol BELOW the reference line means
    # the weld is on the arrow side. V-groove symbol with the groove angle next to it.
    tip = (PX((gap / 2 + run * 0.6, t)), PY((0, t)))
    rx, ry = 330, 150
    body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.2"/>' % (rx, ry, rx + 120, ry, INK))
    body.append('<line x1="%d" y1="%d" x2="%s" y2="%s" stroke="%s" stroke-width="1.2"/>' % (rx, ry, fmt(tip[0], 1), fmt(tip[1], 1), INK))
    ang = math.atan2(ry - tip[1], rx - tip[0])
    a1 = (tip[0] + 11 * math.cos(ang + 0.35), tip[1] + 11 * math.sin(ang + 0.35))
    a2 = (tip[0] + 11 * math.cos(ang - 0.35), tip[1] + 11 * math.sin(ang - 0.35))
    body.append('<polygon points="%s,%s %s,%s %s,%s" fill="%s"/>' % (fmt(tip[0], 1), fmt(tip[1], 1), fmt(a1[0], 1), fmt(a1[1], 1), fmt(a2[0], 1), fmt(a2[1], 1), INK))
    vx = rx + 62
    body.append('<path d="M%d %d L%d %d L%d %d" fill="none" stroke="%s" stroke-width="1.4"/>' % (vx - 9, ry, vx, ry + 14, vx + 9, ry, INK))
    body.append(text(vx, ry + 28, '60°', 10, INK2, 'middle', mono=True))
    body.append(text(rx + 60, ry + 48, 'Símbolo AWS: ranura en V', 10, MUTED, 'middle'))
    body.append(text(rx + 60, ry + 62, 'del lado de la flecha', 10, MUTED, 'middle'))
    # --- right: T joint, 8 mm fillet welds on both sides of the web
    ox2, oy2 = 610, 262
    S2 = 7.0
    web_t, fl_t, leg = 10.0, 10.0, 8.0
    body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#E3DDD2" stroke="%s" stroke-width="1.2"/>'
                % (fmt(ox2 - 20 * S2, 1), fmt(oy2, 1), fmt(40 * S2, 1), fmt(fl_t * S2, 1), INK))
    body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#E3DDD2" stroke="%s" stroke-width="1.2"/>'
                % (fmt(ox2 - web_t / 2 * S2, 1), fmt(oy2 - 22 * S2, 1), fmt(web_t * S2, 1), fmt(22 * S2, 1), INK))
    for sgn in (-1, 1):
        x_web = ox2 + sgn * web_t / 2 * S2
        body.append('<polygon points="%s,%s %s,%s %s,%s" fill="#E7B78F" stroke="%s" stroke-width="0.8"/>'
                    % (fmt(x_web, 1), fmt(oy2, 1), fmt(x_web + sgn * leg * S2, 1), fmt(oy2, 1), fmt(x_web, 1), fmt(oy2 - leg * S2, 1), INK2))
    body.append(text(ox2 + web_t / 2 * S2 + leg * S2 / 2, oy2 + fl_t * S2 + 16, 'pierna %s mm' % fmt(leg, 0), 10.5, INK2, 'middle', mono=True))
    body.append(text(ox2, 36, 'Junta en T con soldadura de filete', 12.5, INK, 'middle', 700))
    # AWS fillet symbol, both sides: right triangles above and below the reference line,
    # perpendicular leg always on the left, size to the left of the symbol.
    xw = ox2 + web_t / 2 * S2
    tip2 = (xw + leg * S2 * 0.5, oy2 - leg * S2 * 0.5)        # middle of the right fillet face
    rx2, ry2 = 700, 170
    body.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="%s" stroke-width="1.2"/>' % (rx2, ry2, rx2 + 100, ry2, INK))
    body.append('<line x1="%d" y1="%d" x2="%s" y2="%s" stroke="%s" stroke-width="1.2"/>' % (rx2, ry2, fmt(tip2[0], 1), fmt(tip2[1], 1), INK))
    ang2 = math.atan2(ry2 - tip2[1], rx2 - tip2[0])
    b1 = (tip2[0] + 11 * math.cos(ang2 + 0.35), tip2[1] + 11 * math.sin(ang2 + 0.35))
    b2 = (tip2[0] + 11 * math.cos(ang2 - 0.35), tip2[1] + 11 * math.sin(ang2 - 0.35))
    body.append('<polygon points="%s,%s %s,%s %s,%s" fill="%s"/>' % (fmt(tip2[0], 1), fmt(tip2[1], 1), fmt(b1[0], 1), fmt(b1[1], 1), fmt(b2[0], 1), fmt(b2[1], 1), INK))
    fx = rx2 + 52
    body.append('<path d="M%d %d L%d %d L%d %d Z" fill="none" stroke="%s" stroke-width="1.3"/>' % (fx, ry2, fx, ry2 + 12, fx + 12, ry2, INK))
    body.append('<path d="M%d %d L%d %d L%d %d Z" fill="none" stroke="%s" stroke-width="1.3"/>' % (fx, ry2, fx, ry2 - 12, fx + 12, ry2, INK))
    body.append(text(fx - 6, ry2 + 12, '8', 10.5, INK2, 'end', mono=True))
    body.append(text(fx - 6, ry2 - 3, '8', 10.5, INK2, 'end', mono=True))
    body.append(text(rx2 + 50, ry2 + 34, 'Filete a ambos lados', 10, MUTED, 'middle'))
    return svg(W, H, '\n'.join(body), 'Soldadura: junta con bisel en V y junta en T con filete',
               'Corte de una junta a tope de placa de 12 mm con ranura en V de 60 grados (bisel de 30 grados por lado) y abertura '
               'de raíz de 3 mm, con su símbolo AWS, y una junta en T con soldadura de filete de 8 mm a ambos lados y su símbolo.')


# ================================================================== 10. construction (building section)
def g_construccion():
    W, H = 820, 420
    body = []
    S = 38.0
    ox, oy = 200, 300
    X = lambda x: ox + x * S
    Y = lambda z: oy - z * S
    levels = [('NPT +0.00', 0.0), ('Entrepiso +3.00', 3.0), ('Techo +6.00', 6.0)]
    # ground and footings
    body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#EFE3C7"/>' % (X(-1.5), Y(0), 13 * S, 2.3 * S))
    for x in (0, 5, 10):
        body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#D9CDB4" stroke="%s"/>' % (X(x - 0.6), Y(-1.2), 1.2 * S, 0.4 * S, INK2))
        body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#D9CDB4" stroke="%s"/>' % (X(x - 0.15), Y(0), 0.3 * S, 0.8 * S, INK2))
    # columns and slabs
    for x in (0, 5, 10):
        body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#CFC3AB" stroke="%s"/>' % (X(x - 0.15), Y(6), 0.3 * S, 6 * S, INK))
    for _, z in levels[1:]:
        body.append('<rect x="%s" y="%s" width="%s" height="%s" fill="#CFC3AB" stroke="%s"/>' % (X(-0.3), Y(z), 10.6 * S, 0.2 * S, INK))
    body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.6"/>' % (X(-1.5), Y(0), X(11.5), Y(0), '#8B6B4E'))
    for name, z in levels:
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8" stroke-dasharray="6 4"/>' % (X(10.5), Y(z), X(12.4), Y(z), RUST))
        body.append('<polygon points="%s,%s %s,%s %s,%s" fill="%s"/>' % (fmt(X(12.4), 1), fmt(Y(z), 1), fmt(X(12.4) - 6, 1), fmt(Y(z) - 9, 1), fmt(X(12.4) + 6, 1), fmt(Y(z) - 9, 1), RUST))
        body.append(text(X(12.4) + 12, Y(z) - 2, name, 11, RUST, weight=700, mono=True))
    for a, b in ((0, 5), (5, 10)):
        body.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="0.8"/>' % (X(a), Y(-1.9), X(b), Y(-1.9), INK2))
        body.append(text((X(a) + X(b)) / 2, Y(-1.9) - 5, '5.00 m', 10.5, INK2, 'middle', mono=True))
    body.append(text(X(1.2), Y(-0.75), 'Zapata', 10.5, INK2))
    body.append(text(30, 30, 'Corte de una edificación', 13, INK, weight=700))
    body.append(text(30, 50, 'Zapatas, columnas y losas', 11, MUTED))
    body.append(text(30, 68, 'con sus niveles de piso', 11, MUTED))
    body.append(text(30, 86, 'Alturas de piso a piso: 3.00 m', 11, MUTED))
    return svg(W, H, '\n'.join(body), 'Construcción: corte con cimentación, columnas, losas y niveles',
               'Corte de un edificio de dos niveles con zapatas, columnas a 5 metros, losas y los niveles de piso +0.00, +3.00 y +6.00.')


GRAPHICS = {
    'levantamiento-topografico': g_topografico,
    'levantamiento-catastral': g_catastral,
    'control-de-obras': g_control_obra,
    'diseno-vialidad': g_vialidad,
    'costos-presupuestos': g_costos,
    'diseno-arquitectonico': g_arquitectonico,
    'mojones-geodesicos': g_mojones,
    'modelado-bim': g_bim,
    'soldadura': g_soldadura,
    'construccion': g_construccion,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    for name, fn in GRAPHICS.items():
        r = fn()
        doc, info = (r if isinstance(r, tuple) else (r, None))
        path = os.path.join(OUT, name + '.svg')
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(doc)
        print('  %-28s %5.1f KB%s' % (name + '.svg', len(doc.encode()) / 1024, ('  ' + str(info)) if info else ''))


if __name__ == '__main__':
    main()
