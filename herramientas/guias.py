#!/usr/bin/env python3
"""Guías nuevas y página de No Minimal.

Cada guía se arma clonando una guía existente (misma cabecera, estilos, Header/Footer)
y cambiando título, metadatos, schema, cuerpo, preguntas e índice. También añade las
tarjetas al hub /guias, y las URLs al sitemap y al mapa del sitio. Es idempotente.

    python herramientas/guias.py
    python herramientas/prerender.py      # después, para regenerar los snapshots

Reglas del contenido: sin precios, sin clientes inventados, sin citar leyes. Los números
de los ejemplos salen de cálculos que se pueden rehacer (ver cada guía).
"""
import io, os, re, sys, json, html, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'herramientas'))
import prerender as p

SITE = 'https://martinezseguramultiserviciosni.com'
PLANTILLA = 'guia-replanteo-de-obra.html'
HOY = '2026-10-11'
FECHA = '11 de octubre de 2026'
V2 = 0.698737            # m² por vara cuadrada (Nicaragua)
MZ = 10000 * V2          # m² por manzana


def n(x, d=2):
    return ('{:,.%df}' % d).format(x)


def fig(svg, w, h, alt, cap):
    return ('<figure style="margin:8px 0 26px;"><img src="/assets/graficos/%s.svg" width="%d" height="%d" alt="%s" loading="lazy" decoding="async" '
            'style="display:block;width:100%%;height:auto;border:1px solid rgba(43,31,21,0.12);border-radius:12px;">'
            '<figcaption style="font-size:14px;color:#6B5844;line-height:1.55;margin-top:10px;">%s</figcaption></figure>' % (svg, w, h, alt, cap))


# ---------------------------------------------------------------- tabla de medidas
def filas_medidas():
    rows = [('300 v² (lote de 10 × 30 varas)', 300 * V2), ('500 v²', 500 * V2), ('1,000 v²', 1000 * V2),
            ('¼ de manzana (2,500 v²)', MZ / 4), ('½ manzana (5,000 v²)', MZ / 2), ('1 manzana (10,000 v²)', MZ),
            ('5 manzanas', 5 * MZ), ('10 manzanas', 10 * MZ)]
    return ''.join('<tr><td>%s</td><td>%s m²</td><td>%s ha</td></tr>' % (a, n(m), n(m / 10000, 4)) for a, m in rows)


def filas_angulo():
    return ''.join('<tr><td>%d m</td><td>%s cm</td></tr>' % (d, n(d * math.tan(math.radians(0.5)) * 100, 1)) for d in (5, 10, 20, 30))


OBRA_ASIDE = ('¿Tienes una obra en marcha?', 'Mándanos los planos o una descripción y coordinamos las visitas de control según tu cronograma.')
OBRA_CTA = ('¿Necesitas control topográfico en tu obra?', 'Replanteo, niveles y plomos en los 12 departamentos donde trabajamos. Respuesta por WhatsApp en menos de 2 horas.')
TERRENO_ASIDE = ('¿Tienes un terreno en mente?', 'Cuéntanos ubicación y tamaño, y te respondemos con una cotización cerrada.')
TERRENO_CTA = ('¿Necesitas medir tu terreno?', 'Respuesta por WhatsApp en menos de 2 horas, en español o inglés.')

