/* Martínez-Segura Facturación — service worker.
 *
 * Two jobs: make the app installable on Android, and make it open with no
 * signal. The pages are ~1 MB single-file bundles, so they are served from
 * cache immediately and refreshed in the background (stale-while-revalidate);
 * a new deploy is picked up on the next launch.
 *
 * Everything outside APP_URLS is left completely alone — this worker is
 * registered at the site root, so it must not touch the rest of the site.
 *
 * Bump CACHE_VERSION on every deploy so old bundles are evicted.
 */
const CACHE_VERSION = 'ms-facturacion-v12.3';
/* Written by the app on every run so this worker can raise a follow-up
   notification without the app being open. Never evicted with the page cache. */
const NOTIFY_CACHE = 'ms-facturacion-notify';
const CACHE = CACHE_VERSION;

/* The directory this worker was served from — '/' at the site root,
   '/deploy-facturacion/' when the folder is uploaded as a subdirectory.
   Every path below is built from it, so the same file works either way. */
const BASE = self.location.pathname.replace(/[^/]*$/, '');
const at = (f) => BASE + f;

/* Fetched during install so the app opens offline on first launch. */
const PRECACHE = [
  at('facturacion-app'),
  at('manifest-facturacion.webmanifest'),
  at('icon-192.png'),
  at('icon-512.png'),
  at('icon-maskable-192.png'),
  at('apple-touch-icon.png'),
];

/* Also cached, but only once actually visited — no point paying for the
   desktop bundle and the calculator on a phone's first install. */
const RUNTIME = [
  at('facturacion-web'),
  at('facturacion-calculadora'),
  at('facturacion-app.html'),
  at('facturacion-web.html'),
  at('facturacion-calculadora.html'),
];

const OWNED = new Set(PRECACHE.concat(RUNTIME));

self.addEventListener('install', (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE);
    // Individually, so one missing file cannot fail the whole install.
    await Promise.all(PRECACHE.map((url) =>
      cache.add(new Request(url, { cache: 'reload' })).catch(() => {})
    ));
    await self.skipWaiting();
  })());
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(
      names.filter((n) => n.startsWith('ms-facturacion-') && n !== CACHE && n !== NOTIFY_CACHE)
           .map((n) => caches.delete(n))
    );
    await self.clients.claim();
  })());
});

self.addEventListener('message', (event) => {
  if (event.data === 'skip-waiting') self.skipWaiting();
});

function isOurs(url) {
  if (url.origin !== self.location.origin) return false;
  return OWNED.has(url.pathname);
}

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  let url;
  try { url = new URL(req.url); } catch (e) { return; }

  // The manifest's shortcuts add a query string; the document is the same one.
  const isAppNav = req.mode === 'navigate' && url.origin === self.location.origin &&
                   (url.pathname === at('facturacion-app') || url.pathname === at('facturacion-app.html'));

  if (!isAppNav && !isOurs(url)) return;  // hands off the rest of the site

  const key = isAppNav ? at('facturacion-app') : url.pathname;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE);
    const cached = await cache.match(key);

    const network = fetch(req).then((res) => {
      if (res && res.ok && res.type !== 'opaque') cache.put(key, res.clone());
      return res;
    }).catch(() => null);

    // Serve what we have and refresh behind it; fall back to the network on a
    // cold cache, and to whatever we have when the network is gone.
    if (cached) { event.waitUntil(network); return cached; }

    const fresh = await network;
    if (fresh) return fresh;

    if (isAppNav) {
      const shell = await cache.match(at('facturacion-app'));
      if (shell) return shell;
    }
    return new Response(
      '<!doctype html><meta charset="utf-8"><title>Sin conexión</title>' +
      '<body style="margin:0;display:flex;align-items:center;justify-content:center;' +
      'height:100vh;background:#17333D;color:#F4EAD2;font:16px/1.5 system-ui,sans-serif;' +
      'text-align:center;padding:24px">' +
      '<div><p style="font-weight:700;margin:0 0 6px">Sin conexión</p>' +
      '<p style="margin:0;opacity:.75;font-size:14px">Abre la app una vez con internet ' +
      'para poder usarla sin señal.</p></div>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } }
    );
  })());
});

/* ── Avisos de seguimiento ────────────────────────────────────────
 * The app writes /__followup into NOTIFY_CACHE whenever it runs. Ages are
 * recomputed here at fire time, so a summary written days ago still produces
 * an accurate notification.
 *
 * periodicsync is Chromium-on-Android only, and only for an installed app the
 * browser considers engaged — it is a best-effort daily nudge, not a schedule.
 */
const DAY = 86400000;

function daysSince(iso) {
  if (!iso) return 0;
  const [y, m, d] = String(iso).split('-').map(Number);
  if (!y) return 0;
  return Math.round((Date.now() - new Date(y, m - 1, d).getTime()) / DAY);
}

async function readFollowup() {
  try {
    const cache = await caches.open(NOTIFY_CACHE);
    const res = await cache.match('/__followup');
    if (!res) return null;
    return await res.json();
  } catch (e) { return null; }
}

async function notifyFollowup() {
  const p = await readFollowup();
  if (!p) return;

  const days = p.days || 7;
  const quotes = (p.quotes || []).filter((q) => daysSince(q.since) >= days);
  const cobros = (p.cobros || []).filter((c) => daysSince(c.due) > 0);
  if (!quotes.length && !cobros.length) return;

  // At most one a day, even if the browser wakes us more often.
  const stamp = new Date().toISOString().slice(0, 10);
  const cache = await caches.open(NOTIFY_CACHE);
  const seen = await cache.match('/__notified');
  if (seen && (await seen.text()) === stamp) return;

  const parts = [];
  if (quotes.length) {
    parts.push(quotes.length + ' cotización' + (quotes.length === 1 ? '' : 'es') + ' sin respuesta');
  }
  if (cobros.length) {
    parts.push(cobros.length + ' factura' + (cobros.length === 1 ? '' : 's') + ' vencida' + (cobros.length === 1 ? '' : 's'));
  }
  const first = quotes[0] || cobros[0];
  const oldest = quotes.length ? daysSince(quotes[0].since) : 0;

  try {
    await self.registration.showNotification('Seguimiento pendiente', {
      body: parts.join(' · ')
        + (first ? '\n' + first.client + ' · ' + first.number : '')
        + (oldest ? ' · ' + oldest + ' días' : ''),
      icon: at('icon-192.png'),
      badge: at('icon-192.png'),
      tag: 'ms-followup',
      data: { url: at('facturacion-app?accion=seguimiento') },
    });
    await cache.put('/__notified', new Response(stamp));
  } catch (e) {
    // Permission revoked since the app asked: stay quiet and try again
    // tomorrow rather than rejecting the sync event.
  }
}

self.addEventListener('periodicsync', (event) => {
  if (event.tag === 'ms-followup') event.waitUntil(notifyFollowup());
});

/* Manual trigger, so the app can ask for a check without duplicating the logic. */
self.addEventListener('message', (event) => {
  if (event.data === 'check-followup') event.waitUntil(notifyFollowup());
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || at('facturacion-app');
  event.waitUntil((async () => {
    const all = await self.clients.matchAll({ type: 'window', includeUncontrolled: true });
    for (const c of all) {
      if (c.url.includes(at('facturacion-app'))) {
        await c.focus();
        if ('navigate' in c) { try { await c.navigate(url); } catch (e) {} }
        return;
      }
    }
    await self.clients.openWindow(url);
  })());
});
