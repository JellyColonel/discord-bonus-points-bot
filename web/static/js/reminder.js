// =================================================================
// Returning User Reminder
// =================================================================
// Self-contained single-screen reminder modal for users inactive 14+ days.
// Uses apiCall from common.js.

/** @type {boolean} Reminder VIP toggle state (initialized from DOM) */
let reminderVIP = false;

/** @type {boolean} Reminder event toggle state (initialized from DOM) */
let reminderEvent = false;

/**
 * Initialize reminder state from DOM badge classes.
 */
function initializeReminder() {
    const vipBadge = document.getElementById('reminder-vip-badge');
    const eventBadge = document.getElementById('reminder-event-badge');
    if (vipBadge) {
        reminderVIP = vipBadge.classList.contains('badge-vip');
    }
    if (eventBadge) {
        reminderEvent = eventBadge.classList.contains('badge-event');
    }
}

/**
 * Toggle VIP badge in the reminder modal.
 */
function reminderToggleVIP() {
    reminderVIP = !reminderVIP;
    const badge = document.getElementById('reminder-vip-badge');
    if (reminderVIP) {
        badge.className = 'badge badge-vip';
        badge.textContent = '⭐ Активен';
    } else {
        badge.className = 'badge badge-inactive';
        badge.textContent = 'Неактивен';
    }
}

/**
 * Toggle event badge in the reminder modal.
 */
function reminderToggleEvent() {
    reminderEvent = !reminderEvent;
    const badge = document.getElementById('reminder-event-badge');
    if (reminderEvent) {
        badge.className = 'badge badge-event';
        badge.textContent = '🎉 Активно';
    } else {
        badge.className = 'badge badge-inactive';
        badge.textContent = 'Неактивно';
    }
}

/**
 * Dismiss the reminder. Optionally save changed settings first.
 * @param {boolean} saveChanges - Whether to save balance/VIP/event before dismissing
 */
async function reminderDismiss(saveChanges) {
    if (saveChanges) {
        // Save balance
        const balanceInput = document.getElementById('reminder-balance');
        const balanceValue = parseInt(balanceInput.value, 10);
        if (!isNaN(balanceValue) && balanceValue >= 0) {
            const balanceResult = await apiCall('/api/set_balance', { amount: balanceValue }, { overlay: false });
            if (!balanceResult) return;
        }

        // Save VIP
        const vipResult = await apiCall('/api/toggle_vip', { vip_status: reminderVIP }, { overlay: false });
        if (!vipResult) return;

        // Save event
        const eventResult = await apiCall('/api/toggle_event', { event_status: reminderEvent }, { overlay: false });
        if (!eventResult) return;
    }

    // Dismiss the reminder on the server
    const dismissResult = await apiCall('/api/dismiss_reminder', {}, { overlay: false });
    if (!dismissResult) return;

    // Remove overlay
    const overlay = document.getElementById('reminder-overlay');
    if (overlay) overlay.remove();

    // Reload if changes were saved to reflect new settings
    if (saveChanges) {
        window.location.reload();
    }
}

// Self-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('reminder-overlay');
    if (overlay) {
        initializeReminder();
    }
});
