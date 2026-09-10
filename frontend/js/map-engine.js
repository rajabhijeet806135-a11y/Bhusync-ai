/**
 * BhuSynch AI — Map Engine
 * MapLibre GL JS + 3D Extrusion + Split/Swipe Comparison Tool.
 */

const MapEngine = {
    map: null,
    is3D: false,
    isSwipeActive: false,
    swipeDivider: null,

    init(containerId, options = {}) {
        const defaultCenter = (typeof MockData !== 'undefined') ? MockData.center : [73.8567, 18.5204];
        const defaultZoom = (typeof MockData !== 'undefined') ? MockData.zoom : 17.2;

        const map = new maplibregl.Map({
            container: containerId,
            style: {
                version: 8,
                name: 'BhuSynch Cadastral Dark',
                sources: {
                    'carto-dark': {
                        type: 'raster',
                        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
                        tileSize: 256,
                        attribution: '© OpenStreetMap contributors',
                        maxzoom: 19,
                    },
                    'osm-satellite-mock': {
                        type: 'raster',
                        tiles: ['https://services.arcgisonline.com/arcgis/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'],
                        tileSize: 256,
                        attribution: '© Esri, Maxar, Earthstar Geographics',
                        maxzoom: 19,
                    },
                },
                layers: [
                    {
                        id: 'base-dark',
                        type: 'raster',
                        source: 'carto-dark',
                        minzoom: 0,
                        maxzoom: 20,
                    },
                    {
                        id: 'base-satellite',
                        type: 'raster',
                        source: 'osm-satellite-mock',
                        minzoom: 0,
                        maxzoom: 22,
                        layout: { visibility: 'none' },
                        paint: { 'raster-opacity': 0.85 },
                    },
                ],
                glyphs: 'https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf',
            },
            center: options.center || defaultCenter,
            zoom: options.zoom || defaultZoom,
            pitch: options.pitch || 0,
            bearing: options.bearing || 0,
            maxZoom: 22,
            minZoom: 4,
            attributionControl: false,
        });

        // Add controls
        map.addControl(new maplibregl.AttributionControl({ compact: true }), 'bottom-right');
        map.addControl(new maplibregl.NavigationControl({ showCompass: true, showZoom: false }), 'top-right');

        // Mouse coordinates tracker
        map.on('mousemove', (e) => {
            const latEl = document.getElementById('coord-lat');
            const lonEl = document.getElementById('coord-lon');
            const zoomEl = document.getElementById('coord-zoom');
            if (latEl) latEl.textContent = e.lngLat.lat.toFixed(6);
            if (lonEl) lonEl.textContent = e.lngLat.lng.toFixed(6);
            if (zoomEl) zoomEl.textContent = map.getZoom().toFixed(1);
        });

        // Map load handler
        map.on('load', () => {
            console.log('🗺️ [MapEngine] Initialized with layers');

            // Initialize all data layers
            ParcelLayer.init(map);
            ConflictLayer.init(map);
            ErrorEllipseLayer.init(map);
            HeatmapLayer.init(map);
            if (typeof MultiSourceProofLayer !== 'undefined') {
                MultiSourceProofLayer.init(map);
            }

            // Parcel selection click event
            map.on('click', 'parcel-fill', (e) => {
                if (e.features && e.features.length > 0) {
                    const feature = e.features[0];
                    this.highlightParcel(feature.properties.id);
                    if (typeof MultiSourceProofLayer !== 'undefined') {
                        MultiSourceProofLayer.showProofForFeature(feature);
                    }
                    ParcelInspector.show(feature.properties);

                    new maplibregl.Popup({ closeOnClick: true, maxWidth: '320px', className: 'bhusynch-popup' })
                        .setLngLat(e.lngLat)
                        .setHTML(ParcelLayer.createPopupHTML(feature.properties))
                        .addTo(map);
                }
            });

            // 3D Extrusion Click
            map.on('click', 'parcel-extrusion', (e) => {
                if (e.features && e.features.length > 0) {
                    const feature = e.features[0];
                    this.highlightParcel(feature.properties.id);
                    if (typeof MultiSourceProofLayer !== 'undefined') {
                        MultiSourceProofLayer.showProofForFeature(feature);
                    }
                    ParcelInspector.show(feature.properties);
                }
            });

            // Hover cursor styling
            map.on('mouseenter', 'parcel-fill', () => { map.getCanvas().style.cursor = 'pointer'; });
            map.on('mouseleave', 'parcel-fill', () => { map.getCanvas().style.cursor = ''; });
            map.on('mouseenter', 'parcel-extrusion', () => { map.getCanvas().style.cursor = 'pointer'; });
            map.on('mouseleave', 'parcel-extrusion', () => { map.getCanvas().style.cursor = ''; });

            // Trigger initial inspector with loaded parcel if available
            setTimeout(() => {
                if (window.BhuSynchApp && window.BhuSynchApp.loadedParcels && window.BhuSynchApp.loadedParcels.features.length > 0) {
                    const first = window.BhuSynchApp.loadedParcels.features[0];
                    MapEngine.highlightParcel(first.properties.id || first.id);
                    if (typeof MultiSourceProofLayer !== 'undefined') {
                        MultiSourceProofLayer.showProofForFeature(first);
                    }
                    ParcelInspector.show(first.properties);
                }
            }, 800);
        });

        this.map = map;
        return map;
    },

    toggleLayer(layerName, visible) {
        if (!this.map) return;

        const layerMappings = {
            'parcels': ['parcel-fill', 'parcel-outline'],
            'conflicts': ['conflict-fill', 'conflict-outline', 'conflict-labels'],
            'error-ellipses': ['error-ellipse-layer', 'error-ellipse-center'],
            'heatmap': ['heatmap-layer'],
            'satellite': ['base-satellite'],
            'multisource': [
                'proof-cadastral-line', 'proof-cadastral-fill',
                'proof-municipal-line', 'proof-municipal-fill',
                'proof-drone-line',
                'proof-building-fill', 'proof-building-line',
                'proof-cors-circle',
                'proof-harmonized-line', 'proof-harmonized-fill'
            ],
        };

        const layers = layerMappings[layerName] || [];
        layers.forEach(layerId => {
            if (this.map.getLayer(layerId)) {
                this.map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
            }
        });

        if (typeof Toast !== 'undefined') {
            Toast.info(`Layer "${layerName}" ${visible ? 'enabled' : 'disabled'}`, 1800);
        }
    },

    toggle3DView() {
        if (!this.map) return;
        this.is3D = !this.is3D;

        if (this.is3D) {
            this.map.easeTo({ pitch: 58, bearing: -24, duration: 900 });
            ParcelLayer.toggleExtrusion(this.map, true);
            const btn = document.getElementById('btn-3d-toggle');
            if (btn) btn.classList.add('active');
            if (typeof Toast !== 'undefined') Toast.success('3D LADM Extrusion Mode Activated (LiDAR/nDSM)', 2500);
        } else {
            this.map.easeTo({ pitch: 0, bearing: 0, duration: 700 });
            ParcelLayer.toggleExtrusion(this.map, false);
            const btn = document.getElementById('btn-3d-toggle');
            if (btn) btn.classList.remove('active');
            if (typeof Toast !== 'undefined') Toast.info('2D Planimetric Cadastre View', 2000);
        }
    },

    highlightParcel(parcelId) {
        if (!this.map || !this.map.getLayer('parcel-highlight')) return;
        this.map.setFilter('parcel-highlight', ['==', ['get', 'id'], parcelId]);
    },

    flyTo(lng, lat, zoom = 17) {
        if (this.map) {
            this.map.flyTo({ center: [lng, lat], zoom, speed: 1.2, curve: 1.4, essential: true });
        }
    },

    toggleSwipeMode() {
        this.isSwipeActive = !this.isSwipeActive;
        const btn = document.getElementById('btn-swipe-toggle');
        const container = document.getElementById('map-container');

        if (this.isSwipeActive) {
            if (this.map.getLayer('base-satellite')) {
                this.map.setLayoutProperty('base-satellite', 'visibility', 'visible');
            }
            if (btn) btn.classList.add('active');
            if (typeof Toast !== 'undefined') {
                Toast.success('Swipe Comparison: Drone Orthophoto vs. Cadastre Overlay', 3000);
            }
        } else {
            if (this.map.getLayer('base-satellite')) {
                this.map.setLayoutProperty('base-satellite', 'visibility', 'none');
            }
            if (btn) btn.classList.remove('active');
            if (typeof Toast !== 'undefined') {
                Toast.info('Standard Map View', 2000);
            }
        }
    },
};

window.MapEngine = MapEngine;
