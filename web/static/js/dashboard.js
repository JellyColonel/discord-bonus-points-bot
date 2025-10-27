// =================================================================
// Dashboard Interactivity
// =================================================================

// Global state
let isLoading = false;

// Show/hide loading overlay
function showLoading() {
    document.getElementById('loading-overlay').style.display = 'flex';
    isLoading = true;
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
    isLoading = false;
}

// Show toast notification
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Toggle activity completion
async function toggleActivity(activityId, completed) {
    if (isLoading) return;
    
    showLoading();
    
    try {
        const response = await fetch('/api/toggle_activity', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                activity_id: activityId,
                completed: completed
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update balance display
            document.getElementById('balance-display').textContent = data.new_balance;
            
            // Update activity card styling
            const card = document.querySelector(`[data-activity-id="${activityId}"]`);
            if (completed) {
                card.classList.add('completed');
            } else {
                card.classList.remove('completed');
            }
            
            // Refresh stats
            await refreshStats();
            
            showToast(
                `Activity ${completed ? 'completed' : 'uncompleted'} (${data.bp_change > 0 ? '+' : ''}${data.bp_change} BP)`,
                'success'
            );
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error toggling activity:', error);
        showToast('Failed to update activity', 'error');
        
        // Revert checkbox
        const checkbox = document.getElementById(`activity-${activityId}`);
        checkbox.checked = !completed;
    } finally {
        hideLoading();
    }
}

// Set balance
async function setBalance() {
    const input = document.getElementById('balance-input');
    const amount = parseInt(input.value);
    
    if (isNaN(amount) || amount < 0) {
        showToast('Please enter a valid amount', 'error');
        return;
    }
    
    if (amount > 1000000) {
        showToast('Amount cannot exceed 1,000,000 BP', 'error');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch('/api/set_balance', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ amount: amount })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('balance-display').textContent = data.new_balance;
            input.value = '';
            showToast(`Balance updated to ${data.new_balance} BP`, 'success');
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error setting balance:', error);
        showToast('Failed to update balance', 'error');
    } finally {
        hideLoading();
    }
}

// Toggle VIP status
async function toggleVIP() {
    showLoading();
    
    try {
        // Get current VIP status from badge
        const vipBadge = document.getElementById('vip-badge');
        const currentVIP = vipBadge.classList.contains('badge-vip');
        const newVIP = !currentVIP;
        
        const response = await fetch('/api/toggle_vip', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ vip_status: newVIP })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update badge
            if (data.vip_status) {
                vipBadge.classList.remove('badge-inactive');
                vipBadge.classList.add('badge-vip');
                vipBadge.textContent = '⭐ VIP Active';
            } else {
                vipBadge.classList.remove('badge-vip');
                vipBadge.classList.add('badge-inactive');
                vipBadge.textContent = 'VIP Inactive';
            }
            
            showToast(`VIP status ${data.vip_status ? 'activated' : 'deactivated'}`, 'success');
            
            // Refresh page to update BP values
            setTimeout(() => location.reload(), 1000);
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error toggling VIP:', error);
        showToast('Failed to toggle VIP status', 'error');
    } finally {
        hideLoading();
    }
}

// Refresh statistics
async function refreshStats() {
    try {
        const response = await fetch('/api/user_data');
        const data = await response.json();
        
        // Update balance
        document.getElementById('balance-display').textContent = data.balance;
        
        // TODO: Update earned/remaining (requires recalculation)
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
    }
}

// Allow Enter key to submit balance
document.addEventListener('DOMContentLoaded', () => {
    const balanceInput = document.getElementById('balance-input');
    if (balanceInput) {
        balanceInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                setBalance();
            }
        });
    }
});

// Auto-refresh every 30 seconds (optional - commented out)
// setInterval(refreshStats, 30000);