GUIAS = [
 dict(slug='guia-area-de-escritura-vs-terreno', tag='Terrenos', minutos=6, card='levantamiento-catastral',
      titulo='Tu escritura dice 1,000 m²: por qué tu terreno puede medir otra cosa',
      seo='Área de escritura vs. área real del terreno',
      desc='Por qué el área de la escritura no siempre coincide con la del terreno, cuánto cuesta una cerca corrida y qué entrega un levantamiento topográfico.',
      lead='El papel dice una cosa y el terreno, a veces, otra. La diferencia casi nunca es mala fe: es que nadie volvió a medir.',
      servicio=('Levantamiento catastral', '/levantamiento-catastral'), aside=TERRENO_ASIDE, cta=TERRENO_CTA,
      relacionadas=['guia-varas-manzanas-y-metros', 'guia-antes-de-comprar-un-terreno', 'guia-deslinde-problemas-de-linderos'],
      cuerpo='''
<p>Muchas escrituras en Nicaragua describen el terreno con un área redonda y unos linderos del tipo "al norte, propiedad de fulano". Eso alcanza para identificar la propiedad, pero no para saber cuánto mide hoy. En el caso de ejemplo que usamos en esta guía, la escritura decía <strong>1,000 m²</strong> y la medición en campo dio <strong>927.85 m²</strong>: 72.15 m² menos de lo que dice el papel.</p>

<h2 id="por-que">Por qué el papel y el terreno no coinciden</h2>
<ul>
<li><strong>Se midió hace décadas, con cinta y en varas.</strong> Las conversiones y los redondeos de entonces se arrastran en cada traspaso.</li>
<li><strong>La escritura no tiene coordenadas.</strong> Describe colindantes, no puntos; si el vecino cambió, la referencia se perdió.</li>
<li><strong>Las cercas y los mojones se movieron.</strong> Un poste que se repone medio metro adentro, repetido en varios años, cambia el área.</li>
<li><strong>Hubo ventas parciales o calles nuevas</strong> que nunca se reflejaron en un plano.</li>
</ul>

<h2 id="como-se-mide">Cómo se mide de verdad</h2>
<p>Con estación total se miden <strong>ángulos y distancias</strong> a cada vértice del terreno. Con eso se calculan las <strong>coordenadas</strong> de cada esquina, y con las coordenadas, el área exacta. Ya no depende de la memoria de nadie: cualquier topógrafo puede volver al sitio y comprobar los mismos puntos.</p>
''' + fig('levantamiento-catastral', 820, 432,
          'Plano catastral de ejemplo con la distancia y el rumbo de cada lindero y el área del terreno',
          'Otro terreno de ejemplo: cada lindero lleva su distancia y su rumbo, y el área sale de las coordenadas.') + '''
<h2 id="derrotero">El derrotero: cada lado con rumbo y distancia</h2>
<p>El resultado se escribe como un <strong>derrotero</strong>: la lista de lados del terreno, cada uno con su rumbo (la dirección respecto al norte) y su distancia. Es la descripción técnica que acompaña al plano y la que permite replantear los linderos si un día se pierde una cerca.</p>

<h2 id="cerca">Lo que cuesta una cerca corrida</h2>
<p>En el mismo ejemplo, un lindero mide 36.17 m. Si la cerca del vecino quedó <strong>60 cm adentro</strong> de tu terreno a lo largo de ese lado, pierdes 36.17 × 0.60 = <strong>21.70 m²</strong>, unas 31 varas cuadradas que pagaste y no usas. A simple vista, 60 cm no se notan; en el plano, sí.</p>
<div class="g-note"><p><strong>Medir no es pelear.</strong> Un plano con coordenadas le da a los dos vecinos el mismo dato para conversar. Si hay desacuerdo, lee la guía sobre <a href="/guia-deslinde-problemas-de-linderos">deslinde y problemas de linderos</a>.</p></div>

<h2 id="senales">Tres señales de que conviene medir</h2>
<ol>
<li>Tu escritura es vieja y no tiene coordenadas.</li>
<li>Las cercas o los mojones se movieron con los años.</li>
<li>Vas a comprar, heredar, dividir o construir.</li>
</ol>

<h2 id="que-recibes">Qué recibes con el levantamiento</h2>
<ul>
<li>Plano topográfico o catastral.</li>
<li>Derrotero y descripción técnica: rumbos, distancias y colindantes de cada lado.</li>
<li>Área en m², varas cuadradas y manzanas (mira la guía de <a href="/guia-varas-manzanas-y-metros">varas, manzanas y metros</a>).</li>
<li>Coordenadas UTM y un archivo KML para abrir el terreno en Google Earth.</li>
</ul>
<p>Si el área medida no coincide con la escritura, el plano es el documento con el que tu abogado o notario decide qué trámite corresponde.</p>
''',
      faqs=[('¿Qué hago si mi terreno mide menos de lo que dice la escritura?',
             'Lo primero es tener el plano con el área medida. Con ese documento, tu abogado o notario define el trámite que corresponde en tu caso.'),
            ('¿Es normal que haya diferencia?',
             'En escrituras antiguas, sí: se midió con otros métodos y sin coordenadas. Lo importante es conocer la diferencia antes de comprar, vender o construir.'),
            ('¿Necesito que esté el vecino para medir?',
             'No es obligatorio, pero ayuda: si los colindantes ven la medición, es más fácil ponerse de acuerdo sobre el lindero.')]),

 dict(slug='guia-error-de-replanteo', tag='Obra', minutos=6, card='control-de-obras',
      titulo='Un eje corrido 5 cm: cuánto pesa un error de replanteo',
      seo='Error de replanteo: qué pasa si un eje se corre 5 cm',
      desc='Qué pasa cuando una columna queda 5 cm fuera de eje: 25 % más de presión en un borde de la zapata, y cómo medio grado de error son 17.5 cm a 20 m.',
      lead='"Son solo cinco centímetros" es la frase más cara de una obra. Aquí están las cuentas, para que decidas con números.',
      servicio=('Control de obras', '/control-de-obras'), aside=OBRA_ASIDE, cta=OBRA_CTA,
      relacionadas=['guia-replanteo-de-obra', 'guia-control-topografico-de-obra', 'guia-topografia-antes-de-construir'],
      cuerpo='''
<p>Replantear es pasar el plano al terreno. Si un eje queda corrido unos centímetros, la columna sigue en pie y a simple vista nada parece mal. El problema está abajo, en cómo la zapata reparte la carga sobre el suelo.</p>

<h2 id="excentricidad">5 cm fuera de eje: 25 % más de presión en un borde</h2>
<p>Una zapata cuadrada reparte la carga de forma pareja solo si la columna cae en su centro. Si la columna queda desplazada una distancia <em>e</em>, un borde se carga más y el opuesto, menos. En una zapata de ancho <em>B</em>, el aumento en el borde más cargado es de <strong>6 × e ÷ B</strong>.</p>
<p>Con una zapata de 1.20 m y una columna 5 cm fuera del centro: 6 × 0.05 ÷ 1.20 = 0.25. Ese borde trabaja con <strong>un 25 % más de presión</strong> que la que calculó el diseñador, y el otro con un 25 % menos.</p>
<div class="g-note"><p><strong>Esto no significa que la zapata vaya a fallar.</strong> Significa que trabaja distinto a como se diseñó. Quien decide si se acepta, se refuerza o se corrige es el ingeniero estructural, y para decidir necesita saber cuánto se corrió.</p></div>
''' + fig('control-de-obras', 820, 462,
          'Replanteo de ejes y zapatas con estación total y control de niveles contra un banco de nivel',
          'Replanteo con estación total: cada centro de zapata se marca desde un punto de control, no desde la zapata anterior.') + '''
<h2 id="angulo">Medio grado de error: 17.5 cm a 20 metros</h2>
<p>El otro error típico es de ángulo. Una escuadra que no está a 90° exactos casi no se nota cerca de la esquina, pero crece con la distancia:</p>
<div class="g-scroll"><table class="g-table">
<thead><tr><th>Distancia desde la esquina</th><th>Corrimiento con 0.5° de error</th></tr></thead>
<tbody>''' + filas_angulo() + '''</tbody></table></div>
<p>Por eso los ejes largos se trazan con estación total y no con cinta y escuadra de carpintero: cada punto se mide desde la referencia, y el error no se acumula.</p>

<h2 id="diagonales">La prueba de las diagonales</h2>
<p>Un rectángulo bien trazado tiene las <strong>dos diagonales iguales</strong>. Si una mide más que la otra, la figura es un romboide y alguna esquina no está a 90°. Es la comprobación más barata que existe y se hace antes de excavar.</p>
<p>Para sacar una escuadra solo con cinta sirve la regla <strong>3-4-5</strong>: 3 m en un lado, 4 m en el otro, y la diagonal debe dar 5.00 m exactos (3² + 4² = 5²). Funciona bien en tramos cortos.</p>

<h2 id="revisar">Qué revisar antes de colar</h2>
<ul>
<li>Ejes y distancias entre columnas.</li>
<li>Diagonales iguales.</li>
<li>Nivel del fondo de zapatas.</li>
<li>Plomo del acero y de la formaleta.</li>
<li>Recubrimiento y amarres.</li>
</ul>
<p>Lo que se cuela mal, se demuele. Lo que se revisa, se corrige en minutos. En la guía de <a href="/guia-replanteo-de-obra">replanteo de obra paso a paso</a> está el orden completo.</p>
''',
      faqs=[('¿Un corrimiento de 5 cm siempre es grave?',
             'Depende del elemento y de la tolerancia que fije el diseñador. Lo que sí es seguro es que hay que medirlo e informarlo antes de colar, para que el ingeniero decida.'),
            ('¿Se puede corregir después de colar?',
             'A veces, pero es caro: puede implicar ampliar la zapata, reforzar o demoler. La solución la define el ingeniero estructural.'),
            ('¿Sirve trazar con cinta y escuadra?',
             'En obras pequeñas y tramos cortos, sí, comprobando con la regla 3-4-5 y las diagonales. En ejes largos el error se acumula y conviene estación total.')]),

 dict(slug='guia-varas-manzanas-y-metros', tag='Medidas', minutos=5, card='levantamiento-catastral',
      titulo='Varas, manzanas y metros: cómo convertir medidas de terreno en Nicaragua',
      seo='Cuánto mide una manzana: varas, metros y hectáreas',
      desc='Cuántos metros tiene una manzana y una vara cuadrada en Nicaragua, con tabla de conversión a metros cuadrados y hectáreas y ejemplos resueltos.',
      lead='La escritura está en varas, el anuncio en manzanas y el plano en metros. Estas son las equivalencias que usamos en Nicaragua.',
      servicio=('Levantamiento topográfico', '/levantamiento-topografico'), aside=TERRENO_ASIDE, cta=TERRENO_CTA,
      relacionadas=['guia-area-de-escritura-vs-terreno', 'guia-cuanto-cuesta-un-levantamiento-topografico', 'guia-documentos-para-medir-un-terreno'],
      cuerpo='''
<p>En Nicaragua conviven tres formas de decir cuánto mide un terreno. Las escrituras antiguas hablan de <strong>varas cuadradas</strong>, las fincas se venden por <strong>manzanas</strong> y los planos y el catastro trabajan en <strong>metros cuadrados</strong>. Convertir mal entre ellas es una de las formas más comunes de pagar de más.</p>

<h2 id="equivalencias">Las equivalencias</h2>
<ul>
<li><strong>1 vara</strong> = 0.8359 m.</li>
<li><strong>1 vara cuadrada (v²)</strong> = ''' + n(V2, 6) + ''' m².</li>
<li><strong>1 manzana (mz)</strong> = 10,000 v² = ''' + n(MZ) + ''' m².</li>
<li><strong>1 hectárea (ha)</strong> = 10,000 m² = ''' + n(10000 / MZ, 4) + ''' manzanas.</li>
<li><strong>1 m²</strong> = ''' + n(1 / V2, 4) + ''' v².</li>
</ul>
<p>Una manzana es, entonces, un poco menos de 7,000 m², o cerca de siete décimas de hectárea.</p>

<h2 id="tabla">Tabla de conversión</h2>
<div class="g-scroll"><table class="g-table">
<thead><tr><th>Medida</th><th>Metros cuadrados</th><th>Hectáreas</th></tr></thead>
<tbody>''' + filas_medidas() + '''</tbody></table></div>

<h2 id="ejemplos">Dos ejemplos</h2>
<h3>De varas a metros</h3>
<p>Una escritura dice 1,430 v². En metros: 1,430 × ''' + n(V2, 6) + ''' = <strong>''' + n(1430 * V2) + ''' m²</strong>.</p>
<h3>De manzanas a hectáreas</h3>
<p>Un anuncio ofrece 12 manzanas. En hectáreas: 12 × ''' + n(MZ / 10000, 6) + ''' = <strong>''' + n(12 * MZ / 10000) + ''' ha</strong>, es decir ''' + n(12 * MZ, 1) + ''' m².</p>

<h2 id="cuidado">Con qué tener cuidado</h2>
<ul>
<li><strong>Vara lineal no es vara cuadrada.</strong> Un lote de 10 × 30 varas tiene 300 v², no 30.</li>
<li><strong>La manzana no mide igual en todos los países.</strong> Estas equivalencias son las que se usan en Nicaragua; no las apliques a un terreno en otro país sin revisar.</li>
<li><strong>El área de la escritura es un dato de partida, no una medición.</strong> Si la cifra importa, hay que medir. Lo explicamos en <a href="/guia-area-de-escritura-vs-terreno">por qué tu terreno puede medir otra cosa</a>.</li>
</ul>
<p>Nuestros planos entregan el área en las tres unidades. Y el <a href="/cotizador">cotizador</a> acepta el tamaño en m², varas cuadradas, manzanas o hectáreas.</p>
''',
      faqs=[('¿Cuántos metros cuadrados tiene una manzana en Nicaragua?', 'Una manzana tiene 10,000 varas cuadradas, que equivalen a %s m².' % n(MZ)),
            ('¿Cuántas manzanas tiene una hectárea?', 'Una hectárea son 10,000 m², que equivalen a %s manzanas.' % n(10000 / MZ, 4)),
            ('¿Cuánto mide una vara cuadrada?', 'Una vara cuadrada equivale a %s m². La vara lineal mide 0.8359 m.' % n(V2, 6))]),

 dict(slug='guia-como-leer-un-plano-topografico', tag='Conceptos', minutos=6, card='levantamiento-topografico',
      titulo='Cómo leer un plano topográfico: curvas de nivel, cotas y escala',
      seo='Cómo leer un plano topográfico y sus curvas de nivel',
      desc='Qué significan las curvas de nivel, las cotas, la escala y el norte en un plano topográfico, y cómo saber hacia dónde baja el terreno.',
      lead='Un plano topográfico es el terreno visto desde arriba, con la altura dibujada. Con cuatro ideas se lee completo.',
      servicio=('Levantamiento topográfico', '/levantamiento-topografico'), aside=TERRENO_ASIDE, cta=TERRENO_CTA,
      relacionadas=['guia-levantamiento-topografico-vs-catastral', 'guia-topografia-antes-de-construir', 'guia-varas-manzanas-y-metros'],
      cuerpo='''
<p>Cuando recibes un plano topográfico ves líneas curvas, números pequeños y una flecha. Todo eso responde a tres preguntas: <strong>dónde está cada cosa, a qué altura y hacia dónde baja el terreno</strong>.</p>
''' + fig('levantamiento-topografico', 820, 420,
          'Plano topográfico de ejemplo con curvas de nivel cada metro y la cota de cada punto medido con estación total',
          'Plano de ejemplo de un terreno de 110 × 58 m: curvas de nivel cada metro, curvas maestras cada cinco y la cota de cada punto medido.') + '''
<h2 id="curvas">Curvas de nivel</h2>
<p>Una <strong>curva de nivel</strong> une todos los puntos que están a la misma altura. Si caminaras sobre una de ellas, no subirías ni bajarías. La diferencia de altura entre una curva y la siguiente es siempre la misma y se llama <strong>equidistancia</strong>: en el plano de ejemplo es de 1 m.</p>
<p>Cada cierto número de curvas hay una más gruesa con su altura escrita: es la <strong>curva maestra</strong> (en el ejemplo, cada 5 m). Sirve para ubicarse rápido.</p>

<h2 id="pendiente">Juntas o separadas: la pendiente</h2>
<ul>
<li><strong>Curvas muy juntas:</strong> el terreno sube o baja rápido. Es una ladera.</li>
<li><strong>Curvas separadas:</strong> el terreno es casi plano.</li>
</ul>
<p>La pendiente se calcula dividiendo la diferencia de altura entre la distancia. Si entre dos puntos separados 25 m hay 2 m de desnivel, la pendiente es 2 ÷ 25 = 0.08, es decir <strong>8 %</strong>.</p>

<h2 id="agua">Hacia dónde corre el agua</h2>
<p>El agua baja siempre cruzando las curvas en ángulo recto, de la cota mayor a la menor. Donde las curvas forman una V que apunta hacia las cotas altas hay una <strong>vaguada</strong>: por ahí corre el agua cuando llueve. Donde forman curvas cerradas con la cota mayor en el centro hay una <strong>loma</strong>.</p>
<div class="g-note"><p><strong>Antes de ubicar la casa, mira por dónde pasa el agua.</strong> Es más barato mover el diseño unos metros que construir un drenaje para corregirlo.</p></div>

<h2 id="cotas">Cotas</h2>
<p>Los números junto a los puntos son <strong>cotas</strong>: la altura medida en ese lugar exacto. Pueden estar referidas al nivel del mar o a un punto de la obra al que se le asignó una altura (por ejemplo 100.000). Lo que importa para diseñar es la diferencia entre ellas.</p>

<h2 id="escala">Escala y norte</h2>
<p>La <strong>escala</strong> dice cuánto mide en la realidad lo que ves en el papel. A escala 1:200, un centímetro del plano son 2 metros en el terreno. La barra gráfica sirve aunque el plano se imprima en otro tamaño.</p>
<p>La <strong>flecha de norte</strong> orienta el plano. Con ella el arquitecto decide hacia dónde abren las ventanas y dónde pega el sol de la tarde.</p>

<h2 id="para-que">Para qué sirve todo esto</h2>
<ul>
<li>Ubicar la construcción donde menos tierra haya que mover.</li>
<li>Definir niveles de piso, rampas y gradas.</li>
<li>Calcular volúmenes de corte y relleno.</li>
<li>Diseñar el drenaje pluvial y la salida de aguas.</li>
</ul>
''',
      faqs=[('¿Cada cuánto deben ir las curvas de nivel?',
             'Depende del terreno y del uso. Para diseñar una vivienda suele trabajarse con curvas cada 0.50 m o cada 1 m; tu arquitecto o ingeniero define cuál necesita.'),
            ('¿Qué diferencia hay con un plano catastral?',
             'El catastral define linderos y área para trámites legales. El topográfico añade las alturas, que es lo que se necesita para diseñar y construir.'),
            ('¿Puedo ver el plano en mi teléfono?',
             'Sí. Además del plano entregamos las coordenadas y un archivo KML para abrir el terreno en Google Earth.')]),

 dict(slug='guia-topografia-antes-de-construir', tag='Obra', minutos=6, card='levantamiento-topografico',
      titulo='Topografía antes de construir tu casa: qué pedir y en qué orden',
      seo='Topografía antes de construir: qué pedir y en qué orden',
      desc='Qué trabajos de topografía necesita una casa, del terreno a la obra: linderos, curvas de nivel, replanteo y control antes de cada colado.',
      lead='Una casa pasa por la topografía cuatro veces. Saltarse una suele costar más que hacerlas todas.',
      servicio=('Control de obras', '/control-de-obras'), aside=OBRA_ASIDE, cta=OBRA_CTA,
      relacionadas=['guia-como-leer-un-plano-topografico', 'guia-replanteo-de-obra', 'guia-error-de-replanteo'],
      cuerpo='''
<p>La topografía no es un solo trabajo que se hace al principio. Acompaña la obra en cuatro momentos, y cada uno responde a una pregunta distinta. Este es el orden.</p>

<div class="g-scroll"><table class="g-table">
<thead><tr><th>Momento</th><th>Qué se pide</th><th>Qué responde</th></tr></thead>
<tbody>
<tr><td><strong>Antes de comprar o diseñar</strong></td><td>Levantamiento de linderos</td><td>¿Cuánto mide y dónde termina mi terreno?</td></tr>
<tr><td><strong>Antes de diseñar</strong></td><td>Levantamiento topográfico con curvas de nivel</td><td>¿Qué forma tiene y hacia dónde baja?</td></tr>
<tr><td><strong>Antes de excavar</strong></td><td>Replanteo de ejes y niveles</td><td>¿Dónde va exactamente cada cosa?</td></tr>
<tr><td><strong>Antes de cada colado</strong></td><td>Verificación de ejes, niveles y plomos</td><td>¿Quedó como dice el plano?</td></tr>
</tbody></table></div>

<h2 id="linderos">1. Saber dónde termina el terreno</h2>
<p>Antes de dibujar una sola pared hay que conocer los linderos reales y el área. Construir pegado a una cerca que no está en el lindero es un problema que aparece años después. Si además vas a hacer un trámite, pide el levantamiento catastral; en la guía de <a href="/guia-levantamiento-topografico-vs-catastral">topográfico vs. catastral</a> explicamos la diferencia.</p>

<h2 id="curvas">2. Conocer la forma del terreno</h2>
<p>El arquitecto necesita un <strong>plano con curvas de nivel</strong> para decidir dónde ubicar la casa, a qué altura queda el piso y por dónde sale el agua. Diseñar sobre un terreno "más o menos plano" termina en rellenos, muros de contención o gradas que nadie presupuestó. Si no sabes interpretarlo, mira <a href="/guia-como-leer-un-plano-topografico">cómo leer un plano topográfico</a>.</p>
<p>Pide los dos levantamientos juntos si puedes: hacerlos en una sola visita cuesta menos que en dos.</p>

<h2 id="replanteo">3. Llevar el plano al terreno</h2>
<p>Con el diseño listo, el <strong>replanteo</strong> marca en el sitio los ejes, las zapatas y los niveles. Aquí se colocan los puntos de control y el banco de nivel que se usarán durante toda la obra. El detalle está en <a href="/guia-replanteo-de-obra">replanteo de obra paso a paso</a>.</p>

<h2 id="control">4. Verificar antes de colar</h2>
<p>Lo que se revisa antes del concreto se corrige moviendo un hilo. Lo que se descubre después, se demuele. En una casa bastan tres visitas: antes de excavar, antes de colar fundaciones y antes de la losa. En <a href="/guia-error-de-replanteo">cuánto pesa un error de replanteo</a> están las cuentas de por qué importa.</p>

<h2 id="suelo">¿Y el estudio de suelo?</h2>
<p>No es topografía, pero va en el mismo momento que el levantamiento: le dice al ingeniero estructural cómo es el terreno por dentro para dimensionar las fundaciones. Si tu proyecto lo necesita, lo define el ingeniero.</p>

<h2 id="al-final">Al terminar</h2>
<p>Un levantamiento de lo construido deja registrado dónde quedó todo: útil para escriturar, ampliar o vender.</p>
''',
      faqs=[('¿Puedo construir sin levantamiento topográfico?',
             'Se puede, pero se diseña a ciegas: los niveles, los rellenos y el drenaje se resuelven en obra, que es donde más cuesta.'),
            ('¿Qué pido primero, el catastral o el topográfico?',
             'Si puedes, los dos en la misma visita. El catastral define linderos y área; el topográfico agrega las alturas para diseñar.'),
            ('¿Cuántas visitas de control necesita una casa?',
             'Como mínimo tres: antes de excavar, antes de colar fundaciones y antes de la losa.')]),
]

