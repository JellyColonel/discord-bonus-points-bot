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
            
            // Get the activity card and its category
            const card = document.querySelector(`[data-activity-id="${activityId}"]`);
            const category = card.getAttribute('data-category');
            
            // Move card to appropriate tab
            moveActivityToTab(activityId, category, completed);
            
            // Update tab counts
            updateTabCounts(completed ? 1 : -1);
            
            // Refresh stats (earned/remaining)
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
        const checkbox = document.getElementById(`activity-${activityId}`) || 
                        document.getElementById(`activity-completed-${activityId}`);
        if (checkbox) {
            checkbox.checked = !completed;
        }
    } finally {
        hideLoading();
    }
}

// Set balance
async function setBalance() {
    if (isLoading) return;
    
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
    if (isLoading) return;
    
    showLoading();
    
    // Disable button to prevent multiple clicks
    const vipButton = document.getElementById('vip-toggle-btn');
    vipButton.disabled = true;
    
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
            // Update badge smoothly
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
            
            // Update all activity BP values without page reload
            await updateActivityBPValues();
        } else {
            throw new Error(data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error toggling VIP:', error);
        showToast('Failed to toggle VIP status', 'error');
    } finally {
        hideLoading();
        vipButton.disabled = false;
    }
}

// Update all activity BP values in the UI
async function updateActivityBPValues() {
    try {
        const response = await fetch('/api/activity_bp_values');
        const data = await response.json();
        
        if (data.activities) {
            // Update each activity's BP display
            Object.entries(data.activities).forEach(([activityId, bpValue]) => {
                const bpElement = document.querySelector(`[data-activity-id="${activityId}"] .bp-value`);
                if (bpElement) {
                    bpElement.textContent = `${bpValue} BP`;
                }
            });
        }
        
        // Update earned/remaining totals
        if (data.total_earned !== undefined) {
            document.getElementById('earned-display').textContent = data.total_earned;
        }
        if (data.total_remaining !== undefined) {
            document.getElementById('remaining-display').textContent = data.total_remaining;
        }
    } catch (error) {
        console.error('Error updating BP values:', error);
    }
}

// Refresh statistics (earned/remaining counters)
async function refreshStats() {
    try {
        const response = await fetch('/api/user_stats');
        const data = await response.json();
        
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
        
        // Update progress if needed
        if (data.completed_count !== undefined && data.total_activities !== undefined) {
            const progressFill = document.querySelector('.progress-fill');
            const progressPercentage = Math.round((data.completed_count / data.total_activities) * 100);
            if (progressFill) {
                progressFill.style.width = `${progressPercentage}%`;
            }
            
            const statValue = document.querySelector('.stat-card:nth-child(2) .stat-value');
            if (statValue) {
                statValue.textContent = `${data.completed_count} / ${data.total_activities}`;
            }
        }
        
    } catch (error) {
        console.error('Error refreshing stats:', error);
    }
}

// Switch between tabs
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabName) {
            btn.classList.add('active');
        }
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

// Move activity card to appropriate tab
function moveActivityToTab(activityId, category, completed) {
    // Get the card from current location
    const card = document.querySelector(`[data-activity-id="${activityId}"]`);
    if (!card) return;
    
    // Store activity details
    const activityName = card.querySelector('label').textContent.trim();
    const bpValue = card.querySelector('.bp-value').textContent;
    
    // Determine source and target tabs
    const sourceTab = completed ? 'active-tab' : 'completed-tab';
    const targetTab = completed ? 'completed-tab' : 'active-tab';
    
    // Remove card from source tab
    card.remove();
    
    // Create new card for target tab
    const newCard = createActivityCard(activityId, activityName, bpValue, category, completed);
    
    // Find or create category in target tab
    let targetCategory = document.querySelector(`#${targetTab} [data-category="${category}"]`);
    
    if (!targetCategory) {
        // Create new category section
        targetCategory = document.createElement('div');
        targetCategory.className = 'activity-category';
        targetCategory.setAttribute('data-category', category);
        
        const categoryTitle = document.createElement('h2');
        categoryTitle.className = 'category-title';
        categoryTitle.textContent = category;
        
        const activityGrid = document.createElement('div');
        activityGrid.className = 'activity-grid';
        
        targetCategory.appendChild(categoryTitle);
        targetCategory.appendChild(activityGrid);
        
        // Insert before empty state if exists
        const emptyState = document.querySelector(`#${targetTab} .empty-state`);
        if (emptyState) {
            emptyState.parentNode.insertBefore(targetCategory, emptyState);
        } else {
            document.getElementById(targetTab).appendChild(targetCategory);
        }
    }
    
    // Add card to target category
    const grid = targetCategory.querySelector('.activity-grid');
    grid.appendChild(newCard);
    
    // Check if source category is now empty and remove it
    const sourceCategory = document.querySelector(`#${sourceTab} [data-category="${category}"]`);
    if (sourceCategory) {
        const sourceGrid = sourceCategory.querySelector('.activity-grid');
        if (sourceGrid && sourceGrid.children.length === 0) {
            sourceCategory.remove();
        }
    }
    
    // Update empty states
    updateEmptyStates();
}

// Create activity card element
function createActivityCard(activityId, name, bpValue, category, completed) {
    const card = document.createElement('div');
    card.className = `activity-card ${completed ? 'completed' : ''}`;
    card.setAttribute('data-activity-id', activityId);
    card.setAttribute('data-category', category);
    
    const checkboxId = completed ? `activity-completed-${activityId}` : `activity-${activityId}`;
    
    card.innerHTML = `
        <div class="activity-header">
            <input type="checkbox" 
                   id="${checkboxId}" 
                   ${completed ? 'checked' : ''}
                   onchange="toggleActivity('${activityId}', this.checked)">
            <label for="${checkboxId}">
                ${name}
            </label>
        </div>
        <div class="activity-bp">
            <span class="bp-value">${bpValue}</span>
        </div>
    `;
    
    return card;
}

// Update tab counts
function updateTabCounts(completedDelta) {
    const activeCount = document.getElementById('active-count');
    const completedCount = document.getElementById('completed-count');
    
    if (activeCount && completedCount) {
        const currentActive = parseInt(activeCount.textContent);
        const currentCompleted = parseInt(completedCount.textContent);
        
        activeCount.textContent = currentActive - completedDelta;
        completedCount.textContent = currentCompleted + completedDelta;
    }
}

// Update empty states in both tabs
function updateEmptyStates() {
    ['active-tab', 'completed-tab'].forEach(tabId => {
        const tab = document.getElementById(tabId);
        const categories = tab.querySelectorAll('.activity-category');
        let emptyState = tab.querySelector('.empty-state');
        
        if (categories.length === 0) {
            if (!emptyState) {
                emptyState = document.createElement('div');
                emptyState.className = 'empty-state';
                
                if (tabId === 'active-tab') {
                    emptyState.innerHTML = `
                        <div class="empty-icon">🎉</div>
                        <h3>All Activities Completed!</h3>
                        <p>Great job! Check the Completed tab to review or uncheck activities.</p>
                    `;
                } else {
                    emptyState.innerHTML = `
                        <div class="empty-icon">📝</div>
                        <h3>No Completed Activities Yet</h3>
                        <p>Start checking off activities to see them here!</p>
                    `;
                }
                
                tab.appendChild(emptyState);
            }
        } else if (emptyState) {
            emptyState.remove();
        }
    });
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