/**
 * BhuSynch AI — Service Worker
 * Provides offline-first caching for the Mobile Ground-Truthing PWA.
 * Implements cache-first strategy for static assets and network-first for API calls.
 */

const CACHE_NAME = 'bhusynch-field-v1.0.0';
const STATIC_CACHE = 'bhusynch-static-v1';
const DATA_CACHE = 'bhusynch-data-v1';
const TILE_CACHE = 'bhusynch-tiles-v1';

/** Static assets to pre-cache on install */
const PRECACHE_URLS = [
    '/mobile-pwa/index.html',
    '/mobile-pwa/css/mobile.css',
    '/mobile-pwa/js/pwa-app.js',
    '/mobile-pwa/js/offline-sync.js',
    '/mobile-pwa/js/camera-capture.js',
    '/mobile-pwa/manifest.json'
];

/** Maximum tile cache size (in entries) */
const MAX_TILE_CACHE_ENTRIES = 500;

// ── Install Event ──
self.addEventListener('install', (event) => {
    console.log('[BhuSynch SW] Installing service worker...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[BhuSynch SW] Pre-caching static assets');
                return cache.addAll(PRECACHE_URLS);
            })
            .then(() => self.skipWaiting())
    );
});

// ── Activate Event ──
self.addEventListener('activate', (event) => {
    console.log('[BhuSynch SW] Activating service worker...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => {
                        return name !== STATIC_CACHE &&
                               name !== DATA_CACHE &&
                               name !== TILE_CACHE;
                    })
                    .map((name) => {
                        console.log(`[BhuSynch SW] Deleting old cache: ${name}`);
                        return caches.delete(name);
                    })
            );
        }).then(() => self.clients.claim())
    );
});

// ── Fetch Event ──
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Tile requests — cache-first with eviction
    if (url.pathname.includes('/tiles/') || url.pathname.endsWith('.pbf')) {
        event.respondWith(tileCacheFirst(request));
        return;
    }

    // API requests — network-first, fall back to cache
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/ogc/')) {
        event.respondWith(networkFirst(request));
        return;
    }

    // Static assets — cache-first
    event.respondWith(cacheFirst(request));
});

// ── Background Sync ──
self.addEventListener('sync', (event) => {
    if (event.tag === 'bhusynch-survey-sync') {
        console.log('[BhuSynch SW] Background sync triggered');
        event.waitUntil(syncPendingSurveys());
    }
});

// ── Push Notifications ──
self.addEventListener('push', (event) => {
    if (!event.data) return;

    const data = event.data.json();
    const options = {
        body: data.body || 'New update from BhuSynch AI',
        icon: '/mobile-pwa/icons/icon-192x192.png',
        badge: '/mobile-pwa/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            url: data.url || '/mobile-pwa/index.html'
        },
        actions: [
            { action: 'open', title: 'View' },
            { action: 'dismiss', title: 'Dismiss' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification(data.title || 'BhuSynch AI', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();
    if (event.action === 'open' || !event.action) {
        event.waitUntil(
            clients.openWindow(event.notification.data.url)
        );
    }
});

// ── Cache Strategies ──

/**
 * Cache-first strategy for static assets.
 */
async function cacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(STATIC_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.warn('[BhuSynch SW] Offline — no cached version for:', request.url);
        return new Response('Offline', { status: 503, statusText: 'Service Unavailable' });
    }
}

/**
 * Network-first strategy for API calls.
 */
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(DATA_CACHE);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        const cached = await caches.match(request);
        if (cached) {
            console.log('[BhuSynch SW] Serving API from cache:', request.url);
            return cached;
        }
        return new Response(JSON.stringify({ error: 'offline', message: 'No network and no cached data' }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

/**
 * Tile cache-first with LRU eviction.
 */
async function tileCacheFirst(request) {
    const cached = await caches.match(request);
    if (cached) return cached;

    try {
        const response = await fetch(request);
        if (response.ok) {
            const cache = await caches.open(TILE_CACHE);
            // Evict oldest entries if over limit
            const keys = await cache.keys();
            if (keys.length >= MAX_TILE_CACHE_ENTRIES) {
                const deleteCount = Math.ceil(MAX_TILE_CACHE_ENTRIES * 0.1);
                for (let i = 0; i < deleteCount; i++) {
                    await cache.delete(keys[i]);
                }
            }
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return new Response('', { status: 204 });
    }
}

/**
 * Sync pending survey data from IndexedDB to server.
 */
async function syncPendingSurveys() {
    // Opens IndexedDB and pushes pending items to the API
    // This is called by Background Sync when connectivity is restored
    console.log('[BhuSynch SW] Syncing pending survey data...');

    try {
        const db = await openSyncDB();
        const tx = db.transaction('pending_surveys', 'readonly');
        const store = tx.objectStore('pending_surveys');
        const surveys = await getAllFromStore(store);

        for (const survey of surveys) {
            try {
                const response = await fetch('/api/v1/survey/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(survey.data)
                });

                if (response.ok) {
                    // Remove from pending queue
                    const deleteTx = db.transaction('pending_surveys', 'readwrite');
                    deleteTx.objectStore('pending_surveys').delete(survey.id);
                    console.log(`[BhuSynch SW] Synced survey: ${survey.id}`);
                }
            } catch (err) {
                console.warn(`[BhuSynch SW] Failed to sync survey ${survey.id}:`, err);
            }
        }
    } catch (error) {
        console.error('[BhuSynch SW] Sync failed:', error);
    }
}

function openSyncDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('BhuSynchFieldDB', 1);
        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains('pending_surveys')) {
                db.createObjectStore('pending_surveys', { keyPath: 'id', autoIncrement: true });
            }
        };
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

function getAllFromStore(store) {
    return new Promise((resolve, reject) => {
        const request = store.getAll();
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}
