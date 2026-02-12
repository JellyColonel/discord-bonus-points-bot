// =================================================================
// Dashboard Interactivity
// =================================================================
// Shared utilities (isLoading, getCsrfToken, showLoading,
// hideLoading, showToast, apiCall, debounce) are loaded from common.js

/** @type {string} Local storage key for filters */
const FILTER_STORAGE_KEY = 'bp_dashboard_filters';

/** @type {string} Current active tab ('active' or 'completed') */
let currentTab = 'active';

// =================================================================
// Timestamp Functions
// =================================================================

/**
 * Format a UTC ISO timestamp to local "\u0432 HH:MM" string.
 * @param {string} utcTimestamp - UTC ISO timestamp
 * @returns {string} Formatted time string or empty string
 */
function formatCompletionTime(utcTimestamp) {
    if (!utcTimestamp) return '';
    const date = new Date(utcTimestamp);
    if (isNaN(date.getTime())) return '';
    return `\u0432 ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
}

/**
 * Initialize timestamps on all activity cards from data attributes.
 */
function initializeTimestamps() {
    document.querySelectorAll('.activity-card').forEach(card => {
        const ts = card.getAttribute('data-completed-at');
        const el = card.querySelector('.activity-timestamp');
        if (ts && el) {
            el.textContent = formatCompletionTime(ts);
            el.style.display = '';
        }
    });
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
    let activeCount = 0;
    let completedCount = 0;

    cards.forEach(card => {
        const cardType = card.getAttribute('data-type');
        const cardTime = card.getAttribute('data-time');
        const cardName = card.getAttribute('data-name') || '';
        const cardId = card.getAttribute('data-activity-id').toLowerCase();
        const isCompleted = card.getAttribute('data-completed') === 'true';
        const isRepeatable = card.getAttribute('data-repeatable') === 'true';

        // Count for tabs (before other filters)
        // Repeatable cards always count as active
        if (isRepeatable) {
            activeCount++;
        } else if (isCompleted) {
            completedCount++;
        } else {
            activeCount++;
        }

        let visible = true;

        // Filter by tab (active vs completed)
        // Repeatable cards always show in active tab, never in completed
        if (isRepeatable) {
            if (currentTab === 'completed') {
                visible = false;
            }
        } else if (currentTab === 'active' && isCompleted) {
            visible = false;
        } else if (currentTab === 'completed' && !isCompleted) {
            visible = false;
        }

        // Filter by type
        if (visible && filters.type !== 'all' && cardType !== filters.type) {
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

    // Update tab counts
    document.getElementById('active-count').textContent = activeCount;
    document.getElementById('completed-tab-count').textContent = completedCount;

    // Update filter results count
    const tabTotal = currentTab === 'active' ? activeCount : completedCount;
    document.getElementById('visible-count').textContent = visibleCount;
    document.getElementById('filtered-total').textContent = tabTotal;

    // Show/hide empty state with context-aware messages
    if (visibleCount === 0) {
        emptyState.style.display = 'block';
        activityGrid.style.display = 'none';

        const emptyIcon = document.getElementById('empty-icon');
        const emptyTitle = document.getElementById('empty-title');
        const emptyDescription = document.getElementById('empty-description');
        const emptyAction = document.getElementById('empty-action');

        if (tabTotal === 0) {
            // No activities in this tab at all
            if (currentTab === 'active') {
                emptyIcon.textContent = '\uD83C\uDF89';
                emptyTitle.textContent = 'Все активности выполнены!';
                emptyDescription.textContent = 'Отличная работа! Посмотрите выполненные во вкладке "Выполненные"';
                emptyAction.textContent = 'Выполненные';
                emptyAction.onclick = () => switchTab('completed');
            } else {
                emptyIcon.textContent = '\uD83D\uDCCB';
                emptyTitle.textContent = 'Нет выполненных активностей';
                emptyDescription.textContent = 'Выполненные активности появятся здесь';
                emptyAction.textContent = 'К активным';
                emptyAction.onclick = () => switchTab('active');
            }
        } else {
            // Filtered out
            emptyIcon.textContent = '\uD83D\uDD0D';
            emptyTitle.textContent = 'Нет активностей по фильтрам';
            emptyDescription.textContent = 'Попробуйте изменить фильтры или сбросить их';
            emptyAction.textContent = 'Сбросить фильтры';
            emptyAction.onclick = resetFilters;
        }
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
 * Switch to a different tab.
 * @param {string} tab - The tab to switch to ('active' or 'completed')
 */
function switchTab(tab) {
    currentTab = tab;

    // Update tab button styles
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === tab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Re-apply filters with new tab
    applyFilters();

    // Save tab preference with date
    localStorage.setItem('bp_dashboard_tab', JSON.stringify({
        tab: tab,
        date: new Date().toDateString()
    }));
}

/**
 * Initialize tab event listeners.
 */
function initializeTabs() {
    // Load saved tab preference (only if from today)
    try {
        const saved = localStorage.getItem('bp_dashboard_tab');
        if (saved) {
            const parsed = JSON.parse(saved);
            if (parsed.date === new Date().toDateString()) {
                if (parsed.tab === 'active' || parsed.tab === 'completed') {
                    currentTab = parsed.tab;
                }
            }
        }
    } catch {
        // Legacy format or corrupted — ignore
    }

    // Set initial active state
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.getAttribute('data-tab') === currentTab) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }

        // Add click listeners
        btn.addEventListener('click', () => {
            switchTab(btn.getAttribute('data-tab'));
        });
    });
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
    const card = document.querySelector(`[data-activity-id="${activityId}"]`);
    if (card) card.style.pointerEvents = 'none';

    const data = await apiCall('/api/toggle_activity', {
        activity_id: activityId,
        completed: completed
    }, { overlay: false });

    if (card) card.style.pointerEvents = '';

    if (!data) {
        revertCheckbox(activityId, completed);
        return;
    }

    if (card) {
        // Update data attribute first (needed for filtering)
        card.setAttribute('data-completed', completed ? 'true' : 'false');

        // Hide card immediately (before visual transition)
        card.classList.add('filter-hidden');

        // Update visual state (will be visible when user switches tabs)
        if (completed) {
            card.classList.add('completed');
        } else {
            card.classList.remove('completed');
        }

        // Update BP value display if it changed
        const bpElement = card.querySelector('.bp-value');
        if (bpElement && data.bp_change) {
            bpElement.textContent = `${Math.abs(data.bp_change)} BP`;
        }

        // Update timestamp
        const tsEl = card.querySelector('.activity-timestamp');
        if (tsEl) {
            if (completed && data.completed_at) {
                card.setAttribute('data-completed-at', data.completed_at);
                tsEl.textContent = formatCompletionTime(data.completed_at);
                tsEl.style.display = '';
            } else {
                card.setAttribute('data-completed-at', '');
                tsEl.textContent = '';
                tsEl.style.display = 'none';
            }
        }
    }

    // Update balance display
    document.getElementById('balance-display').textContent = data.new_balance;

    // Refresh stats and tab counts
    await refreshStats();
    applyFilters();

    showToast(
        `Активность ${completed ? 'выполнена' : 'отменена'} (${data.bp_change > 0 ? '+' : ''}${data.bp_change} BP)`,
        'success'
    );
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

        if (!response.ok) return;

        const data = await response.json();

        if (data.success) {
            // Update balance
            if (data.balance !== undefined) {
                document.getElementById('balance-display').textContent = data.balance;
            }

            // Update earned/remaining
            if (data.total_earned !== undefined) {
                document.getElementById('earned-display').textContent = '+' + data.total_earned;
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
        // Skip repeatable cards — they use +/- buttons, not click-to-toggle
        if (card.getAttribute('data-repeatable') === 'true') return;

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
// Repeatable Activity Functions
// =================================================================

/**
 * Add or remove a repeatable activity completion via API.
 * @param {string} activityId - The activity identifier
 * @param {string} action - "add" or "remove"
 */
async function repeatActivity(activityId, action) {
    const card = document.querySelector(`[data-activity-id="${activityId}"]`);
    if (card) card.style.pointerEvents = 'none';

    const data = await apiCall('/api/repeatable_activity', {
        activity_id: activityId,
        action: action
    }, { overlay: false });

    if (card) card.style.pointerEvents = '';

    if (!data) return;

    if (card) {
        const count = data.count;
        card.setAttribute('data-repeat-count', count);

        // Update counter display
        const countEl = card.querySelector('.repeat-count');
        if (countEl) countEl.textContent = count;

        // Update BP display
        const bpEl = card.querySelector('.bp-value');
        if (bpEl) {
            if (count > 0) {
                bpEl.textContent = `${data.total_bp} BP`;
            } else {
                bpEl.textContent = `${card.getAttribute('data-bp')} BP`;
            }
        }

        // Update remove button state
        const removeBtn = card.querySelector('.repeat-btn-remove');
        if (removeBtn) {
            if (count === 0) {
                removeBtn.disabled = true;
                removeBtn.classList.add('disabled');
            } else {
                removeBtn.disabled = false;
                removeBtn.classList.remove('disabled');
            }
        }

        // Update add button state (max completions cap)
        const addBtn = card.querySelector('.repeat-btn-add');
        if (addBtn) {
            const maxCompletions = data.max_completions || parseInt(card.getAttribute('data-max-completions'));
            if (maxCompletions && count >= maxCompletions) {
                addBtn.disabled = true;
                addBtn.classList.add('disabled');
            } else {
                addBtn.disabled = false;
                addBtn.classList.remove('disabled');
            }
        }

        // Update timestamp
        const tsEl = card.querySelector('.activity-timestamp');
        if (tsEl) {
            if (data.completed_at) {
                card.setAttribute('data-completed-at', data.completed_at);
                tsEl.textContent = formatCompletionTime(data.completed_at);
                tsEl.style.display = '';
            } else if (count === 0) {
                card.setAttribute('data-completed-at', '');
                tsEl.textContent = '';
                tsEl.style.display = 'none';
            }
        }
    }

    // Update balance display
    document.getElementById('balance-display').textContent = data.new_balance;

    // Refresh stats
    await refreshStats();

    const bpText = data.bp_change > 0 ? `+${data.bp_change}` : `${data.bp_change}`;
    showToast(`${action === 'add' ? 'Выполнение добавлено' : 'Выполнение удалено'} (${bpText} BP)`, 'success');
}

// =================================================================
// Onboarding Functions
// =================================================================

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

// =================================================================
// Returning User Reminder Functions
// =================================================================

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

// =================================================================
// Initialization
// =================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize onboarding if present (before other init)
    const onboardingOverlay = document.getElementById('onboarding-overlay');
    if (onboardingOverlay) {
        onboardingUpdateUI();
    }

    // Initialize returning user reminder if present
    const reminderOverlay = document.getElementById('reminder-overlay');
    if (reminderOverlay) {
        initializeReminder();
    }

    // Initialize tabs first (before filters)
    initializeTabs();

    // Initialize filters (loads from storage and applies)
    initializeFilters();

    // Initialize search
    initializeSearch();

    // Make cards clickable
    initializeClickableCards();

    // Initialize completion timestamps
    initializeTimestamps();
});
