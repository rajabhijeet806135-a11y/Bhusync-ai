/**
 * BhuSynch AI — Toast Notification Utility
 * Lightweight, accessible, glassmorphism notifications.
 */

const Toast = {
    container: null,

    init() {
        if (!this.container) {
            let el = document.getElementById('toast-container');
            if (!el) {
                el = document.createElement('div');
                el.id = 'toast-container';
                el.className = 'toast-container';
                el.setAttribute('role', 'region');
                el.setAttribute('aria-live', 'polite');
                el.setAttribute('aria-label', 'System notifications');
                document.body.appendChild(el);
            }
            this.container = el;
        }
    },

    show(message, type = 'info', duration = 4000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;

        const icons = {
            success: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>`,
            warning: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>`,
            danger: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="m15 9-6 6"/><path d="m9 9 6 6"/></svg>`,
            info: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>`,
        };

        toast.innerHTML = `
            <span class="toast__icon" aria-hidden="true">${icons[type] || icons.info}</span>
            <span class="toast__message">${message}</span>
            <button class="toast__close" aria-label="Dismiss notification">&times;</button>
        `;

        const closeBtn = toast.querySelector('.toast__close');
        closeBtn.addEventListener('click', () => this.dismiss(toast));

        this.container.appendChild(toast);

        // Auto dismiss
        if (duration > 0) {
            setTimeout(() => this.dismiss(toast), duration);
        }

        return toast;
    },

    dismiss(toast) {
        if (!toast || !toast.parentNode) return;
        toast.classList.add('toast--hiding');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    },

    success(msg, duration) { return this.show(msg, 'success', duration); },
    warning(msg, duration) { return this.show(msg, 'warning', duration); },
    danger(msg, duration) { return this.show(msg, 'danger', duration); },
    info(msg, duration) { return this.show(msg, 'info', duration); },
};

window.Toast = Toast;
