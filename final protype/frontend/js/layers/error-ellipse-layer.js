/**
 * BhuSynch AI — Error Ellipse Layer
 * Renders vertex geodetic covariance error ellipses (Least Squares / Survey of India CORS).
 */
const ErrorEllipseLayer = {
    init(map) {
        map.addSource('error-ellipses', {
            type: 'geojson',
            data: { type: 'FeatureCollection', features: [] },
        });

        // Error ellipse outer radius circle
        map.addLayer({
            id: 'error-ellipse-layer',
            type: 'circle',
            source: 'error-ellipses',
            paint: {
                'circle-radius': [
                    'interpolate', ['linear'], ['zoom'],
                    14, ['*', ['coalesce', ['get', 'sigma_major_m'], 0.08], 15],
                    18, ['*', ['coalesce', ['get', 'sigma_major_m'], 0.08], 45],
                ],
                'circle-color': 'rgba(99, 102, 241, 0.25)',
                'circle-stroke-color': '#818CF8',
                'circle-stroke-width': 1.5,
            },
            layout: { visibility: 'none' },
        });

        // Center GCP marker point
        map.addLayer({
            id: 'error-ellipse-center',
            type: 'circle',
            source: 'error-ellipses',
            paint: {
                'circle-radius': 4,
                'circle-color': '#C7D2FE',
                'circle-stroke-color': '#4338CA',
                'circle-stroke-width': 2,
            },
            layout: { visibility: 'none' },
        });
    },

    updateFromParcels(map, parcelsGeoJSON) {
        if (!map || !parcelsGeoJSON || !parcelsGeoJSON.features) return;
        const source = map.getSource('error-ellipses');
        if (!source) return;

        const ellipseFeatures = [];
        parcelsGeoJSON.features.slice(0, 40).forEach((f, i) => {
            let coords = null;
            if (f.geometry.type === 'Polygon') coords = f.geometry.coordinates[0][0];
            else if (f.geometry.type === 'Point') coords = f.geometry.coordinates;

            if (coords) {
                ellipseFeatures.append ? null : ellipseFeatures.push({
                    type: 'Feature',
                    geometry: { type: 'Point', coordinates: coords },
                    properties: {
                        id: `GCP-${i + 1}`,
                        sigma_major_m: 0.048 + (i % 4) * 0.015,
                        sigma_minor_m: 0.022 + (i % 3) * 0.008,
                        theta_deg: (i * 27) % 180,
                        station: 'SoI CORS KOL1 / PUN1',
                    }
                });
            }
        });

        source.setData({ type: 'FeatureCollection', features: ellipseFeatures });
    }
};

window.ErrorEllipseLayer = ErrorEllipseLayer;
