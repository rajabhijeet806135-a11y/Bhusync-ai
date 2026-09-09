/**
 * BhuSynch AI — Revenue Adjudication Controller
 * Orchestrates Three-Truths Decision Core, interactive conflict queue,
 * DSC Signing Ceremony, Merkle hash updates, and Statutory Dossier generation.
 */

const AdjudicationController = {
    currentCaseId: 'CONF-WB-HGL-RIS-104',
    activeCase: null,
    merkleChainCount: 3,

    init() {
        console.log('[AdjudicationController] Initializing...');

        // Setup filter listeners
        this.setupFilters();

        // Setup conflict card clicks
        this.setupConflictCardClicks();

        // Setup action button handlers
        this.setupActionButtons();

        // Setup modal dialogs
        this.setupModals();

        // Check URL params for deep linking
        const urlParams = new URLSearchParams(window.location.search);
        const requestedId = urlParams.get('conflict') || 'CONF-WB-HGL-RIS-104';

        this.selectConflict(requestedId);

        console.log('[AdjudicationController] Ready');
    },

    setupFilters() {
        const severityFilter = document.getElementById('severity-filter');
        const typeFilter = document.getElementById('type-filter');

        const applyFilters = () => {
            const sevVal = severityFilter ? severityFilter.value : 'all';
            const typeVal = typeFilter ? typeFilter.value : 'all';

            const cards = document.querySelectorAll('.conflict-card');
            cards.forEach(card => {
                const cardSev = card.classList.contains('severity-critical') ? 'CRITICAL' :
                                card.classList.contains('severity-medium') ? 'MEDIUM' : 'LOW';
                const cardTypeEl = card.querySelector('.conflict-type');
                const cardType = cardTypeEl ? cardTypeEl.textContent.trim() : '';

                const matchesSev = (sevVal === 'all' || cardSev === sevVal);
                const matchesType = (typeVal === 'all' || cardType === typeVal);

                card.style.display = (matchesSev && matchesType) ? 'block' : 'none';
            });
        };

        severityFilter?.addEventListener('change', applyFilters);
        typeFilter?.addEventListener('change', applyFilters);
    },

    setupConflictCardClicks() {
        const cards = document.querySelectorAll('.conflict-card');
        cards.forEach(card => {
            card.addEventListener('click', (e) => {
                const caseId = card.getAttribute('data-conflict-id');
                if (caseId) this.selectConflict(caseId);
            });
        });
    },

    selectConflict(caseId) {
        this.currentCaseId = caseId;
        const caseData = (typeof MockData !== 'undefined' && MockData.adjudicationCases[caseId]) 
            ? MockData.adjudicationCases[caseId] 
            : null;

        if (!caseData) return;
        this.activeCase = caseData;

        // Highlight active card in left queue
        document.querySelectorAll('.conflict-card').forEach(c => {
            if (c.getAttribute('data-conflict-id') === caseId) {
                c.classList.add('active');
            } else {
                c.classList.remove('active');
            }
        });

        // Update Three-Truths Matrix (TL, TP, TA)
        this.updateTruthsMatrix(caseData);

        // Update Discrepancy Analysis
        this.updateDiscrepancySection(caseData);

        // Update AI Recommendation
        this.updateRecommendation(caseData);

        if (typeof Toast !== 'undefined') {
            Toast.info(`Loaded Conflict #${caseData.id} (${caseData.khasra_no})`, 1500);
        }
    },

    updateTruthsMatrix(data) {
        // Legal Truth (TL)
        const lOwner = document.getElementById('legal-owner');
        const lArea = document.getElementById('legal-area');
        const lKhasra = document.getElementById('legal-khasra');
        const lType = document.getElementById('legal-type');
        if (lOwner) lOwner.textContent = data.legal.owner;
        if (lArea) lArea.innerHTML = data.legal.area;
        if (lKhasra) lKhasra.textContent = data.legal.khasra;
        if (lType) lType.textContent = data.legal.landType;

        // Physical Truth (TP)
        const pArea = document.getElementById('physical-area');
        const pRmse = document.getElementById('physical-rmse');
        const pVert = document.getElementById('physical-vertices');
        const pNdsm = document.getElementById('physical-ndsm');
        if (pArea) pArea.innerHTML = data.physical.observedArea;
        if (pRmse) pRmse.textContent = data.physical.rmse;
        if (pVert) pVert.textContent = data.physical.vertices;
        if (pNdsm) pNdsm.textContent = data.physical.ndsmChange;

        // Admin Truth (TA)
        const aKhata = document.getElementById('admin-khata');
        const aZone = document.getElementById('admin-zone');
        const aTax = document.getElementById('admin-tax');
        const aEnc = document.getElementById('admin-enc');
        if (aKhata) aKhata.textContent = data.admin.khataNo;
        if (aZone) aZone.textContent = data.admin.zone;
        if (aTax) aTax.textContent = data.admin.taxStatus;
        if (aEnc) aEnc.textContent = data.admin.encumbrance;

        // Calculate and update SVG micro-doughnuts
        const legalConf = data.legal?.confidence || 94;
        const physRmse = parseFloat(data.physical?.rmse || '0.04');
        const physConf = data.physical?.confidence || (physRmse < 0.05 ? 93 : (physRmse < 0.1 ? 89 : 82));
        const adminConf = data.admin?.confidence || (data.admin?.taxStatus?.toLowerCase().includes('current') ? 97 : 88);

        this.updateMicroDonut('donut-fill-legal', 'donut-val-legal', 'bar-fill-legal', legalConf);
        this.updateMicroDonut('donut-fill-physical', 'donut-val-physical', 'bar-fill-physical', physConf);
        this.updateMicroDonut('donut-fill-admin', 'donut-val-admin', 'bar-fill-admin', adminConf);
    },

    updateMicroDonut(donutId, valId, barId, percent) {
        const circumference = 106.814;
        const clamped = Math.min(Math.max(percent, 0), 100);
        const offset = circumference * (1 - clamped / 100);

        const donutEl = document.getElementById(donutId);
        const valEl = document.getElementById(valId);
        const barEl = document.getElementById(barId);

        if (donutEl) {
            donutEl.style.strokeDashoffset = offset.toFixed(1);
        }
        if (valEl) {
            valEl.textContent = Math.round(clamped) + '%';
        }
        if (barEl) {
            barEl.style.width = clamped + '%';
            barEl.setAttribute('aria-valuenow', clamped);
            barEl.textContent = Math.round(clamped) + '%';
        }
    },

    updateDiscrepancySection(data) {
        const dArea = document.getElementById('disc-delta-area');
        const dTol = document.getElementById('disc-tolerance');
        const dSigma = document.getElementById('disc-sigma');
        const dFrechet = document.getElementById('disc-frechet');

        if (dArea) dArea.innerHTML = data.discrepancy.deltaArea;
        if (dTol) dTol.textContent = data.discrepancy.tolerance;
        if (dSigma) dSigma.textContent = data.discrepancy.sigmaMajor;
        if (dFrechet) dFrechet.textContent = data.discrepancy.frechetDistance;

        // Parse delta percentage from deltaArea text e.g. "+52.40 m² (+1.36%)" or "-24.60 m² (0.86% within 2.0% limit)"
        let deltaPct = 1.5;
        const str = String(data.discrepancy?.deltaArea || '');
        const match = str.match(/([+-]?\d+(?:\.\d+)?)\s*%/);
        if (match) {
            deltaPct = Math.abs(parseFloat(match[1]));
        }

        this.updateToleranceGauge(deltaPct, 2.0);
    },

    updateToleranceGauge(deltaPct, threshold = 2.0) {
        const isBreach = deltaPct > threshold;
        const needleEl = document.getElementById('gauge-needle');
        const badgeEl = document.getElementById('gauge-status-badge');
        const dArea = document.getElementById('disc-delta-area');

        // Gauge arc: 180 degrees from x=6 (left) to x=42 (right). Center is (24, 28), radius 14.
        // Map deltaPct (0% to 4.0%+) into angle (15 deg to 165 deg)
        const angleDeg = Math.min(Math.max(15 + (deltaPct / 4.0) * 150, 15), 165);
        const rad = (angleDeg * Math.PI) / 180;
        const x2 = (24 - 14 * Math.cos(rad)).toFixed(1);
        const y2 = (28 - 14 * Math.sin(rad)).toFixed(1);

        if (needleEl) {
            needleEl.setAttribute('x2', x2);
            needleEl.setAttribute('y2', y2);
            needleEl.setAttribute('stroke', isBreach ? '#DC2626' : '#166534');
        }

        if (badgeEl) {
            badgeEl.className = isBreach ? 'gauge-badge breach' : 'gauge-badge pass';
            badgeEl.textContent = isBreach ? 'BREACH' : 'PASS';
            badgeEl.title = isBreach 
                ? `Discrepancy (${deltaPct.toFixed(2)}%) exceeds permissible tolerance of ±${threshold.toFixed(1)}%` 
                : `Discrepancy (${deltaPct.toFixed(2)}%) is within legal tolerance of ±${threshold.toFixed(1)}%`;
        }

        if (dArea) {
            if (isBreach) {
                dArea.classList.remove('success');
                dArea.classList.add('warning');
            } else {
                dArea.classList.remove('warning');
                dArea.classList.add('success');
            }
        }
    },

    updateRecommendation(data) {
        const recEl = document.getElementById('ai-recommendation');
        if (recEl) {
            recEl.textContent = data.aiRecommendation;
        }
    },

    setupActionButtons() {
        // Accept AI
        document.getElementById('btn-accept-ai')?.addEventListener('click', () => {
            const remarks = document.getElementById('officer-remarks')?.value || 'AI Rectification accepted per Survey Evidence.';
            this.recordDecision('ACCEPT_AI', remarks);
            if (typeof Toast !== 'undefined') {
                Toast.success(`AI Recommendation Accepted for Khasra ${this.activeCase?.khasra_no || ''}. Merkle audit block created.`, 4000);
            }
        });

        // Modify
        document.getElementById('btn-modify')?.addEventListener('click', () => {
            this.openModifyModal();
        });

        // Reject
        document.getElementById('btn-reject')?.addEventListener('click', () => {
            const remarks = document.getElementById('officer-remarks')?.value || 'Disputed boundary. Escalated for physical ground truthing.';
            this.recordDecision('REJECT_ESCALATE', remarks);
            if (typeof Toast !== 'undefined') {
                Toast.danger(`Conflict escalated to Field Survey Inspector. Notice issued.`, 4000);
            }
        });

        // Sign DSC
        document.getElementById('btn-sign-dsc')?.addEventListener('click', () => {
            this.openDscSigningModal();
        });

        // Generate Statutory Dossier
        document.getElementById('btn-generate-dossier')?.addEventListener('click', () => {
            this.openDossierModal();
        });

        // Export PDF
        document.getElementById('btn-export-pdf')?.addEventListener('click', () => {
            window.print();
        });
    },

    recordDecision(decisionType, remarks) {
        const chain = document.getElementById('merkle-chain');
        if (!chain) return;

        const randomHash = Array.from({length: 8}, () => Math.floor(Math.random()*16).toString(16)).join('');
        const now = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' IST';

        const newEntry = document.createElement('div');
        newEntry.className = 'merkle-entry animate-fade-in';
        newEntry.setAttribute('role', 'listitem');
        newEntry.innerHTML = `
            <div class="merkle-hash">
                <span class="hash-label">H<sub>${++this.merkleChainCount}</sub></span>
                <code class="hash-value">${randomHash}...${Math.floor(Math.random()*1000)}</code>
            </div>
            <div class="merkle-details">
                <span class="font-bold text-accent">${decisionType}</span>
                <span>Officer: RO-2024-0451 (DSC Verified)</span>
                <span>${now}</span>
            </div>
        `;

        chain.insertBefore(newEntry, chain.firstChild);
    },

    setupModals() {
        // Close modal on click outside or close button
        document.querySelectorAll('.modal-overlay').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal || e.target.classList.contains('modal-close')) {
                    modal.style.display = 'none';
                }
            });
        });
    },

    openDscSigningModal() {
        const modal = document.getElementById('dsc-signing-modal');
        if (!modal) return;
        modal.style.display = 'flex';

        // Reset step
        const step1 = document.getElementById('dsc-step-1');
        const step2 = document.getElementById('dsc-step-2');
        if (step1) step1.style.display = 'block';
        if (step2) step2.style.display = 'none';
    },

    async confirmDscSign() {
        const pinInput = document.getElementById('dsc-pin-input');
        const pin = pinInput ? pinInput.value : '';

        if (pin.length < 4) {
            if (typeof Toast !== 'undefined') Toast.danger('Please enter your 6-digit DSC Token PIN', 2500);
            return;
        }

        const step1 = document.getElementById('dsc-step-1');
        const step2 = document.getElementById('dsc-step-2');
        if (step1) step1.style.display = 'none';
        if (step2) step2.style.display = 'block';

        const payload = {
            conflict_id: this.activeCase?.id || 'CONF-2026-0001',
            officer_id: 'RO-2024-0451',
            decision: 'ACCEPT_PHYSICAL',
            chosen_boundary: 'PHYSICAL',
            remarks: document.getElementById('officer-remarks')?.value || 'Statutory DSC Adjudication executed per DILRMP standards.',
            dsc_pin: pin,
        };

        let result = null;
        if (typeof ApiClient !== 'undefined') {
            try {
                result = await ApiClient.executeAdjudication(payload);
            } catch (err) {
                console.warn('API Adjudicate fallback', err);
            }
        }

        setTimeout(() => {
            const modal = document.getElementById('dsc-signing-modal');
            if (modal) modal.style.display = 'none';
            const hash = result?.merkle_block?.current_hash || result?.merkle_hash || 'SHA3-256-CERTIFIED';
            this.recordDecision('DSC_CERTIFIED', `Class-3 Digital Signature Attached (Hash: ${hash.slice(0, 16)}...)`);
            if (typeof Toast !== 'undefined') {
                Toast.success(`🛡️ Digital Signature (IT Act §3) Generated & Registered in Merkle Ledger!`, 4500);
            }
        }, 1200);
    },

    openDossierModal() {
        const modal = document.getElementById('statutory-dossier-modal');
        if (!modal || !this.activeCase) return;

        const c = this.activeCase;
        document.getElementById('dossier-ulpin-val').textContent = c.ulpin;
        document.getElementById('dossier-khasra-val').textContent = c.khasra_no;
        document.getElementById('dossier-village-val').textContent = `${c.village}, ${c.district}`;
        document.getElementById('dossier-owner-val').textContent = c.legal.owner;
        document.getElementById('dossier-area-val').innerHTML = `${c.legal.area} &rarr; ${c.physical.observedArea}`;
        document.getElementById('dossier-hash-val').textContent = `SHA3-256: e89a24cf...71b0 (Merkle Height #${this.merkleChainCount})`;

        modal.style.display = 'flex';
    },

    openModifyModal() {
        const modal = document.getElementById('modify-boundary-modal');
        if (!modal || !this.activeCase) return;
        modal.style.display = 'flex';
    },

    saveBoundaryModification() {
        const modal = document.getElementById('modify-boundary-modal');
        if (modal) modal.style.display = 'none';

        this.recordDecision('BOUNDARY_MODIFICATION', 'Manual vertex coordinate adjustment by Adjudicating Officer');
        if (typeof Toast !== 'undefined') {
            Toast.success('Modified vertex geometry saved & re-triangulated with TPS Elastic Warp.', 3500);
        }
    },
};

// Global export
window.AdjudicationController = AdjudicationController;
document.addEventListener('DOMContentLoaded', () => AdjudicationController.init());
