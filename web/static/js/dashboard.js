// =================================================================
// Dashboard Interactivity
// =================================================================

/** @type {boolean} Whether an API request is in progress */
let isLoading = false;

/** @type {string} Local storage key for filters */
const FILTER_STORAGE_KEY = 'bp_dashboard_filters';

// =================================================================
// Utility Functions
// =================================================================

/**
 * Creates a debounced version of a function that delays execution
 * until after the specified wait time has elapsed since the last call.
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

/**
 * Get CSRF token from meta tag for secure API requests.
 * @returns {string} The CSRF token
 */
function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
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

// =================================================================
// Filter Functions
// =================================================================

/**
 * Get current filter values from dropdowns.
 * @returns {{type: string, time: string, search: string}}
 */
function getCurrentFilters() {
    return {
        type: document.getElementById('filter-type').value,
        time: document.getElementById('filter-time').value,
        search: document.getElementById('activity-search').value.trim().toLowerCase()
    };
}

/**
 * Save current filters to localStorage.
 */
function saveFiltersToStorage() {
    const filters = getCurrentFilters();
    // Don't save search query, only dropdowns
    const filtersToSave = {
        type: filters.type,
        time: filters.time
    };
    localStorage.setItem(FILTER_STORAGE_KEY, JSON.stringify(filtersToSave));
}

/**
 * Load filters from localStorage and apply them.
 */
function loadFiltersFromStorage() {
    try {
        const saved = localStorage.getItem(FILTER_STORAGE_KEY);
        if (saved) {
            const filters = JSON.parse(saved);
            if (filters.type) document.getElementById('filter-type').value = filters.type;
            if (filters.time) document.getElementById('filter-time').value = filters.time;
        }
    } catch (e) {
        console.error('Error loading filters from storage:', e);
    }
}

/**
 * Check if any filter is active (not "all").
 * @returns {boolean}
 */
function hasActiveFilters() {
    const filters = getCurrentFilters();
    return filters.type !== 'all' ||
           filters.time !== 'all' ||
           filters.search.length > 0;
}

/**
 * Update reset button visibility based on active filters.
 */
function updateResetButtonVisibility() {
    const resetBtn = document.getElementById('reset-filters');
    if (hasActiveFilters()) {
        resetBtn.style.display = 'inline-flex';
    } else {
        resetBtn.style.display = 'none';
    }
}

/**
 * Apply all filters and update visibility of activity cards.
 */
function applyFilters() {
    const filters = getCurrentFilters();
    const cards = document.querySelectorAll('.activity-card');
    const emptyState = document.getElementById('empty-state');
    const activityGrid = document.getElementById('activity-grid');

    let visibleCount = 0;
    const totalCount = cards.length;

    cards.forEach(card => {
        const cardType = card.getAttribute('data-type');
        const cardTime = card.getAttribute('data-time');
        const cardName = card.getAttribute('data-name') || '';
        const cardId = card.getAttribute('data-activity-id').toLowerCase();

        let visible = true;

        // Filter by type
        if (filters.type !== 'all' && cardType !== filters.type) {
            visible = false;
        }

        // Filter by time
        if (visible && filters.time !== 'all' && cardTime !== filters.time) {
            visible = false;
        }

        // Filter by search
        if (visible && filters.search.length > 0) {
            if (!cardName.includes(filters.search) && !cardId.includes(filters.search)) {
                visible = false;
            }
        }

        // Apply visibility
        if (visible) {
            card.classList.remove('filter-hidden');
            visibleCount++;
        } else {
            card.classList.add('filter-hidden');
        }
    });

    // Update counts display
    document.getElementById('visible-count').textContent = visibleCount;
    document.getElementById('filtered-total').textContent = totalCount;

    // Show/hide empty state
    if (visibleCount === 0) {
        emptyState.style.display = 'block';
        activityGrid.style.display = 'none';
    } else {
        emptyState.style.display = 'none';
        activityGrid.style.display = 'grid';
    }

    // Update reset button visibility
    updateResetButtonVisibility();

    // Save filters (dropdowns only)
    saveFiltersToStorage();
}

/**
 * Reset all filters to default values.
 */
function resetFilters() {
    document.getElementById('filter-type').value = 'all';
    document.getElementById('filter-time').value = 'all';
    document.getElementById('activity-search').value = '';
    document.getElementById('search-clear').style.display = 'none';

    applyFilters();
}

/**
 * Initialize filter event listeners.
 */
function initializeFilters() {
    // Load saved filters
    loadFiltersFromStorage();

    // Add change listeners to dropdowns
    document.getElementById('filter-type').addEventListener('change', applyFilters);
    document.getElementById('filter-time').addEventListener('change', applyFilters);

    // Reset button
    document.getElementById('reset-filters').addEventListener('click', resetFilters);

    // Apply filters on load
    applyFilters();
}

