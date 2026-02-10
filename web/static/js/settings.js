// =================================================================
// Settings Page JavaScript
// =================================================================
// Shared utilities (isLoading, getCsrfToken, showLoading,
// hideLoading, showToast) are loaded from common.js

// =================================================================
// VIP & Event Functions
// =================================================================

/**
 * Toggle the user's VIP status via API.
 */
async function toggleVIP() {
    if (isLoading) return;

    showLoading();

    const vipBadge = document.getElementById('vip-badge');
    vipBadge.style.pointerEvents = 'none';

    try {
        const currentVIP = vipBadge.classList.contains('badge-vip');
        const newVIP = !currentVIP;

        const response = await fetch('/api/toggle_vip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ vip_status: newVIP })
        });

        const data = await response.json();

        if (data.success) {
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
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error toggling VIP:', error);
        showToast('Не удалось изменить VIP статус', 'error');
    } finally {
        hideLoading();
        vipBadge.style.pointerEvents = 'auto';
    }
}

/**
 * Toggle the user's x2 event status via API.
 */
async function toggleEvent() {
    if (isLoading) return;

    showLoading();

    const eventBadge = document.getElementById('event-badge');
    eventBadge.style.pointerEvents = 'none';

    try {
        const currentEvent = eventBadge.classList.contains('badge-event');
        const newEvent = !currentEvent;

        const response = await fetch('/api/toggle_event', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ event_status: newEvent })
        });

        const data = await response.json();

        if (data.success) {
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
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error toggling event:', error);
        showToast('Не удалось изменить статус события', 'error');
    } finally {
        hideLoading();
        eventBadge.style.pointerEvents = 'auto';
    }
}

// =================================================================
// Balance Functions
// =================================================================

/**
 * Set the user's BP balance via API.
 */
async function setBalance() {
    if (isLoading) return;

    const input = document.getElementById('balance-input');
    const amount = parseInt(input.value);

    if (isNaN(amount) || amount < 0) {
        showToast('Пожалуйста, введите корректную сумму', 'error');
        return;
    }

    if (amount > 1000000) {
        showToast('Сумма не может превышать 1,000,000 BP', 'error');
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/set_balance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ amount: amount })
        });

        const data = await response.json();

        if (data.success) {
            document.getElementById('current-balance').textContent = data.new_balance;
            input.value = '';
            showToast('Баланс обновлён до ' + data.new_balance + ' BP', 'success');
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error setting balance:', error);
        showToast('Не удалось обновить баланс', 'error');
    } finally {
        hideLoading();
    }
}

// =================================================================
// Reset Activities Functions
// =================================================================

/**
 * Reset all of today's activity completions via API.
 */
async function resetTodayActivities() {
    if (isLoading) return;

    if (!confirm('Вы уверены? Все отметки о выполнении за сегодня будут удалены. Баланс BP не изменится.')) {
        return;
    }

    showLoading();

    try {
        const response = await fetch('/api/reset_today_activities', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            }
        });

        const data = await response.json();

        if (data.success) {
            showToast(`Сброшено активностей: ${data.deleted_count}. Баланс: ${data.balance} BP`, 'success');
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error resetting activities:', error);
        showToast('Не удалось сбросить активности', 'error');
    } finally {
        hideLoading();
    }
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
    if (isLoading) return;

    showLoading();

    const endpoint = currentlyHidden ? '/api/unhide_activity' : '/api/hide_activity';

    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ activity_id: activityId })
        });

        const data = await response.json();

        if (data.success) {
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
        } else {
            showToast(data.error || 'Ошибка', 'error');
        }
    } catch (error) {
        console.error('Error toggling activity:', error);
        showToast('Не удалось изменить видимость активности', 'error');
    } finally {
        hideLoading();
    }
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
