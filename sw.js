const CACHE_NAME = 'senda-r6-review-folio-gestion-v1';
const ARCHIVE_RUNTIME = [
  'https://cdn.jsdelivr.net/npm/7z-wasm@1.2.0/7zz.umd.js',
  'https://cdn.jsdelivr.net/npm/7z-wasm@1.2.0/7zz.wasm'
];
const APP_SHELL = [
  './',
  './index.html',
  './manifest.webmanifest',
  './assets/app_icon_senda_r6.png',
  './data/registro_inmobiliario_base.sqlite'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(APP_SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(key => key.startsWith('senda-') && key !== CACHE_NAME).map(key => caches.delete(key))
    ))
  );
  self.clients.claim();
});

async function networkFirst(request, fallback) {
  try {
    const response = await fetch(request, {cache:'reload'});
    if (response && response.ok && (new URL(request.url).origin === self.location.origin || ARCHIVE_RUNTIME.includes(request.url))) {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(request, copy));
    }
    return response;
  } catch (error) {
    return (await caches.match(request)) || (fallback ? await caches.match(fallback) : undefined) || Response.error();
  }
}

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  if (event.request.mode === 'navigate') {
    event.respondWith(networkFirst(event.request, './index.html'));
    return;
  }
  if (new URL(event.request.url).origin === self.location.origin || ARCHIVE_RUNTIME.includes(event.request.url)) {
    event.respondWith(networkFirst(event.request));
  }
});
