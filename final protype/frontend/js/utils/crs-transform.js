/** BhuSynch AI — Client-side CRS Transform Utilities */
const CRSTransform = {
    // Simplified EPSG:7755 ↔ WGS84 for client-side display
    // Full transforms done server-side via pyproj
    toWGS84(x, y) { return { lat: y, lon: x }; },
    fromWGS84(lon, lat) { return { x: lon, y: lat }; },
};