EXISTENTES = {
    'guia-cuanto-cuesta-un-levantamiento-topografico': ('Precios', '¿Cuánto cuesta un levantamiento topográfico en Nicaragua?',
        'Qué define el precio de un levantamiento topográfico en Nicaragua: tamaño, forma, vegetación, acceso y entregables.'),
    'guia-levantamiento-topografico-vs-catastral': ('Conceptos', 'Levantamiento topográfico vs. catastral: ¿cuál necesitas?',
        'Diferencia entre levantamiento topográfico y catastral en Nicaragua, y cuál pedir según lo que vayas a hacer.'),
    'guia-documentos-para-medir-un-terreno': ('Documentos', 'Documentos para medir un terreno en Nicaragua',
        'Escritura, identificación, planos anteriores y colindantes: qué tener listo antes del levantamiento.'),
    'guia-antes-de-comprar-un-terreno': ('Compra', 'Antes de comprar un terreno en Nicaragua: qué revisar',
        'Área contra escritura, linderos, colindantes, acceso, servidumbres y pendientes: la lista de un topógrafo.'),
    'guia-deslinde-problemas-de-linderos': ('Linderos', 'Problemas de linderos con el vecino: qué es un deslinde',
        'Qué es un deslinde, cuándo lo necesitas y cómo se hace: medición de linderos, colindantes, mojones y plano.'),
    'guia-control-topografico-de-obra': ('Obra', 'Control topográfico de obra: qué es, qué incluye y cuándo contratarlo',
        'En qué se diferencia de la supervisión, qué se controla en cada etapa y cuándo conviene contratarlo.'),
    'guia-replanteo-de-obra': ('Obra', 'Replanteo de obra paso a paso',
        'Puntos de control, banco de nivel, niveletas, trazo de ejes, diagonales, niveles y revisión antes de colar.'),
}

