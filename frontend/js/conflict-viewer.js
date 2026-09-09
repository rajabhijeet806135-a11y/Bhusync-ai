/**
 * BhuSynch AI — Conflict Viewer
 * Three-Truths conflict visualization (Cases A/B/C).
 */
const ConflictViewer = {
    show(conflict) {
        console.log('Conflict details:', conflict);
    },
    getColor(severity) {
        switch (severity) {
            case 'CRITICAL': return '#ef4444';
            case 'MEDIUM': return '#f59e0b';
            case 'LOW': return '#3b82f6';
            default: return '#64748b';
        }
    },
};
