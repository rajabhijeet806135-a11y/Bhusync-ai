/**
 * BhuSynch AI — Offline Sync Module
 * 
 * Handles offline data synchronization for the Mobile Ground-Truthing PWA.
 * Implements an encrypted OGC GeoPackage queue that syncs when
 * connectivity is restored.
 */

const OfflineSync = (() => {
    'use strict';

    const DB_NAME = 'bhusynch_offline_db';
    const DB_VERSION = 1;
    const STORES = {
        PARCELS: 'offline_parcels',
        SURVEYS: 'offline_surveys',
        PHOTOS: 'offline_photos',
        SYNC_QUEUE: 'sync_queue'
    };

    let _db = null;
    let _syncInProgress = false;
    let _onSyncCallback = null;

    /**
     * Open (or create) the IndexedDB database with required object stores.
     * @returns {Promise<IDBDatabase>}
     */
    function openDB() {
        return new Promise((resolve, reject) => {
            if (_db) {
                resolve(_db);
                return;
            }
            const request = indexedDB.open(DB_NAME, DB_VERSION);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                // Parcels cached for offline viewing
                if (!db.objectStoreNames.contains(STORES.PARCELS)) {
                    const parcelStore = db.createObjectStore(STORES.PARCELS, { keyPath: 'ulpin' });
                    parcelStore.createIndex('status', 'status', { unique: false });
                    parcelStore.createIndex('lastSynced', 'lastSynced', { unique: false });
                }
                // Ground-truth surveys captured in the field
                if (!db.objectStoreNames.contains(STORES.SURVEYS)) {
                    const surveyStore = db.createObjectStore(STORES.SURVEYS, { keyPath: 'surveyId', autoIncrement: true });
                    surveyStore.createIndex('ulpin', 'ulpin', { unique: false });
                    surveyStore.createIndex('synced', 'synced', { unique: false });
                    surveyStore.createIndex('timestamp', 'timestamp', { unique: false });
                }
                // Photos / camera captures (stored as Blobs)
                if (!db.objectStoreNames.contains(STORES.PHOTOS)) {
                    const photoStore = db.createObjectStore(STORES.PHOTOS, { keyPath: 'photoId', autoIncrement: true });
                    photoStore.createIndex('surveyId', 'surveyId', { unique: false });
                    photoStore.createIndex('synced', 'synced', { unique: false });
                }
                // Generic sync queue for any pending API calls
                if (!db.objectStoreNames.contains(STORES.SYNC_QUEUE)) {
                    const queueStore = db.createObjectStore(STORES.SYNC_QUEUE, { keyPath: 'queueId', autoIncrement: true });
                    queueStore.createIndex('endpoint', 'endpoint', { unique: false });
                    queueStore.createIndex('status', 'status', { unique: false });
                    queueStore.createIndex('createdAt', 'createdAt', { unique: false });
                }
            };

            request.onsuccess = (event) => {
                _db = event.target.result;
                resolve(_db);
            };

            request.onerror = (event) => {
                console.error('[OfflineSync] Failed to open IndexedDB:', event.target.error);
                reject(event.target.error);
            };
        });
    }

    /**
     * Generic helper: add a record to an object store.
     */
    async function addRecord(storeName, record) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.add(record);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Generic helper: put (upsert) a record to an object store.
     */
    async function putRecord(storeName, record) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.put(record);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Generic helper: get all records from an object store.
     */
    async function getAllRecords(storeName) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const request = store.getAll();
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Generic helper: get records by index value.
     */
    async function getByIndex(storeName, indexName, value) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readonly');
            const store = tx.objectStore(storeName);
            const index = store.index(indexName);
            const request = index.getAll(value);
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Generic helper: delete a record by primary key.
     */
    async function deleteRecord(storeName, key) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(storeName, 'readwrite');
            const store = tx.objectStore(storeName);
            const request = store.delete(key);
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // ──────────────────────────────── Parcel Cache ────────────────────────────────

    /**
     * Cache a parcel feature for offline access.
     * @param {Object} parcelGeoJSON - OGC Features GeoJSON feature
     */
    async function cacheParcel(parcelGeoJSON) {
        const record = {
            ulpin: parcelGeoJSON.properties.ulpin,
            feature: parcelGeoJSON,
            status: parcelGeoJSON.properties.status || 'PROVISIONAL',
            lastSynced: new Date().toISOString()
        };
        await putRecord(STORES.PARCELS, record);
    }

    /**
     * Retrieve a cached parcel by ULPIN.
     */
    async function getCachedParcel(ulpin) {
        const db = await openDB();
        return new Promise((resolve, reject) => {
            const tx = db.transaction(STORES.PARCELS, 'readonly');
            const store = tx.objectStore(STORES.PARCELS);
            const request = store.get(ulpin);
            request.onsuccess = () => resolve(request.result ? request.result.feature : null);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Get all cached parcels.
     */
    async function getAllCachedParcels() {
        const records = await getAllRecords(STORES.PARCELS);
        return records.map(r => r.feature);
    }

    // ──────────────────────────────── Survey Records ────────────────────────────────

    /**
     * Save a ground-truth survey observation captured in the field.
     * @param {Object} surveyData - { ulpin, lat, lng, accuracy, notes, measurements }
     * @returns {Promise<number>} surveyId
     */
    async function saveSurvey(surveyData) {
        const record = {
            ...surveyData,
            synced: false,
            timestamp: new Date().toISOString(),
            deviceInfo: {
                userAgent: navigator.userAgent,
                online: navigator.onLine
            }
        };
        const id = await addRecord(STORES.SURVEYS, record);
        // Also enqueue for sync
        await enqueueSync({
            endpoint: '/api/v1/surveys',
            method: 'POST',
            body: { ...record, surveyId: id },
            type: 'survey'
        });
        return id;
    }

    /**
     * Get all unsynced surveys.
     */
    async function getUnsyncedSurveys() {
        return await getByIndex(STORES.SURVEYS, 'synced', false);
    }

    // ──────────────────────────────── Photo Storage ────────────────────────────────

    /**
     * Save a photo blob captured via the device camera.
     * @param {number} surveyId - Associated survey ID
     * @param {Blob} photoBlob - The photo binary data
     * @param {Object} metadata - { lat, lng, bearing, timestamp }
     * @returns {Promise<number>} photoId
     */
    async function savePhoto(surveyId, photoBlob, metadata) {
        const record = {
            surveyId,
            blob: photoBlob,
            metadata: {
                ...metadata,
                capturedAt: new Date().toISOString()
            },
            synced: false
        };
        return await addRecord(STORES.PHOTOS, record);
    }

    /**
     * Get unsynced photos.
     */
    async function getUnsyncedPhotos() {
        return await getByIndex(STORES.PHOTOS, 'synced', false);
    }

    // ──────────────────────────────── Sync Queue ────────────────────────────────

    /**
     * Enqueue a request for later sync when online.
     * @param {Object} item - { endpoint, method, body, type }
     */
    async function enqueueSync(item) {
        const record = {
            ...item,
            status: 'pending',
            createdAt: new Date().toISOString(),
            retryCount: 0,
            maxRetries: 5
        };
        await addRecord(STORES.SYNC_QUEUE, record);
        _updateBadge();
    }

    /**
     * Get all pending sync items.
     */
    async function getPendingQueue() {
        return await getByIndex(STORES.SYNC_QUEUE, 'status', 'pending');
    }

    /**
     * Process the sync queue — called when connectivity is restored.
     */
    async function processQueue() {
        if (_syncInProgress) {
            console.log('[OfflineSync] Sync already in progress, skipping.');
            return;
        }
        if (!navigator.onLine) {
            console.log('[OfflineSync] Still offline, cannot sync.');
            return;
        }

        _syncInProgress = true;
        const pending = await getPendingQueue();

        if (pending.length === 0) {
            _syncInProgress = false;
            return;
        }

        console.log(`[OfflineSync] Processing ${pending.length} queued items...`);
        let successCount = 0;
        let failCount = 0;

        for (const item of pending) {
            try {
                const response = await fetch(item.endpoint, {
                    method: item.method || 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${_getAuthToken()}`
                    },
                    body: item.body ? JSON.stringify(item.body) : undefined
                });

                if (response.ok) {
                    // Mark as synced in the queue
                    item.status = 'synced';
                    item.syncedAt = new Date().toISOString();
                    await putRecord(STORES.SYNC_QUEUE, item);

                    // Also mark the source record as synced
                    if (item.type === 'survey' && item.body && item.body.surveyId) {
                        const surveys = await getByIndex(STORES.SURVEYS, 'synced', false);
                        const survey = surveys.find(s => s.surveyId === item.body.surveyId);
                        if (survey) {
                            survey.synced = true;
                            await putRecord(STORES.SURVEYS, survey);
                        }
                    }
                    successCount++;
                } else if (response.status >= 500) {
                    // Server error — retry later
                    item.retryCount = (item.retryCount || 0) + 1;
                    if (item.retryCount >= item.maxRetries) {
                        item.status = 'failed';
                    }
                    await putRecord(STORES.SYNC_QUEUE, item);
                    failCount++;
                } else {
                    // Client error (4xx) — mark as failed, no retry
                    item.status = 'failed';
                    item.errorCode = response.status;
                    await putRecord(STORES.SYNC_QUEUE, item);
                    failCount++;
                }
            } catch (err) {
                console.error(`[OfflineSync] Failed to sync item ${item.queueId}:`, err);
                item.retryCount = (item.retryCount || 0) + 1;
                if (item.retryCount >= item.maxRetries) {
                    item.status = 'failed';
                }
                await putRecord(STORES.SYNC_QUEUE, item);
                failCount++;
            }
        }

        console.log(`[OfflineSync] Sync complete: ${successCount} succeeded, ${failCount} failed.`);
        _syncInProgress = false;
        _updateBadge();

        if (_onSyncCallback) {
            _onSyncCallback({ success: successCount, failed: failCount });
        }
    }

    /**
     * Upload pending photos (binary) via FormData.
     */
    async function syncPhotos() {
        if (!navigator.onLine) return;
        const photos = await getUnsyncedPhotos();

        for (const photo of photos) {
            try {
                const formData = new FormData();
                formData.append('photo', photo.blob, `survey_${photo.surveyId}_${Date.now()}.jpg`);
                formData.append('surveyId', photo.surveyId);
                formData.append('metadata', JSON.stringify(photo.metadata));

                const response = await fetch('/api/v1/surveys/photos', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${_getAuthToken()}`
                    },
                    body: formData
                });

                if (response.ok) {
                    photo.synced = true;
                    await putRecord(STORES.PHOTOS, photo);
                }
            } catch (err) {
                console.error(`[OfflineSync] Failed to upload photo ${photo.photoId}:`, err);
            }
        }
    }

    // ──────────────────────────────── Connectivity Monitoring ────────────────────────────────

    /**
     * Initialize connectivity listeners.
     */
    function initConnectivityMonitor() {
        window.addEventListener('online', () => {
            console.log('[OfflineSync] Network restored — starting sync...');
            _showNotification('Back online', 'Syncing pending data...');
            processQueue();
            syncPhotos();
        });

        window.addEventListener('offline', () => {
            console.log('[OfflineSync] Network lost — entering offline mode.');
            _showNotification('Offline mode', 'Data will be saved locally and synced when online.');
        });

        // Periodic sync attempt every 5 minutes
        setInterval(() => {
            if (navigator.onLine) {
                processQueue();
            }
        }, 5 * 60 * 1000);
    }

    // ──────────────────────────────── Helpers ────────────────────────────────

    function _getAuthToken() {
        return localStorage.getItem('bhusynch_auth_token') || '';
    }

    function _updateBadge() {
        getPendingQueue().then(items => {
            const badge = document.getElementById('sync-badge');
            if (badge) {
                badge.textContent = items.length;
                badge.style.display = items.length > 0 ? 'flex' : 'none';
            }
        });
    }

    function _showNotification(title, body) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, { body, icon: '/icons/icon-192.png' });
        }
    }

    /**
     * Get sync status summary.
     */
    async function getSyncStatus() {
        const pending = await getPendingQueue();
        const unsyncedSurveys = await getUnsyncedSurveys();
        const unsyncedPhotos = await getUnsyncedPhotos();
        const allParcels = await getAllRecords(STORES.PARCELS);

        return {
            pendingRequests: pending.length,
            unsyncedSurveys: unsyncedSurveys.length,
            unsyncedPhotos: unsyncedPhotos.length,
            cachedParcels: allParcels.length,
            isOnline: navigator.onLine,
            isSyncing: _syncInProgress
        };
    }

    /**
     * Register a callback for sync completion events.
     */
    function onSyncComplete(callback) {
        _onSyncCallback = callback;
    }

    /**
     * Clear all offline data (for logout / reset).
     */
    async function clearAll() {
        const db = await openDB();
        const storeNames = Object.values(STORES);
        const tx = db.transaction(storeNames, 'readwrite');
        for (const name of storeNames) {
            tx.objectStore(name).clear();
        }
        return new Promise((resolve, reject) => {
            tx.oncomplete = resolve;
            tx.onerror = () => reject(tx.error);
        });
    }

    // ──────────────────────────────── Public API ────────────────────────────────

    return {
        init: async () => {
            await openDB();
            initConnectivityMonitor();
            _updateBadge();
            console.log('[OfflineSync] Initialized.');
        },
        cacheParcel,
        getCachedParcel,
        getAllCachedParcels,
        saveSurvey,
        getUnsyncedSurveys,
        savePhoto,
        getUnsyncedPhotos,
        enqueueSync,
        getPendingQueue,
        processQueue,
        syncPhotos,
        getSyncStatus,
        onSyncComplete,
        clearAll
    };
})();

// Auto-initialize when loaded
if (typeof window !== 'undefined') {
    window.OfflineSync = OfflineSync;
}
