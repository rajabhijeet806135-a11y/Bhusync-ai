/**
 * BhuSynch AI — Heatmap Layer
 * Renders conflict intensity and spatial dispute density.
 */
const HeatmapLayer = {
    init(map) {
        map.addSource('heatmap-source', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] },
        });

        map.addLayer({
            id: 'heatmap-layer',
            type: 'heatmap',
            source: 'heatmap-source',
            maxzoom: 19,
            paint: {
                'heatmap-weight': ['interpolate', ['linear'], ['coalesce', ['get', 'discrepancy_area_sqm'], 10.0], 0, 0.2, 50, 1.0],
                'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 11, 0.8, 17, 2.5],
                'heatmap-color': [
                    'interpolate', ['linear'], ['heatmap-density'],
                    0, 'rgba(0, 0, 0, 0)',
                    0.2, 'rgba(56, 189, 248, 0.5)',
                    0.4, 'rgba(251, 191, 36, 0.7)',
                    0.7, 'rgba(249, 115, 22, 0.85)',
                    1.0, 'rgba(239, 68, 68, 0.95)',
                ],
                'heatmap-radius': ['interpolate', ['linear'], ['zoom'], 11, 15, 17, 35],
                'heatmap-opacity': 0.80,
            },
            layout: { visibility: 'none' },
        });

        // Load conflict density
        fetch('data/statewide_west_bengal_spatial_conflicts.geojson')
            .then(r => r.json())
            .then(data => {
                const src = map.getSource('heatmap-source');
                if (src && data) src.setData(data);
            })
            .catch(() => {});
    },

    updateData(map, geojson) {
        const src = map.getSource('heatmap-source');
        if (src && geojson) src.setData(geojson);
    }
};

window.HeatmapLayer = HeatmapLayer;
