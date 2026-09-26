/* Martínez-Segura Facturación — retiro del service worker viejo de la raíz.
 *
 * Las primeras versiones de la app vivían en la raíz del sitio y registraban
 * /facturacion-sw.js con alcance "/". Ese worker servía /facturacion-web y
 * /facturacion-app desde su propia caché primero. Cuando la app se mudó a
 * /deploy-facturacion/ y este archivo se borró, la revisión de actualización
 * empezó a dar 404 — y un navegador sigue ejecutando un service worker cuya
 * actualización falla. Resultado: esos teléfonos y computadoras seguían
 * mostrando la versión vieja guardada, aunque el servidor ya mandaba la nueva.
 *
 * Este archivo reemplaza a ese worker la próxima vez que el navegador lo
 * revisa: borra las cachés viejas, se da de baja y recarga las pestañas
 * abiertas una sola vez. No toca al worker actual, que vive en
 * /deploy-facturacion/ con su propio registro y su propia caché.
 *
 * No borrar este archivo: cualquier navegador que no haya abierto la app desde
 * entonces todavía tiene al worker viejo esperando.
 */
const CURRENT_MIN = [12, 7];   // cachés de /deploy-facturacion/ que se conservan

function isOldCache(name) {
  const m = /^ms-facturacion-v(\d+)\.(\d+)$/.exec(name);
  if (!m) return false;
  const major = +m[1], minor = +m[2];
  return major < CURRENT_MIN[0] || (major === CURRENT_MIN[0] && minor < CURRENT_MIN[1]);
}

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter(isOldCache).map((n) => caches.delete(n)));
    await self.registration.unregister();
    // Las pestañas que el worker viejo controlaba se recargan desde la red.
    const windows = await self.clients.matchAll({ type: 'window' });
    for (const c of windows) {
      try { await c.navigate(c.url); } catch (e) {}
    }
  })());
});

// Sin manejador de fetch: mientras termina de darse de baja, todo va a la red.
