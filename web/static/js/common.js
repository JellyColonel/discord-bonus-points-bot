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
 * Display a toast notification message with stacking support.
 * @param {string} message - The message to display
 * @param {'success'|'error'} [type='success'] - The type of notification
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.setAttribute('role', 'alert');
    toast.textContent = message;

    // Stack toasts by offsetting from existing ones
    const existing = document.querySelectorAll('.toast');
    let offset = 24;
    existing.forEach(t => {
        offset += t.offsetHeight + 8;
    });
    toast.style.bottom = offset + 'px';

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

/**
 * Make a POST API call with CSRF and error handling.
 * @param {string} url - The API endpoint URL
 * @param {Object} [body] - The request body (will be JSON-stringified)
 * @param {Object} [options] - Additional options
 * @param {boolean} [options.overlay=true] - Whether to show the loading overlay
 * @returns {Promise<Object|null>} The response data, or null on failure
 */
async function apiCall(url, body, options = {}) {
    const useOverlay = options.overlay !== false;

    if (isLoading) return null;

    if (useOverlay) showLoading();

    try {
        const options = {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        };
        if (body !== undefined) {
            options.body = JSON.stringify(body);
        }

        const response = await fetch(url, options);

        if (!response.ok) {
            const text = await response.text();
            let errorMsg;
            try {
                const data = JSON.parse(text);
                errorMsg = data.error || `Ошибка сервера (${response.status})`;
            } catch {
                errorMsg = `Ошибка сервера (${response.status})`;
            }
            showToast(errorMsg, 'error');
            return null;
        }

        const data = await response.json();

        if (!data.success) {
            showToast(data.error || 'Произошла ошибка', 'error');
            return null;
        }

        return data;
    } catch (error) {
        console.error(`API error (${url}):`, error);
        showToast('Не удалось выполнить запрос', 'error');
        return null;
    } finally {
        if (useOverlay) hideLoading();
    }
}

/**
 * Creates a debounced version of a function.
 * @param {Function} func - The function to debounce
 * @param {number} wait - The delay in milliseconds
 * @returns {Function} The debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
