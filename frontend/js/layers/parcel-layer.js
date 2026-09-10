/**
 * BhuSynch AI — Parcel Layer
 * Supports standard 2D parcel polygons and 3D LADM extrusions (LiDAR/nDSM heights).
 * Features automatic dual-source loading (FastAPI OGC API with seamless local GeoJSON fallback).
 */
const ParcelLayer = {
    init(map) {
        map.addSource('parcels-source', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] },
            generateId: true,
        });

        // 2D Fill Layer — Status-based color coding
        map.addLayer({
            id: 'parcel-fill',
            type: 'fill',
            source: 'parcels-source',
            paint: {
                'fill-color': [
                    'match', ['get', 'status'],
                    'VERIFIED', 'rgba(16, 185, 129, 0.40)',
                    'ADJUDICATED', 'rgba(99, 102, 241, 0.40)',
                    'CANDIDATE', 'rgba(59, 130, 246, 0.35)',
                    'rgba(245, 158, 11, 0.35)', // PROVISIONAL
                ],
                'fill-opacity': 0.85,
            },
        });

        // 2D Outline Layer with high-contrast borders
        map.addLayer({
            id: 'parcel-outline',
            type: 'line',
            source: 'parcels-source',
            paint: {
                'line-color': [
                    'match', ['get', 'status'],
                    'VERIFIED', '#10B981',
                    'ADJUDICATED', '#818CF8',
                    'CANDIDATE', '#38BDF8',
                    '#F59E0B',
                ],
                'line-width': 2.0,
                'line-opacity': 0.95,
            },
        });

        // 3D Extrusion Layer (LADM 3D Multi-Storey Cadastre)
        map.addLayer({
            id: 'parcel-extrusion',
            type: 'fill-extrusion',
            source: 'parcels-source',
            layout: { visibility: 'none' },
            paint: {
                'fill-extrusion-color': [
                    'match', ['get', 'status'],
                    'VERIFIED', '#059669',
                    'ADJUDICATED', '#6366F1',
                    'CANDIDATE', '#0284C7',
                    '#D97706',
                ],
                'fill-extrusion-height': ['coalesce', ['get', 'height_m'], 12.0],
                'fill-extrusion-base': 0,
                'fill-extrusion-opacity': 0.85,
            },
        });

        // Highlight selection layer
        map.addLayer({
            id: 'parcel-highlight',
            type: 'line',
            source: 'parcels-source',
            paint: {
                'line-color': '#22D3EE',
                'line-width': 4.0,
                'line-opacity': 1.0,
            },
            filter: ['==', ['get', 'id'], ''],
        });

        // Initial data load for West Bengal
        const defaultState = (window.BhuSynchApp && window.BhuSynchApp.currentState) ? window.BhuSynchApp.currentState : '19';
        this.loadData(map, defaultState);
    },

    async loadData(map, stateCode = '19') {
        let geojson = null;

        // 1. Try live FastAPI backend
        if (typeof ApiClient !== 'undefined') {
            try {
                const apiRes = await ApiClient.queryParcels({ state_code: stateCode, limit: 1000 });
                if (apiRes && apiRes.features && apiRes.features.length > 0) {
                    geojson = apiRes;
                    console.log(`📡 [ParcelLayer] Live-loaded ${geojson.features.length} parcels from FastAPI OGC API`);
                }
            } catch (e) {
                console.warn('[ParcelLayer] API fetch error, switching to authentic local data:', e);
            }
        }

        // 2. Direct authentic local GeoJSON fallback
        if (!geojson || !geojson.features || geojson.features.length === 0) {
            const fileMap = {
                '20_ranchi_piska': 'data/ranchi_piska_more_cadastral_parcels.geojson',
                'piska_more': 'data/ranchi_piska_more_cadastral_parcels.geojson',
                '20_piska': 'data/ranchi_piska_more_cadastral_parcels.geojson',
                '20_ranchi': 'data/ranchi_jharkhand_cadastral_parcels.geojson',
                'ranchi': 'data/ranchi_jharkhand_cadastral_parcels.geojson',
                '20': 'data/ranchi_jharkhand_cadastral_parcels.geojson',
                '19_west_medinipur': 'data/west_medinipur_cadastral_parcels.geojson',
                '19_medinipur': 'data/west_medinipur_cadastral_parcels.geojson',
                '19_rishra': 'data/rishra_hooghly_cadastral_parcels.geojson',
                '19': 'data/statewide_west_bengal_cadastral_parcels.geojson',
                '19_statewide': 'data/statewide_west_bengal_cadastral_parcels.geojson',
                '19_darjeeling': 'data/statewide_west_bengal_cadastral_parcels.geojson',
                '19_bardhaman': 'data/statewide_west_bengal_cadastral_parcels.geojson',
                '19_sundarbans': 'data/statewide_west_bengal_cadastral_parcels.geojson',
                '27': 'data/real_pune_ward_14_cadastral_parcels.geojson',
            };
            const targetPath = fileMap[stateCode] || 'data/statewide_west_bengal_cadastral_parcels.geojson';

            try {
                const resp = await fetch(targetPath);
                if (resp.ok) {
                    geojson = await resp.json();
                    console.log(`📦 [ParcelLayer] Loaded ${geojson.features.length} authentic parcels from ${targetPath}`);
                }
            } catch (err) {
                console.error('[ParcelLayer] Failed to load local parcel file:', err);
            }
        }

        if (geojson && map) {
            const source = map.getSource('parcels-source');
            if (source) {
                source.setData(geojson);
            }
            if (window.BhuSynchApp) {
                window.BhuSynchApp.loadedParcels = geojson;
            }

            // Generate error ellipses & heatmap from authentic parcel centroids/vertices
            if (window.ErrorEllipseLayer && window.ErrorEllipseLayer.updateFromParcels) {
                window.ErrorEllipseLayer.updateFromParcels(map, geojson);
            }

            // Immediately display the first parcel in inspector
            if (geojson.features && geojson.features.length > 0) {
                const first = geojson.features[0];
                if (window.MapEngine) {
                    MapEngine.highlightParcel(first);
                }
                if (window.ParcelInspector && first.properties) {
                    ParcelInspector.show(first.properties);
                }
            }
        }
    },

    createPopupHTML(props) {
        const statusColors = {
            VERIFIED: '#10B981',
            ADJUDICATED: '#818CF8',
            CANDIDATE: '#38BDF8',
            PROVISIONAL: '#F59E0B',
        };
        const statusColor = statusColors[props.status] || '#F59E0B';

        const isJharkhand = String(props.ulpin || '').startsWith('20') || props.state_code === '20' || props.state === 'Jharkhand' || (window.BhuSynchApp && window.BhuSynchApp.currentState && window.BhuSynchApp.currentState.startsWith('20'));
        const isMaharashtra = String(props.ulpin || '').startsWith('27') || props.state_code === '27' || props.state === 'Maharashtra' || (window.BhuSynchApp && window.BhuSynchApp.currentState === '27');

        let khasraLabel, ownerName, areaUnit;
        if (isJharkhand) {
            khasraLabel = `खेसरा #${props.khasra_no || props.dag_no || '—'}`;
            ownerName = props.rayat_name || props.owner_name || '—';
            areaUnit = props.legal_area_decimal ? `(${props.legal_area_decimal} डिसमिल)` : '';
        } else if (isMaharashtra) {
            khasraLabel = `Gat #${props.khasra_no || props.gat_no || '—'}`;
            ownerName = props.owner_name || '—';
            areaUnit = '';
        } else {
            khasraLabel = props.dag_no ? `দাগ #${props.dag_no}` : (props.khasra_no ? `Khasra #${props.khasra_no}` : '—');
            ownerName = props.owner_name_bengali ? `${props.owner_name_bengali} (${props.owner_name_english})` : (props.owner_name || '—');
            areaUnit = props.area_in_satak ? `(${props.area_in_satak} শতক)` : '';
        }

        return `
            <div class="parcel-popup">
                <div class="parcel-popup__header">
                    <span class="parcel-popup__khasra">${khasraLabel}</span>
                    <span class="parcel-popup__status" style="background: ${statusColor}22; color: ${statusColor}; border: 1px solid ${statusColor}66;">
                        ${props.status || 'PROVISIONAL'}
                    </span>
                </div>
                <div class="parcel-popup__body">
                    <div class="parcel-popup__row">
                        <span class="label">ULPIN</span>
                        <span class="value mono">${props.ulpin || '—'}</span>
                    </div>
                    <div class="parcel-popup__row">
                        <span class="label">${isJharkhand ? 'रैयत (Owner)' : 'Owner'}</span>
                        <span class="value font-medium">${ownerName}</span>
                    </div>
                    <div class="parcel-popup__row">
                        <span class="label">Legal Area</span>
                        <span class="value">${props.legal_area_sqm ? props.legal_area_sqm + ' m²' : '—'} ${areaUnit}</span>
                    </div>
                    <div class="parcel-popup__row">
                        <span class="label">Physical Area</span>
                        <span class="value">${props.observed_area_sqm || props.physical_area_sqm ? (props.observed_area_sqm || props.physical_area_sqm) + ' m²' : '—'}</span>
                    </div>
                    ${props.has_conflict ? `
                    <div class="parcel-popup__conflict-alert">
                        ⚠️ <strong>Conflict:</strong> ${props.conflict_type || 'Spatial Discrepancy'}
                    </div>` : ''}
                    ${props.cnt_act_section46_restricted ? `
                    <div class="parcel-popup__conflict-alert" style="background: rgba(245, 158, 11, 0.15); border: 1px solid rgba(245, 158, 11, 0.4); color: #FBBF24;">
                        🛡️ <strong>CNT Act Sec 46:</strong> ST Raiyati Land
                    </div>` : ''}
                </div>
                <button class="parcel-popup__btn" onclick="ParcelInspector.showFromUlpin('${props.ulpin}')">
                    Inspect Full Dossier &rarr;
                </button>
            </div>
        `;
    },

    toggleExtrusion(map, enable) {
        if (!map) return;
        if (map.getLayer('parcel-extrusion')) {
            map.setLayoutProperty('parcel-extrusion', 'visibility', enable ? 'visible' : 'none');
        }
        if (map.getLayer('parcel-fill')) {
            map.setLayoutProperty('parcel-fill', 'visibility', enable ? 'none' : 'visible');
        }
    },
};

window.ParcelLayer = ParcelLayer;