# ---------------------------------------------------------------- No Minimal
NM = 'https://nominimal.com/'
ENSAYOS = [
    ('Serie 01 · Temas de arquitectura', [
        ('El ladrillo como lengua materna', 'El bloque, el tolete y el tabique: el idioma con que construimos nuestras casas.', '19 min · 10 capítulos', 'ladrillo.html'),
        ('Color, luz y sombra', 'La luz nunca es neutral y el color nunca es solo decoración.', '57 min · 19 capítulos', 'color.html'),
        ('Por qué América Latina no puede ser minimalista', 'Historia, clima, cultura y economía de una arquitectura propia.', '27 min · 10 capítulos', 'minimalista.html'),
        ('Sombra, agua y patio', 'El vacío central, el agua y la sombra como un solo sistema.', '45 min · 16 capítulos', 'patio.html'),
    ]),
    ('Serie 02 · Tesis de divulgación', [
        ('Construir bien en Latinoamérica', 'Terreno, riesgos, materiales, clima, costos por m² y autoconstrucción por etapas.', '41 min · 18 capítulos', 'construir.html'),
        ('Lo que el color nos hace', 'Lo comprobado y lo exagerado sobre el color y la luz en el cuerpo, la mente, la casa y la ciudad.', '53 min · 16 capítulos', 'psicologia-del-color.html'),
    ]),
]


