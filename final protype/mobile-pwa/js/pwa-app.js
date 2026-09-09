/**
 * BhuSynch AI — PWA Application Controller
 * Manages tab navigation, GPS tracking, vertex recording,
 * and survey workflow for the Mobile Ground-Truthing PWA.
 */

(function () {
    'use strict';

    // ── State ──
    const state = {
        activeTab: 'survey',
        vertices: [],
        watchId: null,
        currentPosition: null,
        isOnline: navigator.onLine
    };

    // ── DOM References ──
    const els = {
        tabBtns: document.querySelectorAll('.tab-btn'),
        tabContents: document.querySelectorAll('.tab-content'),
        syncIndicator: document.getElementById('sync-indicator'),
        gpsIndicator: document.getElementById('gps-indicator'),
        currentCoords: document.getElementById('current-coords'),
        gpsAccuracy: document.getElementById('gps-accuracy'),
        btnMarkVertex: document.getElementById('btn-mark-vertex'),
        btnClosePolygon: document.getElementById('btn-close-polygon'),
        btnTakePhoto: document.getElementById('btn-take-photo'),
        vertexCount: document.getElementById('v-count'),
        btnSyncAll: document.getElementById('btn-sync-all')
    };

    // ── Initialize ──
    function init() {
        setupTabNavigation();
        setupNetworkStatus();
        startGPSTracking();
        setupSurveyActions();
        setupSyncButton();
        console.log('[BhuSynch PWA] App initialized');
    }

    // ── Tab Navigation ──
    function setupTabNavigation() {
        els.tabBtns.forEach((btn) => {
            btn.addEventListener('click', () => {
                const tabId = btn.dataset.tab;
                state.activeTab = tabId;

                els.tabBtns.forEach((b) => b.classList.remove('active'));
                btn.classList.add('active');

                els.tabContents.forEach((content) => {
                    content.classList.toggle('active', content.id === `section-${tabId}`);
                });
            });
        });
    }

    // ── Network Status ──
    function setupNetworkStatus() {
        updateNetworkUI();
        window.addEventListener('online', () => {
            state.isOnline = true;
            updateNetworkUI();
            console.log('[BhuSynch PWA] Network: Online');
        });
        window.addEventListener('offline', () => {
            state.isOnline = false;
            updateNetworkUI();
            console.log('[BhuSynch PWA] Network: Offline');
        });
    }

    function updateNetworkUI() {
        if (els.syncIndicator) {
            els.syncIndicator.classList.toggle('online', state.isOnline);
            els.syncIndicator.classList.toggle('offline', !state.isOnline);
            els.syncIndicator.textContent = state.isOnline ? '🟢' : '🔴';
            els.syncIndicator.title = state.isOnline ? 'Online' : 'Offline';
        }
    }

    // ── GPS Tracking ──
    function startGPSTracking() {
        if (!('geolocation' in navigator)) {
            console.warn('[BhuSynch PWA] Geolocation not supported');
            if (els.gpsIndicator) els.gpsIndicator.textContent = '❌';
            return;
        }

        const options = {
            enableHighAccuracy: true,
            maximumAge: 5000,
            timeout: 15000
        };

        state.watchId = navigator.geolocation.watchPosition(
            (position) => {
                state.currentPosition = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude,
                    accuracy: position.coords.accuracy,
                    altitude: position.coords.altitude,
                    timestamp: position.timestamp
                };
                updateGPSUI(state.currentPosition);
            },
            (error) => {
                console.warn('[BhuSynch PWA] GPS error:', error.message);
                if (els.gpsIndicator) els.gpsIndicator.textContent = '⚠️';
            },
            options
        );
    }

    function updateGPSUI(pos) {
        if (els.currentCoords) {
            els.currentCoords.textContent = `Lat: ${pos.lat.toFixed(6)}, Lng: ${pos.lng.toFixed(6)}`;
        }
        if (els.gpsAccuracy) {
            els.gpsAccuracy.textContent = `Accuracy: ${pos.accuracy.toFixed(1)} m`;
        }
        if (els.gpsIndicator) {
            els.gpsIndicator.textContent = pos.accuracy < 5 ? '📡' : '📡';
            els.gpsIndicator.title = `GPS Accuracy: ${pos.accuracy.toFixed(1)}m`;
        }
    }

    // ── Survey Actions ──
    function setupSurveyActions() {
        if (els.btnMarkVertex) {
            els.btnMarkVertex.addEventListener('click', markVertex);
        }
        if (els.btnClosePolygon) {
            els.btnClosePolygon.addEventListener('click', closePolygon);
        }
        if (els.btnTakePhoto) {
            els.btnTakePhoto.addEventListener('click', () => {
                // Switch to capture tab
                document.querySelector('[data-tab="capture"]').click();
            });
        }
    }

    function markVertex() {
        if (!state.currentPosition) {
            alert('GPS position not available. Please wait for a fix.');
            return;
        }

        const vertex = {
            index: state.vertices.length,
            lat: state.currentPosition.lat,
            lng: state.currentPosition.lng,
            accuracy: state.currentPosition.accuracy,
            altitude: state.currentPosition.altitude,
            timestamp: Date.now(),
            // EPSG:7755 conversion placeholder — actual transform done via proj4
            epsg7755: {
                easting: null,
                northing: null
            }
        };

        state.vertices.push(vertex);

        if (els.vertexCount) {
            els.vertexCount.textContent = state.vertices.length;
        }

        // Haptic feedback
        if ('vibrate' in navigator) {
            navigator.vibrate(50);
        }

        console.log(`[BhuSynch PWA] Vertex ${vertex.index} recorded:`, vertex);
    }

    function closePolygon() {
        if (state.vertices.length < 3) {
            alert('Minimum 3 vertices required to close a polygon.');
            return;
        }

        const surveyData = {
            id: `survey-${Date.now()}`,
            vertices: [...state.vertices],
            vertexCount: state.vertices.length,
            timestamp: new Date().toISOString(),
            crs: 'EPSG:7755',
            status: 'pending'
        };

        // Save to IndexedDB
        saveSurveyToIndexedDB(surveyData);

        // Reset state
        state.vertices = [];
        if (els.vertexCount) els.vertexCount.textContent = '0';

        // Request background sync
        if ('serviceWorker' in navigator && 'SyncManager' in window) {
            navigator.serviceWorker.ready.then((reg) => {
                reg.sync.register('bhusynch-survey-sync');
            });
        }

        alert(`Survey saved with ${surveyData.vertexCount} vertices. Will sync when online.`);
    }

    // ── IndexedDB Storage ──
    async function saveSurveyToIndexedDB(data) {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('BhuSynchFieldDB', 1);

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('pending_surveys')) {
                    db.createObjectStore('pending_surveys', { keyPath: 'id' });
                }
            };

            request.onsuccess = () => {
                const db = request.result;
                const tx = db.transaction('pending_surveys', 'readwrite');
                const store = tx.objectStore('pending_surveys');
                store.put({ id: data.id, data: data, createdAt: Date.now() });
                tx.oncomplete = () => {
                    console.log('[BhuSynch PWA] Survey saved to IndexedDB:', data.id);
                    resolve();
                };
                tx.onerror = () => reject(tx.error);
            };

            request.onerror = () => reject(request.error);
        });
    }

    // ── Sync Button ──
    function setupSyncButton() {
        if (els.btnSyncAll) {
            els.btnSyncAll.addEventListener('click', () => {
                if (!state.isOnline) {
                    alert('No network connection. Data will sync automatically when online.');
                    return;
                }
                if ('serviceWorker' in navigator && 'SyncManager' in window) {
                    navigator.serviceWorker.ready.then((reg) => {
                        reg.sync.register('bhusynch-survey-sync');
                        console.log('[BhuSynch PWA] Manual sync triggered');
                    });
                }
            });
        }
    }

    // ── Cleanup ──
    window.addEventListener('beforeunload', () => {
        if (state.watchId !== null) {
            navigator.geolocation.clearWatch(state.watchId);
        }
    });

    // Boot
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
