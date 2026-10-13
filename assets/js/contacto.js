/* Martínez-Segura — el cliente elige con quién hablar.
 *
 * El Ing. Steven Segura y el Arq. Orelio Martínez atienden por WhatsApp. Los botones
 * genéricos ("Cotizar", "Escríbenos") ya no abren un número fijo: muestran un
 * selector con los dos, lo que atiende cada uno y, cuando la página o el
 * formulario dejan claro el servicio, cuál es el sugerido. Se conserva el
 * mensaje prellenado (?text=).
 *
 * Enlaces que se respetan tal cual:
 *   - los que muestran un nombre o un número en su texto (tarjetas de contacto)
 *   - los que llevan data-persona-fijo (o están dentro de un elemento que lo lleva)
 *   - otros números (p. ej. PARCON)
 *
 * Formularios: window.MSContacto.elegir({ texto: mensaje, servicio: 'Levantamiento catastral' }).
 * También añade en móvil una barra fija con WhatsApp y Cotizar.
 */
(function () {
  var EN = (document.documentElement.lang || 'es').slice(0, 2) === 'en';
  var PERSONAS = {
    steven: {
      nombre: 'Ing. Steven Segura', iniciales: 'SS', numero: '50588663659', tel: '+505 8866 3659',
      servicios: EN ? 'Surveying, cadastral plans, site control and geodetic markers'
                    : 'Topografía, catastro, control de obra y mojones'
    },
    orelio: {
      nombre: 'Arq. Orelio Martínez', iniciales: 'OM', numero: '17608830683', tel: '+1 760 883 0683',
      servicios: EN ? 'Architecture, structural design, BIM and cost estimates'
                    : 'Arquitectura, diseño estructural, BIM y presupuestos'
    }
  };
  var T = EN ? {
    titulo: 'Who would you like to talk to?', sub: 'Pick by the service you need. Both reply on WhatsApp.',
    sugerido: 'Suggested', cerrar: 'Close', wa: 'WhatsApp', cotizar: 'Contact', cotizarHref: '/en/contact', barra: 'Quick contact'
  } : {
    titulo: '¿Con quién quieres hablar?', sub: 'Elige según el servicio que necesitas. Los dos responden por WhatsApp.',
    sugerido: 'Sugerido', cerrar: 'Cerrar', wa: 'WhatsApp', cotizar: 'Cotizar', cotizarHref: '/cotizador', barra: 'Contacto rápido'
  };
  var NUMS = /wa\.me\/(50588663659|17608830683)(?=[/?#]|$)/;
  var PERSONAL = /steven|orelio|\d{3}[\s-]?\d{4}/i;
  var DE_STEVEN = /top[oó]gr|catastr|deslinde|lindero|control[- ]de[- ]obra|replanteo|moj[oó]n|geod[eé]s|terreno|survey|cadastr|boundar|stak|layout|site control|geodetic|monument/i;
  var DE_ORELIO = /arquitect|architect|estructural|structural|\bbim\b|presupuesto|costos|remodel|interior|vivienda|casa\b|house|design|cost estimate|budget/i;
  // Valores cortos del cotizador que las expresiones de arriba no reconocen.
  var CLAVES = { obra: 'steven', division: 'steven', diseno: 'orelio' };

  // Quién lleva el servicio; null cuando no está claro (se muestran los dos sin sugerir).
  function sugerido(texto) {
    var s = String(texto || '');
    if (CLAVES[s]) return CLAVES[s];
    var a = DE_STEVEN.test(s), b = DE_ORELIO.test(s);
    if (a && !b) return 'steven';
    if (b && !a) return 'orelio';
    return null;
  }

  function evento(persona, origen) {
    if (typeof window.gtag !== 'function') return;
    try { window.gtag('event', 'whatsapp_click', { persona: persona, origen: origen, page_path: location.pathname }); } catch (e) {}
  }

  var CSS = '' +
    '.msc-dlg{border:0;padding:0;border-radius:16px;background:#FFFDF6;color:#2B1F15;width:min(440px,calc(100vw - 28px));box-shadow:0 24px 60px rgba(16,34,41,.38);font-family:"Hanken Grotesk",system-ui,sans-serif}' +
    '.msc-dlg::backdrop{background:rgba(16,34,41,.55)}' +
    '.msc-in{padding:22px 20px 20px;display:grid;gap:12px}' +
    '.msc-top{display:flex;align-items:flex-start;justify-content:space-between;gap:12px}' +
    '.msc-h{font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:21px;line-height:1.15;margin:0}' +
    '.msc-p{font-size:14.5px;line-height:1.5;color:#5C4A36;margin:0}' +
    '.msc-x{flex:none;width:44px;height:44px;margin:-10px -8px 0 0;border:0;background:transparent;color:#5C4A36;font-size:24px;line-height:1;cursor:pointer;border-radius:10px}' +
    '.msc-x:hover{background:rgba(43,31,21,.07)}' +
    '.msc-op{display:grid;grid-template-columns:46px 1fr;gap:12px;align-items:center;text-decoration:none;color:inherit;background:#F4EAD2;border:1.5px solid rgba(43,31,21,.14);border-radius:12px;padding:14px;min-height:76px}' +
    '.msc-op:hover{border-color:#25D366;background:#F0F7EC}' +
    '.msc-op:focus-visible,.msc-x:focus-visible,.msc-bar a:focus-visible,.msc-bar button:focus-visible{outline:3px solid #2F5D68;outline-offset:2px}' +
    '.msc-av{width:46px;height:46px;border-radius:50%;background:#17333D;color:#F7EFDC;display:flex;align-items:center;justify-content:center;font-family:"Bricolage Grotesque",sans-serif;font-weight:800;font-size:15px}' +
    '.msc-n{display:flex;flex-wrap:wrap;align-items:center;gap:6px 8px;font-family:"Bricolage Grotesque",sans-serif;font-weight:700;font-size:16.5px;line-height:1.2}' +
    '.msc-s{display:block;font-size:13.5px;line-height:1.4;color:#4E3D2C;margin-top:3px}' +
    '.msc-t{display:block;font-size:13px;color:#7A6A52;margin-top:3px;font-variant-numeric:tabular-nums}' +
    '.msc-b{font-family:"Hanken Grotesk",sans-serif;font-weight:700;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:#0B5A2A;background:#D6F3DF;border-radius:999px;padding:2px 8px}' +
    '.msc-bar{position:fixed;left:0;right:0;bottom:0;z-index:90;display:none;gap:10px;padding:10px 14px calc(10px + env(safe-area-inset-bottom,0px));background:rgba(16,34,41,.96);box-shadow:0 -6px 20px rgba(16,34,41,.25);transform:translateY(110%);transition:transform .22s ease}' +
    '.msc-bar.on{transform:none}' +
    '.msc-bar a,.msc-bar button{flex:1;display:flex;align-items:center;justify-content:center;gap:8px;min-height:48px;border-radius:10px;font:700 15px "Hanken Grotesk",system-ui,sans-serif;text-decoration:none;cursor:pointer;border:0}' +
    '.msc-bar button{background:#25D366;color:#08301C}.msc-bar a{background:#B0512B;color:#FBF2E0}' +
    '@media (max-width:760px){.msc-bar{display:flex}body.msc-pad{padding-bottom:calc(68px + env(safe-area-inset-bottom,0px))}}' +
    '@media (prefers-reduced-motion:reduce){.msc-bar{transition:none}}';
  var WA_ICON = '<svg width="19" height="19" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 00-8.6 15L2 22l5.1-1.3A10 10 0 1012 2zm5.8 14.2c-.2.7-1.4 1.3-2 1.4-.5.1-1.2.1-1.9-.1-.4-.1-1-.3-1.7-.6-3-1.3-4.9-4.3-5-4.5-.1-.2-1.2-1.6-1.2-3s.7-2.1 1-2.4c.2-.3.5-.3.7-.3h.5c.2 0 .4 0 .6.5l.8 1.9c.1.1.1.3 0 .5l-.3.5-.4.4c-.1.1-.3.3-.1.5.1.3.7 1.1 1.4 1.8 1 .8 1.7 1.1 2 1.2.2.1.4.1.5-.1l.6-.8c.2-.2.4-.2.6-.1l1.8.9c.3.1.4.2.5.3.1.2.1.6-.1 1.2z"/></svg>';

  var dlg = null;
  function estilos() {
    if (document.getElementById('msc-css')) return;
    var st = document.createElement('style'); st.id = 'msc-css'; st.textContent = CSS;
    document.head.appendChild(st);
  }

  function opcion(id, query, recomendado, origen) {
    var p = PERSONAS[id], a = document.createElement('a');
    a.className = 'msc-op'; a.target = '_blank'; a.rel = 'noopener';
    a.href = 'https://wa.me/' + p.numero + (query || '');
    a.setAttribute('data-persona-fijo', id);
    a.innerHTML = '<span class="msc-av" aria-hidden="true">' + p.iniciales + '</span><span><span class="msc-n">' + p.nombre +
      (recomendado ? '<span class="msc-b">' + T.sugerido + '</span>' : '') + '</span><span class="msc-s">' + p.servicios +
      '</span><span class="msc-t">WhatsApp · ' + p.tel + '</span></span>';
    a.addEventListener('click', function () { evento(id, origen); cerrar(); });
    return a;
  }

  function cerrar() {
    if (!dlg) return;
    if (dlg.close && dlg.open) dlg.close(); else dlg.removeAttribute('open');
  }

  // opts: { texto, servicio, query, origen }
  function elegir(opts) {
    opts = opts || {};
    estilos();
    var query = opts.query || (opts.texto ? '?text=' + encodeURIComponent(opts.texto) : '');
    var rec = sugerido(opts.servicio != null ? opts.servicio : location.pathname);
    var orden = rec === 'orelio' ? ['orelio', 'steven'] : ['steven', 'orelio'];
    if (!dlg) {
      dlg = document.createElement('dialog'); dlg.className = 'msc-dlg'; dlg.setAttribute('aria-labelledby', 'msc-h');
      dlg.addEventListener('click', function (ev) { if (ev.target === dlg) cerrar(); });
      document.body.appendChild(dlg);
    }
    dlg.innerHTML = '<div class="msc-in"><div class="msc-top"><h2 class="msc-h" id="msc-h">' + T.titulo +
      '</h2><button type="button" class="msc-x" aria-label="' + T.cerrar + '">×</button></div><p class="msc-p">' + T.sub + '</p></div>';
    var box = dlg.firstChild;
    orden.forEach(function (id) { box.appendChild(opcion(id, query, id === rec, opts.origen || 'selector')); });
    dlg.querySelector('.msc-x').addEventListener('click', cerrar);
    if (dlg.showModal) { if (!dlg.open) dlg.showModal(); } else dlg.setAttribute('open', '');
  }

  function generico(a) {
    if (a.closest('[data-persona-fijo]')) return false;
    return !PERSONAL.test(a.textContent || '');
  }

  document.addEventListener('click', function (ev) {
    if (ev.defaultPrevented || ev.button || ev.metaKey || ev.ctrlKey || ev.shiftKey) return;
    var t = ev.target && ev.target.closest ? ev.target.closest('a[href^="tel:"], a[href^="mailto:"]') : null;
    if (t && typeof window.gtag === 'function') {
      // Llamadas y correos también son contactos: se miden igual que WhatsApp.
      try { window.gtag('event', t.getAttribute('href').indexOf('tel:') === 0 ? 'llamada_click' : 'correo_click', { page_path: location.pathname }); } catch (e) {}
    }
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href*="wa.me/"]') : null;
    if (!a) return;
    var href = a.getAttribute('href') || '', m = href.match(NUMS);
    if (!m) return;
    if (!generico(a)) { evento(m[1] === '17608830683' ? 'orelio' : 'steven', 'tarjeta'); return; }
    ev.preventDefault();
    var q = href.indexOf('?') > -1 ? href.slice(href.indexOf('?')) : '';
    var texto = '';
    try { texto = decodeURIComponent((q.match(/[?&]text=([^&]*)/) || [, ''])[1]); } catch (e) {}
    elegir({ query: q, servicio: location.pathname + ' ' + texto, origen: 'boton' });
  }, true);

  // Barra fija en móvil: aparece al bajar, no tapa el primer pantallazo.
  function barra() {
    var path = location.pathname;
    if (/^\/(contacto|cotizador|tarjeta|parajon-construcciones|construccion-|en\/contact)/.test(path)) return;
    if (document.querySelector('.sticky-cta') || document.querySelector('.msc-bar')) return;
    estilos();
    var b = document.createElement('div'); b.className = 'msc-bar'; b.setAttribute('role', 'group'); b.setAttribute('aria-label', T.barra);
    var w = document.createElement('button'); w.type = 'button'; w.innerHTML = WA_ICON + T.wa;
    w.addEventListener('click', function () { elegir({ origen: 'barra' }); });
    var c = document.createElement('a'); c.href = T.cotizarHref; c.textContent = T.cotizar;
    b.appendChild(w); b.appendChild(c); document.body.appendChild(b);
    var on = false;
    function tick() {
      var want = window.scrollY > 520;
      if (want === on) return;
      on = want; b.classList.toggle('on', on); document.body.classList.toggle('msc-pad', on);
    }
    window.addEventListener('scroll', tick, { passive: true }); tick();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', barra); else barra();

  window.MSContacto = { personas: PERSONAS, sugerido: sugerido, elegir: elegir };
})();