def rd(f):
    raw = io.open(os.path.join(ROOT, f), encoding='utf-8', newline='').read()
    return raw.replace('\r\n', '\n'), ('\r\n' if '\r\n' in raw else '\n')


def wr(f, s, nl='\r\n'):
    io.open(os.path.join(ROOT, f), 'w', encoding='utf-8', newline='').write(s.replace('\n', nl))


def esc(s):
    return html.escape(s, quote=True)


def ld(obj):
    return '<script type="application/ld+json">\n%s\n</script>' % json.dumps(obj, ensure_ascii=False, separators=(',', ':'))


def sub1(pat, rep, s, flags=re.S):
    out, k = re.subn(pat, lambda m: rep if isinstance(rep, str) else rep(m), s, count=1, flags=flags)
    assert k == 1, pat[:70]
    return out


def faq_html(faqs):
    it = ''.join('<details class="faq-item" style="background:#FFFDF6;border:1px solid rgba(43,31,21,0.12);border-radius:10px;padding:2px 22px;">'
                 '<summary style="font-family:\'Bricolage Grotesque\',sans-serif;font-weight:700;font-size:16.5px;color:#2B1F15;padding:18px 34px 18px 0;position:relative;min-height:24px;">%s'
                 '<span aria-hidden="true" class="faq-plus" style="position:absolute;right:2px;top:26px;color:#B0512B;font-weight:800;font-size:20px;">+</span></summary>'
                 '<p style="font-size:15.5px;color:#4E3D2C;line-height:1.6;margin:0 0 20px;">%s</p></details>' % (esc(q), esc(a)) for q, a in faqs)
    return '<h2 id="preguntas">Preguntas frecuentes</h2>\n<div style="display:flex;flex-direction:column;gap:12px;">' + it + '</div>\n'


