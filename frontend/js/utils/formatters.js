/** BhuSynch AI — Display Formatters */
const Formatters = {
    area(sqm) {
        if (sqm == null) return '—';
        const val = parseFloat(sqm);
        if (val >= 10000) return `${(val / 10000).toFixed(2)} ha`;
        return `${val.toFixed(2)} m²`;
    },
    areaDiscrepancy(legal, observed) {
        if (legal == null || observed == null) return '—';
        const l = parseFloat(legal), o = parseFloat(observed);
        const pct = Math.abs(l - o) / l * 100;
        const sign = o > l ? '+' : '-';
        return `${sign}${pct.toFixed(1)}%`;
    },
    date(isoStr) {
        if (!isoStr) return '—';
        return new Date(isoStr).toLocaleDateString('en-IN', { year: 'numeric', month: 'short', day: 'numeric' });
    },
    hash(h) { return h ? `${h.substring(0, 8)}...${h.substring(h.length - 8)}` : '—'; },
};
