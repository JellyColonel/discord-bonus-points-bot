// =================================================================
// Settings Page JavaScript
// =================================================================
// Shared utilities (isLoading, getCsrfToken, showLoading,
// hideLoading, showToast, apiCall, debounce) are loaded from common.js

// =================================================================
// VIP & Event Functions
// =================================================================

/**
 * Toggle the user's VIP status via API.
 */
async function toggleVIP() {
    const vipBadge = document.getElementById('vip-badge');
    const currentVIP = vipBadge.classList.contains('badge-vip');

    vipBadge.style.pointerEvents = 'none';

    const data = await apiCall('/api/toggle_vip', { vip_status: !currentVIP });

    vipBadge.style.pointerEvents = 'auto';

    if (!data) return;

    if (data.vip_status) {
        vipBadge.classList.remove('badge-inactive');
        vipBadge.classList.add('badge-vip');
        vipBadge.innerHTML = '&#11088; Активен';
    } else {
        vipBadge.classList.remove('badge-vip');
        vipBadge.classList.add('badge-inactive');
        vipBadge.textContent = 'Неактивен';
    }

    showToast('VIP статус ' + (data.vip_status ? 'активирован' : 'деактивирован'), 'success');
}

/**
 * Toggle the user's x2 event status via API.
 */
async function toggleEvent() {
    const eventBadge = document.getElementById('event-badge');
    const currentEvent = eventBadge.classList.contains('badge-event');

    eventBadge.style.pointerEvents = 'none';

    const data = await apiCall('/api/toggle_event', { event_status: !currentEvent });

    eventBadge.style.pointerEvents = 'auto';

    if (!data) return;

    if (data.event_status) {
        eventBadge.classList.remove('badge-inactive');
        eventBadge.classList.add('badge-event');
        eventBadge.innerHTML = '&#127881; Активно';
    } else {
        eventBadge.classList.remove('badge-event');
        eventBadge.classList.add('badge-inactive');
        eventBadge.textContent = 'Неактивно';
    }

    showToast('x2 событие ' + (data.event_status ? 'активировано' : 'деактивировано'), 'success');
}

// =================================================================
// Balance Functions
// =================================================================

/**
 * Set the user's BP balance via API.
 */
async function setBalance() {
    const input = document.getElementById('balance-input');
    const amount = parseInt(input.value);

    if (isNaN(amount) || amount < 0) {
        showToast('Пожалуйста, введите корректную сумму', 'error');
        return;
    }

    const maxBalance = parseInt(document.getElementById('balance-input').dataset.max) || 1000000;
    if (amount > maxBalance) {
        showToast(`Сумма не может превышать ${maxBalance.toLocaleString('ru-RU')} BP`, 'error');
        return;
    }

    const data = await apiCall('/api/set_balance', { amount: amount });

    if (!data) return;

    document.getElementById('current-balance').textContent = data.new_balance;
    input.value = '';
    showToast('Баланс обновлён до ' + data.new_balance + ' BP', 'success');
}

// =================================================================
// Reset Activities Functions
// =================================================================

/**
 * Reset all of today's activity completions via API.
 */
async function resetTodayActivities() {
    if (!confirm('Вы уверены? Все отметки о выполнении за сегодня будут удалены. Баланс BP не изменится.')) {
        return;
    }

    const data = await apiCall('/api/reset_today_activities');

    if (!data) return;

    showToast(`Сброшено активностей: ${data.deleted_count}. Баланс: ${data.balance} BP`, 'success');

    // Brief delay to let the user see the toast, then reload
    setTimeout(() => window.location.reload(), 1000);
}

// =================================================================
// Activity Visibility Functions
// =================================================================

/**
 * Toggle individual activity visibility.
 * @param {string} activityId - The activity identifier
 * @param {boolean} currentlyHidden - Whether the activity is currently hidden
 */
async function toggleActivityVisibility(activityId, currentlyHidden) {
    const endpoint = currentlyHidden ? '/api/unhide_activity' : '/api/hide_activity';

    const data = await apiCall(endpoint, { activity_id: activityId });

    if (!data) return;

    const item = document.querySelector('.activity-item[data-activity-id="' + activityId + '"]');
    const button = item.querySelector('button');

    if (data.hidden) {
        item.classList.add('hidden-item');
        button.classList.remove('btn-hide');
        button.classList.add('btn-show');
        button.textContent = 'Показать';
        button.onclick = () => toggleActivityVisibility(activityId, true);
    } else {
        item.classList.remove('hidden-item');
        button.classList.remove('btn-show');
        button.classList.add('btn-hide');
        button.textContent = 'Скрыть';
        button.onclick = () => toggleActivityVisibility(activityId, false);
    }

    showToast('Активность ' + (data.hidden ? 'скрыта' : 'показана'), 'success');
}

/**
 * Initialize search functionality for activities list.
 */
function initializeSearch() {
    const searchInput = document.getElementById('settings-activity-search');
    const activitiesList = document.getElementById('activities-list');
    const emptyState = document.getElementById('settings-empty-state');

    if (!searchInput) return;

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim().toLowerCase();
        const items = activitiesList.querySelectorAll('.activity-item');
        let visibleCount = 0;

        items.forEach(item => {
            const name = item.getAttribute('data-name');
            const activityId = item.getAttribute('data-activity-id').toLowerCase();

            if (name.includes(query) || activityId.includes(query)) {
                item.style.display = 'flex';
                visibleCount++;
            } else {
                item.style.display = 'none';
            }
        });

        if (visibleCount === 0) {
            emptyState.style.display = 'block';
        } else {
            emptyState.style.display = 'none';
        }
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSearch();

    const balanceInput = document.getElementById('balance-input');
    if (balanceInput) {
        balanceInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                setBalance();
            }
        });
    }
});