def cabecera(t, slug, title, desc, og_title, card, alt, schemas):
    """Head shared by guides and the No Minimal page."""
    url = SITE + '/' + slug
    assert len(title) <= 60 and len(desc) <= 160, (slug, len(title), len(desc))
    t = sub1(r'<title>.*?</title>', '<title>%s</title>' % esc(title), t)
    t = sub1(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % esc(desc), t)
    t = t.replace(SITE + '/guia-replanteo-de-obra', url)
    for prop in ('property="og:title"', 'name="twitter:title"'):
        t = sub1(r'<meta %s content="[^"]*">' % prop, '<meta %s content="%s">' % (prop, esc(og_title)), t)
    for prop in ('property="og:description"', 'name="twitter:description"'):
        t = sub1(r'<meta %s content="[^"]*">' % prop, '<meta %s content="%s">' % (prop, esc(desc)), t)
    t = t.replace(SITE + '/assets/social/control-de-obras.jpg', SITE + '/assets/social/%s.jpg' % card)
    t = sub1(r'<meta property="og:image:alt" content="[^"]*">', '<meta property="og:image:alt" content="%s">' % esc(alt), t)
    blocks = list(re.finditer(r'<script type="application/ld\+json">.*?</script>', t, re.S))
    assert len(blocks) == 3      # the template guide carries Article, Breadcrumb and FAQ
    t = t[:blocks[0].start()] + '\n'.join(ld(x) for x in schemas) + t[blocks[2].end():]
    return t


def tarjeta(slug, tag, titulo, desc, h='h3'):
    return '<a class="g-card" href="/%s"><span class="g-tag">%s</span><%s>%s</%s><p>%s</p></a>' % (slug, esc(tag), h, esc(titulo), h, esc(desc))


def info(slug):
    for g in GUIAS:
        if g['slug'] == slug: return g['tag'], g['titulo'], g['desc']
    return EXISTENTES[slug]


