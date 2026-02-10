// =================================================================
// Shared Utilities
// =================================================================

/** @type {boolean} Whether an API request is in progress */
let isLoading = false;

/**
 * Get CSRF token from meta tag for secure API requests.
 * @returns {string} The CSRF token
 */
function getCsrfToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (!meta) throw new Error('CSRF token meta tag not found');
    return meta.content;
}

/**
 * Show the loading overlay and set loading state.
 */
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
    isLoading = true;
}

/**
 * Hide the loading overlay and clear loading state.
 */
function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
    isLoading = false;
}

/**
 * Display a toast notification message.
 * @param {string} message - The message to display
 * @param {'success'|'error'} [type='success'] - The type of notification
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}
