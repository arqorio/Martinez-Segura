/* Martínez-Segura — reparto de contactos por WhatsApp.
 *
 * Steven y Orelio atienden clientes por igual. A cada visitante se le asigna
 * una persona al azar (50/50) y se recuerda en localStorage, así siempre le
 * escribe a la misma. Los botones genéricos de WhatsApp ("Cotizar", "Escríbenos")
 * se reescriben hacia esa persona, conservando el ?text= prellenado.
 *
 * No se tocan:
 *   - enlaces con data-persona-fijo (o dentro de un elemento con ese atributo)
 *   - enlaces cuyo texto nombra a alguien o muestra el número (tarjetas de contacto)
 *   - otros números (p. ej. PARCON)
 *
 * Los formularios leen window.MSContacto.numero para enviar a la misma persona.
 */
(function () {
  var PERSONAS = {
    steven: { nombre: 'Ing. Steven Segura', numero: '50588663659' },
    orelio: { nombre: 'Orelio Martínez', numero: '17608830683' }
  };
  var KEY = 'ms-persona';
  var NUMS = /wa\.me\/(50588663659|17608830683)(?=[/?#]|$)/;
  var PERSONAL = /steven|orelio|\d{3}[\s-]?\d{4}/i;

  var id = null;
  try { id = localStorage.getItem(KEY); } catch (e) {}
  if (!PERSONAS[id]) {
    id = Math.random() < 0.5 ? 'steven' : 'orelio';
    try { localStorage.setItem(KEY, id); } catch (e) {}
  }
  var p = PERSONAS[id];
  window.MSContacto = { persona: id, nombre: p.nombre, numero: p.numero };

  function generic(a) {
    if (a.closest('[data-persona-fijo]')) return false;
    return !PERSONAL.test(a.textContent || '');
  }

  function rewrite(a) {
    var href = a.getAttribute('href') || '';
    if (!NUMS.test(href) || !generic(a)) return;
    var next = href.replace(NUMS, 'wa.me/' + p.numero);
    if (next !== href) a.setAttribute('href', next);
  }

  function sweep(root) {
    var list = (root || document).querySelectorAll('a[href*="wa.me/"]');
    for (var i = 0; i < list.length; i++) rewrite(list[i]);
  }

  // The x-dc runtime renders the page after load, so keep watching for new links.
  var queued = false;
  function schedule() {
    if (queued) return;
    queued = true;
    setTimeout(function () { queued = false; sweep(); }, 50);
  }
  if (window.MutationObserver) {
    new MutationObserver(schedule).observe(document.documentElement, { childList: true, subtree: true });
  }
  document.addEventListener('DOMContentLoaded', schedule);

  // Safety net for a link rendered between sweeps, plus the analytics event.
  document.addEventListener('click', function (ev) {
    var a = ev.target && ev.target.closest ? ev.target.closest('a[href*="wa.me/"]') : null;
    if (!a) return;
    rewrite(a);
    var m = (a.getAttribute('href') || '').match(/wa\.me\/(\d+)/);
    if (m && typeof window.gtag === 'function') {
      try {
        window.gtag('event', 'whatsapp_click', {
          destination: m[1],
          persona: m[1] === '17608830683' ? 'orelio' : m[1] === '50588663659' ? 'steven' : 'otro',
          page_path: location.pathname
        });
      } catch (e) {}
    }
  }, true);
})();