def guia(t, g):
    slug, url = g['slug'], SITE + '/' + g['slug']
    crumbs = [('Inicio', SITE + '/'), ('Guías', SITE + '/guias'), (g['titulo'], url)]
    org = {'@type': 'Organization', 'name': 'Martínez-Segura Multiservicios', 'url': SITE + '/'}
    schemas = [
        {'@context': 'https://schema.org', '@type': 'Article', 'headline': g['titulo'], 'description': g['desc'], 'inLanguage': 'es-NI',
         'datePublished': HOY, 'dateModified': HOY, 'wordCount': len(re.sub(r'<[^>]+>', ' ', g['cuerpo']).split()),
         'image': SITE + '/assets/social/%s.jpg' % g['card'], 'mainEntityOfPage': url, 'author': org,
         'publisher': dict(org, logo={'@type': 'ImageObject', 'url': SITE + '/assets/favicon-512.png'})},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': a, 'item': b} for i, (a, b) in enumerate(crumbs)]},
        {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': [
            {'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in g['faqs']]},
    ]
    t = cabecera(t, slug, g['seo'], g['desc'], g['titulo'], g['card'], g['titulo'], schemas)
    t = sub1(r'(<span aria-current="page"[^>]*>)[^<]*(</span></nav>)', lambda m: m.group(1) + esc(g['titulo']) + m.group(2), t)
    t = sub1(r'>Guía · Obra</p>', '>Guía · %s</p>' % esc(g['tag']), t)
    t = sub1(r'(<h1 [^>]*>)[^<]*(</h1>)', lambda m: m.group(1) + esc(g['titulo']) + m.group(2), t)
    t = sub1(r'(</h1>\s*<p [^>]*>)[^<]*(</p>)', lambda m: m.group(1) + g['lead'] + m.group(2), t)
    t = sub1(r'<p class="g-meta">[^<]*</p>', '<p class="g-meta">Lectura de %d min · Actualizado el %s</p>' % (g['minutos'], FECHA), t)
    cuerpo = g['cuerpo'].strip()
    sn, sp = g['servicio']
    art = ('<article class="g-body">\n' + cuerpo + '\n' + faq_html(g['faqs']) +
           '\n      <p style="margin-top:34px;font-size:15px;color:#6B5844;">Servicio relacionado: <a href="%s">%s →</a></p>\n    </article>' % (sp, esc(sn)))
    t = sub1(r'<article class="g-body">.*?</article>', art, t)
    toc = ''.join('<li><a href="#%s">%s</a></li>' % (i, x) for i, x in re.findall(r'<h2 id="([^"]+)">([^<]+)</h2>', cuerpo + '<h2 id="preguntas">Preguntas frecuentes</h2>'))
    t = sub1(r'(<nav class="g-toc"[^>]*><p>En esta guía</p><ol>).*?(</ol></nav>)', lambda m: m.group(1) + toc + m.group(2), t)
    t = sub1(r'(<div class="g-cta">\s*<p [^>]*>)[^<]*(</p>\s*<p [^>]*>)[^<]*(</p>)',
             lambda m: m.group(1) + g['aside'][0] + m.group(2) + g['aside'][1] + m.group(3), t)
    rel = ''.join(tarjeta(s, *info(s)) for s in g['relacionadas'])
    t = sub1(r'(<section aria-label="Más guías".*?<div style="display:grid;[^"]*">).*?(</div>\s*</section>)', lambda m: m.group(1) + rel + m.group(2), t)
    t = sub1(r'(<section aria-label="Contacto".*?<h2 [^>]*>)[^<]*(</h2>\s*<p [^>]*>)[^<]*(</p>)',
             lambda m: m.group(1) + g['cta'][0] + m.group(2) + g['cta'][1] + m.group(3), t)
    return t


def no_minimal(t):
    slug, url = 'no-minimal', SITE + '/no-minimal'
    title = 'No Minimal | Ensayos de Arquitectura Latinoamericana'
    desc = 'No Minimal: seis ensayos y tesis del Arq. Orelio Martínez sobre arquitectura latinoamericana: ladrillo, luz, color, patio y cómo construir bien.'
    crumbs = [('Inicio', SITE + '/'), ('Arquitectura', SITE + '/arquitectura'), ('No Minimal', url)]
    orelio = {'@type': 'Person', '@id': SITE + '/#orelio', 'name': 'Orelio Martínez', 'jobTitle': 'Arquitecto e ingeniero',
              'url': SITE + '/arquitectura', 'sameAs': [NM]}
    schemas = [
        {'@context': 'https://schema.org', '@type': 'CollectionPage', 'name': 'No Minimal', 'description': desc, 'url': url, 'inLanguage': 'es',
         'author': orelio, 'about': 'Arquitectura latinoamericana',
         'hasPart': [{'@type': 'Article', 'headline': a, 'description': b, 'url': NM + u, 'author': {'@id': SITE + '/#orelio'}}
                     for _, lst in ENSAYOS for a, b, _, u in lst]},
        {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': a, 'item': b} for i, (a, b) in enumerate(crumbs)]},
    ]
    t = cabecera(t, slug, title, desc, 'No Minimal: arquitectura latinoamericana sin miedo al color', 'general',
                 'No Minimal, ensayos de arquitectura latinoamericana del Arq. Orelio Martínez', schemas)
    t = sub1(r'<meta property="og:type" content="[^"]*">', '<meta property="og:type" content="website">', t)
    t = sub1(r'(<a href=")/guias("[^>]*>)Guías(</a>)', lambda m: m.group(1) + '/arquitectura' + m.group(2) + 'Arquitectura' + m.group(3), t)
    t = sub1(r'(<span aria-current="page"[^>]*>)[^<]*(</span></nav>)', lambda m: m.group(1) + 'No Minimal' + m.group(2), t)
    t = sub1(r'>Guía · Obra</p>', '>Investigación · Arq. Orelio Martínez</p>', t)
    t = sub1(r'(<h1 [^>]*>)[^<]*(</h1>)', lambda m: m.group(1) + 'No Minimal: arquitectura latinoamericana sin miedo al color' + m.group(2), t)
    t = sub1(r'(</h1>\s*<p [^>]*>)[^<]*(</p>)', lambda m: m.group(1) +
             'Además de proyectar, escribimos sobre lo que construimos. No Minimal reúne los ensayos y tesis del Arq. Orelio Martínez sobre cómo se construye y se habita en América Latina.' + m.group(2), t)
    t = sub1(r'<p class="g-meta">[^<]*</p>',
             '<div style="margin-top:26px;"><a href="%s" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;gap:9px;background:#F2A81E;color:#3A1D0C;'
             'text-decoration:none;border-radius:8px;padding:14px 26px;font-weight:800;font-size:15px;min-height:48px;" style-hover="background:#FFB93D;">Entrar a No Minimal ↗</a></div>' % NM, t)
    series = ''
    for nombre, lst in ENSAYOS:
        cards = ''.join('<a class="g-card" href="%s%s" target="_blank" rel="noopener"><span class="g-tag">%s</span><h3>%s</h3><p>%s</p></a>'
                        % (NM, u, esc(meta), esc(a), esc(b)) for a, b, meta, u in lst)
        series += ('<section style="margin-top:44px;"><h2 style="font-family:\'Bricolage Grotesque\',sans-serif;font-weight:800;font-size:clamp(21px,2.4vw,26px);color:#2B1F15;margin:0 0 16px;">%s</h2>'
                   '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:16px;">%s</div></section>' % (esc(nombre), cards))
    cuerpo = ('''<div class="g-wrap" style="padding-top:clamp(30px,4.5vw,48px);">
  <div class="g-body" style="max-width:760px;">
    <p>No Minimal es una plataforma propia, escrita y firmada por el Arq. Orelio Martínez. Recorre 19 países, de México a Brasil, y defiende una idea: la arquitectura de la región no es una versión incompleta de estéticas ajenas, sino una expresión propia, coherente y legítima.</p>
    <blockquote style="margin:26px 0;padding:22px 26px;background:#17333D;border-radius:12px;color:#F7EFDC;">
      <p style="font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:clamp(22px,3vw,30px);line-height:1.15;margin:0;">América Latina no puede ser minimalista.</p>
      <p style="font-size:16px;line-height:1.6;color:#C6D5D9;margin:12px 0 0;">El minimalismo es una neutralidad importada. Aquí se construyó desde la necesidad, la mezcla y la improvisación: el color no es exceso, es vida, memoria e identidad.</p>
      <p style="font-size:13.5px;color:#9FB2B7;margin:12px 0 0;">Tesis rectora de No Minimal</p>
    </blockquote>
  </div>
''' + series + '''
  <section style="margin-top:44px;max-width:760px;">
    <h2 style="font-family:'Bricolage Grotesque',sans-serif;font-weight:800;font-size:clamp(21px,2.4vw,26px);color:#2B1F15;margin:0 0 12px;">Qué tiene que ver con tu proyecto</h2>
    <p style="font-size:17px;line-height:1.72;color:#34261A;margin:0 0 16px;">Esa mirada es la que llevamos al diseño: materiales de la región, la luz y la sombra tratadas como parte del proyecto, y patios, corredores y aleros que enfrían la casa sin gastar energía. No es teoría aparte; es el criterio con el que dibujamos.</p>
    <p style="font-size:17px;line-height:1.72;color:#34261A;margin:0;">Mira el estudio en <a href="/arquitectura">Martínez-Segura Arquitectura</a> o el servicio de <a href="/diseno-arquitectonico">diseño arquitectónico y estructural</a>.</p>
  </section>
</div>
''')
    a = t.index('<div class="g-wrap" style="padding-top:clamp(30px,4.5vw,48px);">')
    b = t.index('<section aria-label="Contacto"')
    t = t[:a] + cuerpo + t[b:]
    t = sub1(r'(<section aria-label="Contacto".*?<h2 [^>]*>)[^<]*(</h2>\s*<p [^>]*>)[^<]*(</p>)',
             lambda m: m.group(1) + '¿Quieres diseñar con ese criterio?' + m.group(2) +
             'Cuéntanos tu proyecto: casa, remodelación u oficina. Respuesta por WhatsApp en menos de 2 horas.' + m.group(3), t)
    return t


def main():
    if hasattr(sys.stdout, 'reconfigure'): sys.stdout.reconfigure(encoding='utf-8')
    raw, nl = rd(PLANTILLA)
    base = p.strip(raw.replace('\n', nl)).replace('\r\n', '\n')
    for g in GUIAS:
        wr(g['slug'] + '.html', guia(base, g), nl)
        print('  %-44s %4d palabras' % (g['slug'] + '.html', len(re.sub(r'<[^>]+>', ' ', g['cuerpo']).split())))
    wr('no-minimal.html', no_minimal(base), nl)
    print('  no-minimal.html')

    # hub
    s, hnl = rd('guias.html'); s = p.strip(s.replace('\n', hnl)).replace('\r\n', '\n')
    nuevas = [g for g in GUIAS if '/%s"' % g['slug'] not in s]
    if nuevas:
        cards = ''.join('<a class="g-card" href="/%s"><span class="g-tag">%s · %d min</span><h2>%s</h2><p>%s</p></a>'
                        % (g['slug'], esc(g['tag']), g['minutos'], esc(g['titulo']), esc(g['desc'])) for g in nuevas)
        last =s.rindex('</a>', 0, s.index('¿No encuentras tu pregunta?'))
        s = s[:last + 4] + cards + s[last + 4:]
        m = re.search(r'("hasPart":\[)(.*?)(\]\})', s, re.S)
        extra = ''.join(',' + json.dumps({'@type': 'Article', 'headline': g['titulo'], 'url': SITE + '/' + g['slug']}, ensure_ascii=False, separators=(',', ':')) for g in nuevas)
        s = s[:m.end(2)] + extra + s[m.end(2):]
    if 'id="nm-bloque"' not in s:
        nm = ('  <section id="nm-bloque" aria-labelledby="nm-h" style="margin-top:36px;background:linear-gradient(160deg,#17333D 0%%,#102229 100%%);border-radius:14px;padding:clamp(24px,4vw,36px);">\n'
              '    <p style="margin:0;font-weight:700;font-size:12px;letter-spacing:0.2em;text-transform:uppercase;color:#F2A81E;">Aparte de las guías</p>\n'
              '    <h2 id="nm-h" style="font-family:\'Bricolage Grotesque\',sans-serif;font-weight:800;font-size:clamp(22px,2.8vw,30px);color:#F7EFDC;margin:10px 0 0;line-height:1.15;">No Minimal: arquitectura latinoamericana sin miedo al color</h2>\n'
              '    <p style="font-size:16px;color:#C6D5D9;line-height:1.6;margin:12px 0 0;max-width:680px;">Seis ensayos y tesis del Arq. Orelio Martínez sobre el ladrillo, la luz, el color, el patio y cómo construir bien en la región. Lectura larga, con fuentes.</p>\n'
              '    <div style="display:flex;flex-wrap:wrap;gap:12px;margin-top:20px;">\n'
              '      <a href="/no-minimal" style="display:inline-flex;align-items:center;background:#B0512B;color:#FBF2E0;text-decoration:none;border-radius:8px;padding:12px 20px;font-weight:700;font-size:14.5px;min-height:46px;" style-hover="background:#8E3F20;">Ver los ensayos →</a>\n'
              '      <a href="%s" target="_blank" rel="noopener" style="display:inline-flex;align-items:center;color:#F2A81E;text-decoration:none;border:1.5px solid rgba(242,168,30,0.5);border-radius:8px;padding:12px 18px;font-weight:700;font-size:14.5px;min-height:46px;" style-hover="background:rgba(242,168,30,0.12);">Ir a nominimal.com ↗</a>\n'
              '    </div>\n  </section>\n' % NM)
        k = s.index('</div>\n', s.index('¿No encuentras tu pregunta?')) + len('</div>\n')
        s = s[:k] + nm + s[k:]
    wr('guias.html', s, hnl)

    # sitemap
    sm, snl = rd('sitemap.xml')
    add = ''.join('  <url><loc>%s/%s</loc><lastmod>%s</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>\n' % (SITE, x, HOY)
                  for x in [g['slug'] for g in GUIAS] + ['no-minimal'] if '<loc>%s/%s</loc>' % (SITE, x) not in sm)
    sm = re.sub(r'(<loc>%s/guias</loc><lastmod>)[^<]*' % re.escape(SITE), r'\g<1>' + HOY, sm)
    wr('sitemap.xml', sm.replace('</urlset>', add + '</urlset>'), snl)

    # mapa del sitio
    s, mnl = rd('mapa-del-sitio.html'); s = p.strip(s.replace('\n', mnl)).replace('\r\n', '\n')
    m = re.search(r'<a href="/guia-replanteo-de-obra"([^>]*)>[^<]*</a>', s)
    extra = ''.join('\n<a href="/%s"%s>%s</a>' % (g['slug'], m.group(1), esc(g['seo'])) for g in GUIAS if '/%s"' % g['slug'] not in s)
    if '/no-minimal"' not in s: extra += '\n<a href="/no-minimal"%s>No Minimal</a>' % m.group(1)
    wr('mapa-del-sitio.html', s[:m.end()] + extra + s[m.end():], mnl)
    print('hub, sitemap y mapa del sitio actualizados')


if __name__ == '__main__':
    main()
