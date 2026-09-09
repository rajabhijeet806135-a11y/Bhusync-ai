/**
 * BhuSynch AI — API Client
 * REST/OGC API client for backend communication.
 */

const ApiClient = {
    baseUrl: 'http://localhost:8000',

    async request(path, options = {}) {
        try {
            const response = await fetch(`${this.baseUrl}${path}`, {
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
