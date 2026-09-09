/**
 * BhuSynch AI — Conflict Layer
 * Renders conflict polygon highlights and blinking/pulsing conflict borders.
 */
const ConflictLayer = {
    init(map) {
        map.addSource('conflicts', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] },
        });

        // Fill layer with severity-colored glass shading
        map.addLayer({
            id: 'conflict-fill',
            type: 'fill',
            source: 'conflicts',
            paint: {
                'fill-color': [
                    'match', ['get', 'severity'],
                    'CRITICAL', 'rgba(239, 68, 68, 0.45)',
                    'MEDIUM', 'rgba(245, 158, 11, 0.40)',
                    'rgba(59, 130, 246, 0.35)', // LOW
                ],
                'fill-opacity': 0.8,
            },
        });

        // Pulsing / dashed outline
        map.addLayer({
            id: 'conflict-outline',
            type: 'line',
            source: 'conflicts',
            paint: {
                'line-color': [
                    'match', ['get', 'severity'],
                    'CRITICAL', '#EF4444',
                    'MEDIUM', '#F59E0B',
                    '#38BDF8',
                ],
                'line-width': 2.5,
                'line-dasharray': [2, 2],
            },
        });

        // Conflict symbol / label
        map.addLayer({
            id: 'conflict-labels',
            type: 'symbol',
            source: 'conflicts',
            layout: {
                'text-field': ['concat', '[!] ', ['coalesce', ['get', 'conflict_type'], ['get', 'type'], 'Dispute']],
                'text-size': 11,
                'text-offset': [0, -1],
                'text-anchor': 'bottom',
                'text-font': ['Noto Sans Regular'],
            },
            paint: {
                'text-color': '#FEF08A',
                'text-halo-color': '#0F172A',
                'text-halo-width': 2,
            },
        });

        const defaultState = (window.BhuSynchApp && window.BhuSynchApp.currentState) ? window.BhuSynchApp.currentState : '19';
        this.loadData(map, defaultState);
    },

    async loadData(map, stateCode = '19') {
        let geojson = null;

        // 1. Try FastAPI backend
        if (typeof ApiClient !== 'undefined') {
            try {
                const apiRes = await ApiClient.queryConflicts({ state_code: stateCode, limit: 100 });
                if (apiRes && apiRes.features && apiRes.features.length > 0) {
                    geojson = apiRes;
                }
            } catch (e) {
                console.warn('[ConflictLayer] API query error, using local conflict file', e);
            }
        }

        // 2. Direct authentic local GeoJSON fallback
        if (!geojson || !geojson.features || geojson.features.length === 0) {
            let targetPath = 'data/statewide_west_bengal_spatial_conflicts.geojson';
            if (stateCode === '27') {
                targetPath = 'data/real_pune_ward_14_spatial_conflicts.geojson';
            } else if (stateCode === '20_ranchi_piska' || stateCode === 'piska_more' || stateCode === '20_piska') {
                targetPath = 'data/ranchi_piska_more_dispute_cases.geojson';
            } else if (stateCode === '20_ranchi' || stateCode === 'ranchi' || stateCode === '20') {
                targetPath = 'data/ranchi_jharkhand_dispute_cases.geojson';
            } else if (stateCode === '19_west_medinipur' || stateCode === '19_medinipur') {
                targetPath = 'data/west_medinipur_dispute_cases.geojson';
            } else if (stateCode === '19_rishra') {
                targetPath = 'data/rishra_hooghly_dispute_cases.geojson';
            }

            try {
                const resp = await fetch(targetPath);
                if (resp.ok) {
                    geojson = await resp.json();
                }
            } catch (err) {
                console.warn('[ConflictLayer] Failed to load local conflict file:', err);
            }
        }

        if (geojson && map) {
            const source = map.getSource('conflicts');
            if (source) source.setData(geojson);
            console.log(`⚠️ [ConflictLayer] Active conflicts loaded (${geojson.features ? geojson.features.length : 0} cases)`);
        }
    },

    updateData(map, geojson) {
        const source = map.getSource('conflicts');
        if (source) source.setData(geojson);
    },
};

window.ConflictLayer = ConflictLayer;
