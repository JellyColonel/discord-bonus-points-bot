// =================================================================
// Onboarding Flow
// =================================================================
// Self-contained 3-step onboarding modal for first-login users.
// Uses apiCall from common.js.

/** @type {number} Current onboarding step index */
let onboardingStep = 0;

/** @type {boolean} Onboarding VIP toggle state */
let onboardingVIP = false;

/** @type {boolean} Onboarding event toggle state */
let onboardingEvent = false;

/**
 * Update onboarding UI to show the current step.
 */
function onboardingUpdateUI() {
    const steps = document.querySelectorAll('.onboarding-step');
    const dots = document.querySelectorAll('.onboarding-dot');
    const backBtn = document.getElementById('onboarding-back');
    const nextBtn = document.getElementById('onboarding-next');
    const skipBtn = document.getElementById('onboarding-skip');

    steps.forEach((step, i) => {
        step.classList.toggle('active', i === onboardingStep);
    });
    dots.forEach((dot, i) => {
        dot.classList.toggle('active', i === onboardingStep);
    });

    backBtn.style.display = onboardingStep > 0 ? '' : 'none';
    nextBtn.textContent = onboardingStep === 3 ? 'Готово' : 'Далее';
    skipBtn.style.display = onboardingStep === 3 ? 'none' : '';
}

/**
 * Toggle VIP badge in the onboarding modal.
 */
function onboardingToggleVIP() {
    onboardingVIP = !onboardingVIP;
    const badge = document.getElementById('onboarding-vip-badge');
    if (onboardingVIP) {
        badge.className = 'badge badge-vip';
        badge.textContent = '⭐ Активен';
    } else {
        badge.className = 'badge badge-inactive';
        badge.textContent = 'Неактивен';
    }
}

/**
 * Toggle event badge in the onboarding modal.
 */
function onboardingToggleEvent() {
    onboardingEvent = !onboardingEvent;
    const badge = document.getElementById('onboarding-event-badge');
    if (onboardingEvent) {
        badge.className = 'badge badge-event';
        badge.textContent = '🎉 Активно';
    } else {
        badge.className = 'badge badge-inactive';
        badge.textContent = 'Неактивно';
    }
}

/**
 * Save the current onboarding step's data via existing API.
 * @returns {Promise<boolean>} Whether the save succeeded
 */
async function onboardingSaveStep() {
    if (onboardingStep === 1) {
        // Save balance
        const input = document.getElementById('onboarding-balance');
        const value = parseInt(input.value, 10);
        if (isNaN(value) || value < 0) return true; // Skip invalid, treat as 0
        const data = await apiCall('/api/set_balance', { amount: value }, { overlay: false });
        return data !== null;
    } else if (onboardingStep === 2) {
        // Save VIP
        const data = await apiCall('/api/toggle_vip', { vip_status: onboardingVIP }, { overlay: false });
        return data !== null;
    } else if (onboardingStep === 3) {
        // Save event
        const data = await apiCall('/api/toggle_event', { event_status: onboardingEvent }, { overlay: false });
        return data !== null;
    }
    return true;
}

/**
 * Advance to the next onboarding step. On last step, close and reload.
 */
async function onboardingNext() {
    const saved = await onboardingSaveStep();
    if (!saved) return;

    if (onboardingStep < 3) {
        onboardingStep++;
        onboardingUpdateUI();
    } else {
        // Done — reload to reflect new settings
        window.location.reload();
    }
}

/**
 * Go back to the previous onboarding step.
 */
function onboardingBack() {
    if (onboardingStep > 0) {
        onboardingStep--;
        onboardingUpdateUI();
    }
}

/**
 * Skip onboarding entirely — create user row with defaults and close.
 */
async function onboardingSkip() {
    const data = await apiCall('/api/complete_onboarding', {}, { overlay: false });
    if (data) {
        document.getElementById('onboarding-overlay').remove();
    }
}

// Self-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('onboarding-overlay');
    if (overlay) {
        onboardingUpdateUI();
    }
});
