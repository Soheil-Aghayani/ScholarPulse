// ScholarPulse Service Worker
const CACHE_NAME = 'scholarpulse-v3';
const ASSETS = [
  './',
  './index.html',
  './manifest.json',
  './icon.svg',
  './icon-192.png',
  './icon-512.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS).catch(() => {});
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);
  const isSameOrigin = requestUrl.origin === self.location.origin;
  const isImage = event.request.destination === 'image';
  if (!isSameOrigin && !isImage) return;

  // Keep navigation fresh while still allowing the app shell to open offline.
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).then((response) => {
        const cachedResponse = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put('./index.html', cachedResponse));
        return response;
      }).catch(() => caches.match('./index.html'))
    );
    return;
  }

  // Static files and previously viewed profile pictures remain available after
  // the first successful visit. A background request refreshes stale content.
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      const networkResponse = fetch(event.request).then((response) => {
        if (response.ok || response.type === 'opaque') {
          const cachedCopy = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, cachedCopy));
        }
        return response;
      }).catch(() => cachedResponse);
      return cachedResponse || networkResponse;
    })
  );
});
