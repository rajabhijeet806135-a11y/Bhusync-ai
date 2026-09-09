/**
 * BhuSynch AI — API Client
 * REST/OGC API client for backend communication.
 */

const ApiClient = {
    getBaseUrl() {
        if (typeof window === 'undefined') return 'http://localhost:8000';
        const urlParam = new URLSearchParams(window.location.search).get('api');
        if (urlParam) return urlParam.replace(/\/+$/, '');
        if (window.BHUSYNCH_API_URL) return window.BHUSYNCH_API_URL.replace(/\/+$/, '');
        try {
            const saved = localStorage.getItem('bhusynch_api_url');
            if (saved) return saved.replace(/\/+$/, '');
        } catch (e) {}
        // Default live cloud backend on Render
        if (window.location.protocol === 'https:' && window.location.hostname !== 'localhost' && window.location.hostname !== '127.0.0.1') {
            return 'https://bhusync-api-25dk.onrender.com';
        }
        return 'http://localhost:8000';
    },

    get baseUrl() {
        return this.getBaseUrl();
    },

    async request(path, options = {}) {
        const base = this.baseUrl;
        if (!base && window.location.protocol === 'https:' && !path.startsWith('/api') && !path.startsWith('/ogc')) {
            // Standalone static cloud mode - fall back directly to static datasets
            return null;
        }
        try {
            const targetUrl = base ? `${base}${path}` : path;
            const response = await fetch(targetUrl, {
                headers: { 'Content-Type': 'application/json', ...options.headers },
                ...options,
            });
            if (!response.ok) throw new Error(`API Error: ${response.status}`);
            return await response.json();
        } catch (error) {
            console.warn(`API request failed: ${path}`, error.message);
            return null;
        }
    },

    // OGC Features
    async queryParcels(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/ogc/features/collections/parcels/items?${qs}`);
    },

    async queryConflicts(params = {}) {
        const qs = new URLSearchParams(params).toString();
        return this.request(`/ogc/features/collections/conflicts/items?${qs}`);
    },

    async getParcelByUlpin(ulpin) {
        return this.request(`/ogc/features/collections/parcels/items/${ulpin}`);
    },

    // Adjudication & Disputes
    async listConflicts() {
        return this.request('/api/v1/adjudication/conflicts');
    },

    async getConflictDetails(conflictId) {
        return this.request(`/api/v1/adjudication/conflicts/${conflictId}`);
    },

    async executeAdjudication(payload) {
        return this.request('/api/v1/adjudication/adjudicate', {
            method: 'POST',
            body: JSON.stringify(payload),
        });
    },

    // OGC Processes
    async triggerGeoreference(sajraPath, oriPath) {
        return this.request('/ogc/processes/georeference/execution', {
            method: 'POST',
            body: JSON.stringify({ sajra_path: sajraPath, reference_ori_path: oriPath }),
        });
    },

    async triggerConflation(imageryPath, legacyPath, dsmPath, dtmPath) {
        return this.request('/ogc/processes/conflation/execution', {
            method: 'POST',
            body: JSON.stringify({
                imagery_path: imageryPath,
                legacy_vectors_path: legacyPath,
                dsm_path: dsmPath,
                dtm_path: dtmPath,
            }),
        });
    },

    // Adjudication Dossier
    async generateDossier(ulpin, officerId) {
        return this.request(`/api/v1/adjudication/dossier/${ulpin}`, {
            method: 'POST',
            body: JSON.stringify({ officer_id: officerId }),
        });
    },

    // Audit
    async verifyMerkleChain(ulpin) {
        return this.request(`/api/v1/audit/verify/${ulpin}`);
    },

    async getHistory(ulpin) {
        return this.request(`/api/v1/audit/history/${ulpin}`);
    },

    // Multi-Ministry Benchmark & 7 Quality Gates
    async getMultiMinistryBenchmark(ulpin, stateCode = '27') {
        return this.request(`/api/v1/adjudication/multi-ministry-benchmark/${ulpin}?state_code=${stateCode}`);
    },

    // MVT Tiles URL
    getTileUrl() {
        return `${this.baseUrl}/ogc/tiles/parcels/{z}/{x}/{y}.pbf`;
    },
};
