/**
 * BhuSynch AI — Main Application Initialization
 * Orchestrates map, layers, inspector, and UI components.
 * 
 * Architecture: Section 1 (Client Presentation Tier)
 * Design: ui-ux-pro-max — GSAP stagger, reduced-motion, stat counters
 */

const BhuSynchApp = {
    map: null,
    currentState: '20_ranchi_piska', // Default: Ranchi Piska More & Ratu Road Hub (State 20)
    config: {
        apiBaseUrl: 'http://localhost:8000',
        states: {
            '20_ranchi_piska': {
                name: 'Jharkhand — Ranchi: Piska More & Ratu Road Hub (Hehal/Pandra)',
                center: [85.3050, 23.3820],
                zoom: 15.8,
                pitch: 45,
                bearing: -5,
                corsName: 'CORS RNC1 Active (Survey of India Ranchi)',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 503, verified: 480, conflicts: 23, avgRmse: 0.039 },
                chips: [
                    { ulpin: '20340204000272', label: 'Dominoz Pizza (Piska More Chowk)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '20340204000071', label: 'विवेकानंद अस्पताल (Hehal Thana 204)', color: '#10B981', bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.35)' },
                    { ulpin: '20340204000238', label: 'Mall of Ranchi (Ratu Road Hub)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                    { ulpin: '20340204000116', label: 'प्रमिला कुंज (Pandra Thana 203)', color: '#A5B4FC', bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.35)' },
                ]
            },
            '20_ranchi': {
                name: 'Jharkhand — Ranchi Capital City (Morabadi/Dhurwa/Main Rd)',
                center: [85.3340, 23.3441],
                zoom: 14.8,
                pitch: 42,
                bearing: -6,
                corsName: 'CORS RNC1 Active (Survey of India Ranchi)',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 350, verified: 332, conflicts: 18, avgRmse: 0.041 },
                chips: [
                    { ulpin: '20340000000101', label: 'प्लॉट १०१ (Morabadi CNT Act)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '20340000000102', label: 'प्लॉट २०२ (Subarnarekha Buffer)', color: '#FCA5A5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)' },
                    { ulpin: '20340000000103', label: 'प्लॉट ३०৩ (NH-20 Ring Road)', color: '#10B981', bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.35)' },
                    { ulpin: '20340000000104', label: 'प्लॉट ४०৪ (Harmu Rejuvenation)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                ]
            },
            '19_west_medinipur': {
                name: 'West Bengal — West Medinipur (Midnapore & Kharagpur)',
                center: [87.3105, 22.3850],
                zoom: 14.8,
                pitch: 42,
                bearing: -8,
                corsName: 'CORS KGP1 Active (Survey of India Kharagpur)',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 350, verified: 335, conflicts: 15, avgRmse: 0.042 },
                chips: [
                    { ulpin: '191833372909', label: 'দাগ ১০১ (New Wagon Workshop)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '191833763160', label: 'দাগ ১০২ (SE Railway Kharagpur)', color: '#10B981', bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.35)' },
                    { ulpin: '191834132992', label: 'দাগ ১০৩ (Nimpura Industrial)', color: '#FCA5A5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)' },
                    { ulpin: '191834073007', label: 'দাগ ১০৪ (Hijli / IIT Campus)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                ]
            },
            '19_rishra': {
                name: 'West Bengal — Rishra & Serampore (Hooghly District)',
                center: [88.3450, 22.7150],
                zoom: 16.5,
                pitch: 45,
                bearing: -12,
                corsName: 'CORS KOL1 Active (Survey of India)',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 300, verified: 285, conflicts: 15, avgRmse: 0.045 },
                chips: [
                    { ulpin: '191472693545', label: 'দাগ ১০১ (Jayshree Textiles)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '191471503505', label: 'দাগ ১০২ (Hastings Jute Mill)', color: '#10B981', bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.35)' },
                    { ulpin: '191472933375', label: 'দাগ ১০৩ (Rishra Municipality)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                    { ulpin: '191472893459', label: 'দাগ ১০৪ (Eastern Railway)', color: '#A5B4FC', bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.35)' },
                ]
            },
            '19_statewide': {
                name: 'West Bengal — All 23 Districts (Statewide Cadastre)',
                center: [88.3697, 22.5726],
                zoom: 12.5,
                pitch: 35,
                bearing: -5,
                corsName: 'CORS KOL1 Active',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 200, verified: 185, conflicts: 15, avgRmse: 0.048 },
                chips: [
                    { ulpin: '19010410100001', label: 'দাগ ১০১/১ (Bastu)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '19011420100004', label: 'দাগ ১০১/৪ (KMDA RoW)', color: '#FCA5A5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)' },
                    { ulpin: '19011420100012', label: 'দাগ ১০৩/৪ (Gas Buffer)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                    { ulpin: '19010410100025', label: 'দাগ ১০৭/১ (Drainage Buffer)', color: '#A5B4FC', bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.35)' },
                ]
            },
            '19': {
                name: 'West Bengal — Bidhannagar Sector V / KMC (State 19)',
                center: [88.4325, 22.5697],
                zoom: 16.8,
                pitch: 42,
                bearing: -10,
                corsName: 'CORS KOL1 Active',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 200, verified: 185, conflicts: 15, avgRmse: 0.048 },
                chips: [
                    { ulpin: '19010410100001', label: 'দাগ ১০১/১ (Bastu)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '19011420100004', label: 'দাগ ১০১/৪ (KMDA RoW)', color: '#FCA5A5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)' },
                    { ulpin: '19011420100012', label: 'দাগ ১০৩/৪ (Gas Buffer)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                    { ulpin: '19010410100025', label: 'দাগ ১০৭/১ (Drainage Buffer)', color: '#A5B4FC', bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.35)' },
                ]
            },
            '19_darjeeling': {
                name: 'West Bengal — Darjeeling & Siliguri (North Bengal)',
                center: [88.3953, 26.7271],
                zoom: 14.5,
                pitch: 38,
                bearing: -8,
                corsName: 'CORS SLG1 Active',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 85, verified: 78, conflicts: 7, avgRmse: 0.052 },
                chips: [
                    { ulpin: '19013440100007', label: 'দাগ ৪২/১ (Matigara)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '19013440100015', label: 'দাগ ৪৮/৩ (Teesta Blue Line)', color: '#FCA5A5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)' },
                ]
            },
            '19_bardhaman': {
                name: 'West Bengal — Paschim Bardhaman (Asansol-Durgapur)',
                center: [87.3119, 23.5204],
                zoom: 14.8,
                pitch: 35,
                bearing: -5,
                corsName: 'CORS DUR1 Active',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 95, verified: 88, conflicts: 7, avgRmse: 0.050 },
                chips: [
                    { ulpin: '19014450100008', label: 'দাগ ৫২/২ (City Centre)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '19014450100016', label: 'দাগ ৬০/১ (Damodar RoW)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                ]
            },
            '19_sundarbans': {
                name: 'West Bengal — South 24 Parganas & Sundarbans',
                center: [88.7500, 21.8500],
                zoom: 11.5,
                pitch: 25,
                bearing: 0,
                corsName: 'CORS KOL1 / Forest Base',
                crsBadge: 'EPSG:7755 (India 45N)',
                stats: { totalParcels: 50, verified: 48, conflicts: 2, avgRmse: 0.055 },
                chips: [
                    { ulpin: '19011420100001', label: 'Biosphere Reserve Exclusion', color: '#10B981', bg: 'rgba(16,185,129,0.15)', border: 'rgba(16,185,129,0.35)' },
                ]
            },
            '27': {
                name: 'Maharashtra — Pune Ward 14 (State 27)',
                center: [73.8567, 18.5204],
                zoom: 17.2,
                pitch: 40,
                bearing: -15,
                corsName: 'CORS PUNE PUN1 Active',
                crsBadge: 'EPSG:7755 (India 43N)',
                stats: { totalParcels: 150, verified: 138, conflicts: 12, avgRmse: 0.048 },
                chips: [
                    { ulpin: '27010410010001', label: 'Gat 118/1 (Sadashiv Peth)', color: '#38BDF8', bg: 'rgba(8,145,178,0.15)', border: 'rgba(8,145,178,0.35)' },
                    { ulpin: '27010410010002', label: 'Gat 118/2 (DP 24m RoW)', color: '#FCA5A5', bg: 'rgba(239,68,68,0.15)', border: 'rgba(239,68,68,0.35)' },
                    { ulpin: '27010410010005', label: 'Gat 120/A (Mutha Nallah)', color: '#FBBF24', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.35)' },
                    { ulpin: '27010410010003', label: 'Gat 119/1 (Gaothan Mixed)', color: '#A5B4FC', bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.35)' },
                ]
            }
        }
    },
    loadedParcels: null,
    prefersReducedMotion: false,

    async init() {
        console.log('[BhuSynch AI] Initializing National Urban Cadastral Console...');

        this.prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

        const select = document.getElementById('jurisdiction-select');
        if (select && select.value) {
            this.currentState = select.value;
        }

        const defaultState = this.config.states[this.currentState] || this.config.states['20_ranchi_piska'];

        // Initialize map
        this.map = MapEngine.init('map', {
            center: defaultState.center,
            zoom: defaultState.zoom,
            pitch: defaultState.pitch,
            bearing: defaultState.bearing,
        });

        // Set up event listeners
        this.setupJurisdictionSelector();
        this.setupLayerToggles();
        this.setupMapControls();
        this.setupSearch();
        this.setupInspectorClose();

        // Render chips for default state
        const chipsContainer = document.getElementById('search-chips-container');
        if (chipsContainer && defaultState.chips) {
            chipsContainer.innerHTML = defaultState.chips.map(chip => `
                <button class="chip" onclick="ParcelInspector.showFromUlpin('${chip.ulpin}')" 
                    style="background: ${chip.bg}; border: 1px solid ${chip.border}; color: ${chip.color}; border-radius: 4px; padding: 2px 6px; font-size: 0.68rem; cursor: pointer;">
                    ${chip.label}
                </button>
            `).join('');
        }

        // Load initial data with animated counters
        await this.loadStats(this.currentState);

        // GSAP stagger animation on sidebar sections
        this.animateSidebarEntrance();

        // Populate featured parcel in Cadastral Dossier so 3-column layout is immediately visible
        setTimeout(() => {
            if (defaultState.chips && defaultState.chips[0] && window.ParcelInspector) {
                ParcelInspector.showFromUlpin(defaultState.chips[0].ulpin);
            }
        }, 600);

        console.log('[BhuSynch AI] Ready with West Bengal & Maharashtra multi-ministry feeds.');
    },

    setupJurisdictionSelector() {
        const select = document.getElementById('jurisdiction-select');
        if (!select) return;

        select.addEventListener('change', async (e) => {
            const newState = e.target.value;
            await this.switchJurisdiction(newState);
        });
    },

    async switchJurisdiction(stateCode) {
        this.currentState = stateCode;
        const stateConf = this.config.states[stateCode];
        if (!stateConf) return;

        console.log(`[BhuSynch AI] Switching jurisdiction to: ${stateConf.name}`);

        // Update UI Badges
        const corsLabel = document.getElementById('cors-status-label');
        if (corsLabel) corsLabel.textContent = stateConf.corsName;

        const crsBadge = document.getElementById('crs-badge');
        if (crsBadge) crsBadge.textContent = stateConf.crsBadge;

        // Update Search Chips
        const chipsContainer = document.getElementById('search-chips-container');
        if (chipsContainer && stateConf.chips) {
            chipsContainer.innerHTML = stateConf.chips.map(chip => `
                <button class="chip" onclick="ParcelInspector.showFromUlpin('${chip.ulpin}')" 
                    style="background: ${chip.bg}; border: 1px solid ${chip.border}; color: ${chip.color}; border-radius: 4px; padding: 2px 6px; font-size: 0.68rem; cursor: pointer;">
                    ${chip.label}
                </button>
            `).join('');
        }

        // Fly camera to new region
        if (this.map) {
            this.map.flyTo({
                center: stateConf.center,
                zoom: stateConf.zoom,
                pitch: stateConf.pitch,
                bearing: stateConf.bearing,
                duration: 1800,
                essential: true
            });
        }

        // Reload Map Layers with state_code parameter
        await this.reloadLayersForState(stateCode);

        // Reload Stats
        await this.loadStats(stateCode);

        if (typeof Toast !== 'undefined') {
            Toast.success(`Switched to ${stateConf.name}`, 3000);
        }
    },

    async reloadLayersForState(stateCode) {
        if (this.map) {
            if (window.ParcelLayer && window.ParcelLayer.loadData) {
                await ParcelLayer.loadData(this.map, stateCode);
            }
            if (window.ConflictLayer && window.ConflictLayer.loadData) {
                await ConflictLayer.loadData(this.map, stateCode);
            }
        }
    },

    animateSidebarEntrance() {
        if (this.prefersReducedMotion || typeof gsap === 'undefined') return;

        const sections = document.querySelectorAll('.sidebar__section');
        if (sections.length === 0) return;

        gsap.from(sections, {
            opacity: 0,
            y: 12,
            duration: 0.4,
            stagger: { each: 0.08, from: 'start' },
            ease: 'back.out(1.2)',
            clearProps: 'all',
        });
    },

    animateCounter(elementId, targetValue, duration = 1.2) {
        const el = document.getElementById(elementId);
        if (!el) return;

        if (this.prefersReducedMotion || typeof gsap === 'undefined') {
            el.textContent = targetValue;
            return;
        }

        const numericStr = String(targetValue).replace(/[^0-9.]/g, '');
        const numericVal = parseFloat(numericStr);

        if (isNaN(numericVal)) {
            el.textContent = targetValue;
            return;
        }

        const isDecimal = String(targetValue).includes('.');
        const hasCommas = String(targetValue).includes(',');
        const obj = { val: 0 };

        gsap.to(obj, {
            val: numericVal,
            duration: duration,
            ease: 'power2.out',
            delay: 0.2,
            onUpdate: () => {
                let display;
                if (isDecimal) {
                    display = obj.val.toFixed(2);
                } else {
                    const rounded = Math.round(obj.val);
                    display = hasCommas ? rounded.toLocaleString('en-IN') : String(rounded);
                }
                el.textContent = display;
            },
        });
    },

    setupLayerToggles() {
        const toggles = {
            'toggle-parcels': 'parcels',
            'toggle-conflicts': 'conflicts',
            'toggle-ellipses': 'error-ellipses',
            'toggle-heatmap': 'heatmap',
            'toggle-satellite': 'satellite',
        };

        Object.entries(toggles).forEach(([toggleId, layerName]) => {
            const el = document.getElementById(toggleId);
            if (el) {
                const checkbox = el.querySelector('input[type="checkbox"]');
                if (checkbox) {
                    checkbox.addEventListener('change', () => {
                        MapEngine.toggleLayer(layerName, checkbox.checked);
                    });
                }
            }
        });
    },

    setupMapControls() {
        document.getElementById('btn-zoom-in')?.addEventListener('click', () => {
            this.map?.zoomIn({ duration: 300 });
        });
        document.getElementById('btn-zoom-out')?.addEventListener('click', () => {
            this.map?.zoomOut({ duration: 300 });
        });
        document.getElementById('btn-3d-toggle')?.addEventListener('click', () => {
            MapEngine.toggle3DView();
        });
        document.getElementById('btn-swipe-toggle')?.addEventListener('click', () => {
            MapEngine.toggleSwipeMode();
        });
        document.getElementById('btn-north')?.addEventListener('click', () => {
            this.map?.resetNorth({ duration: 400 });
        });
    },

    setupSearch() {
        const searchInput = document.getElementById('search-ulpin');
        if (!searchInput) return;

        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const query = searchInput.value.trim();
                if (!query) return;

                if (window.ParcelInspector && ParcelInspector.showFromUlpin) {
                    ParcelInspector.showFromUlpin(query);
                }
            }
        });
    },

    setupInspectorClose() {
        document.getElementById('inspector-close')?.addEventListener('click', () => {
            const panel = document.getElementById('inspector-panel');
            if (panel) panel.style.display = 'none';
            if (typeof MapEngine !== 'undefined' && MapEngine.map) {
                setTimeout(() => MapEngine.map.resize(), 100);
            }
        });
    },

    async loadStats(stateCode = '19') {
        const stateConf = this.config.states[stateCode] || this.config.states['19'];
        const stats = stateConf.stats;

        this.animateCounter('stat-total-parcels', stats.totalParcels);
        this.animateCounter('stat-verified', stats.verified);
        this.animateCounter('stat-conflicts', stats.conflicts);
        this.animateCounter('stat-rmse', stats.avgRmse + ' m');

        // Dynamic Concordance Micro-Donut Update (44x44px)
        const total = stats.totalParcels || 1;
        const verified = stats.verified || 0;
        const conflicts = stats.conflicts || 0;
        const concordancePct = (verified / total) * 100;
        const disputePct = (conflicts / total) * 100;

        const circumference = 106.814;
        const offset = circumference * (1 - concordancePct / 100);

        const donutFill = document.getElementById('sidebar-donut-fill');
        const donutVal = document.getElementById('sidebar-donut-val');
        const pctEl = document.getElementById('sidebar-concordance-pct');

        if (donutFill) donutFill.style.strokeDashoffset = offset.toFixed(1);
        if (donutVal) donutVal.textContent = Math.round(concordancePct) + '%';
        if (pctEl) pctEl.textContent = concordancePct.toFixed(1) + '%';
    },
};

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    BhuSynchApp.init();
});

window.BhuSynchApp = BhuSynchApp;