// =================================================================
// Search Functions
// =================================================================

/**
 * Initialize search functionality.
 */
function initializeSearch() {
    const searchInput = document.getElementById('activity-search');
    const searchClear = document.getElementById('search-clear');

    if (!searchInput) return;

    // Debounced search
    const debouncedApply = debounce(() => {
        applyFilters();
    }, 200);

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        if (query.length > 0) {
            searchClear.style.display = 'flex';
        } else {
            searchClear.style.display = 'none';
        }

        debouncedApply();
    });

    // Clear button
    searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchClear.style.display = 'none';
        applyFilters();
        searchInput.focus();
    });

    // Clear on Escape
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchClear.style.display = 'none';
            applyFilters();
        }
    });
}

// =================================================================
// Activity Toggle Functions
// =================================================================

/**
 * Toggle an activity's completion status via API.
 * @param {string} activityId - The activity identifier
 * @param {boolean} completed - Whether the activity is now completed
 */
async function toggleActivity(activityId, completed) {
    if (isLoading) return;

    showLoading();

    try {
        const response = await fetch('/api/toggle_activity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({
                activity_id: activityId,
                completed: completed
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update card visual state
            const card = document.querySelector(`[data-activity-id="${activityId}"]`);
            if (card) {
                if (completed) {
                    card.classList.add('completed');
                    card.setAttribute('data-completed', 'true');
                } else {
                    card.classList.remove('completed');
                    card.setAttribute('data-completed', 'false');
                }

                // Update BP value display if it changed
                const bpElement = card.querySelector('.bp-value');
                if (bpElement && data.bp_change) {
                    bpElement.textContent = `${Math.abs(data.bp_change)} BP`;
                }
            }

            // Update balance display
            document.getElementById('balance-display').textContent = data.new_balance;

            // Refresh stats
            await refreshStats();

            showToast(
                `Активность ${completed ? 'выполнена' : 'отменена'} (${data.bp_change > 0 ? '+' : ''}${data.bp_change} BP)`,
                'success'
            );
        } else {
            showToast(data.error || 'Не удалось обновить активность', 'error');
            revertCheckbox(activityId, completed);
        }
    } catch (error) {
        console.error('Error toggling activity:', error);
        showToast('Не удалось обновить активность', 'error');
        revertCheckbox(activityId, completed);
    } finally {
        hideLoading();
    }
}

/**
 * Revert checkbox state after an error.
 * @param {string} activityId - The activity identifier
 * @param {boolean} completed - The attempted state (will revert to opposite)
 */
function revertCheckbox(activityId, completed) {
    const checkbox = document.getElementById(`activity-${activityId}`);
    if (checkbox) {
        checkbox.checked = !completed;
    }
}

// =================================================================
// Data Refresh Functions
// =================================================================

/**
 * Refresh user statistics from the API.
 */
async function refreshStats() {
    try {
        const response = await fetch('/api/user_stats');
        const data = await response.json();

        if (data.success) {
            // Update balance
            if (data.balance !== undefined) {
                document.getElementById('balance-display').textContent = data.balance;
            }

            // Update earned/remaining
            if (data.total_earned !== undefined) {
                document.getElementById('earned-display').textContent = data.total_earned;
            }
            if (data.total_remaining !== undefined) {
                document.getElementById('remaining-display').textContent = data.total_remaining;
            }

            // Update progress
            if (data.completed_count !== undefined && data.total_activities !== undefined) {
                const progressFill = document.getElementById('progress-fill');
                const progressPercentage = Math.round((data.completed_count / data.total_activities) * 100);
                if (progressFill) {
                    progressFill.style.width = `${progressPercentage}%`;
                }

                document.getElementById('completed-count').textContent = data.completed_count;
                document.getElementById('total-count').textContent = data.total_activities;
            }
        }
    } catch (error) {
        console.error('Error refreshing stats:', error);
    }
}

// =================================================================
// Card Click Handler
// =================================================================

/**
 * Initialize click handlers for activity cards.
 */
function initializeClickableCards() {
    const cards = document.querySelectorAll('.activity-card');
    cards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking directly on checkbox or label
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'LABEL') {
                return;
            }

            const checkbox = this.querySelector('input[type="checkbox"]');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                const event = new Event('change', { bubbles: true });
                checkbox.dispatchEvent(event);
            }
        });
    });
}

// =================================================================
// Initialization
// =================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize filters (loads from storage and applies)
    initializeFilters();

    // Initialize search
    initializeSearch();

    // Make cards clickable
    initializeClickableCards();
});
