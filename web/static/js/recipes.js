// =================================================================
// Recipes Page
// =================================================================
// All recipe data is embedded as JSON in the page — no API calls needed.

/** @type {Object} Parsed recipe data from server */
let recipesData = null;

/** @type {string|null} Currently expanded recipe ID */
let activeRecipeId = null;

/** @type {string|null} Currently active step tab ID */
let activeStepId = null;

// =================================================================
// Data Loading
// =================================================================

/**
 * Parse recipe data from the embedded JSON script tag.
 * @returns {Object} Parsed recipes data
 */
function loadRecipesData() {
    const el = document.getElementById('recipes-json');
    if (!el) return { recipes: [] };
    return JSON.parse(el.textContent);
}

// =================================================================
// Search
// =================================================================

/**
 * Initialize search functionality.
 */
function initializeSearch() {
    const searchInput = document.getElementById('recipe-search');
    const searchClear = document.getElementById('search-clear');

    if (!searchInput) return;

    const debouncedFilter = debounce(() => {
        applySearch();
    }, 200);

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        searchClear.style.display = query.length > 0 ? 'flex' : 'none';
        debouncedFilter();
    });

    searchClear.addEventListener('click', () => {
        searchInput.value = '';
        searchClear.style.display = 'none';
        applySearch();
        searchInput.focus();
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            searchInput.value = '';
            searchClear.style.display = 'none';
            applySearch();
        }
    });
}

/**
 * Apply search filter to recipe cards.
 */
function applySearch() {
    const query = document.getElementById('recipe-search').value.trim().toLowerCase();
    const cards = document.querySelectorAll('.recipe-card');
    const emptyState = document.getElementById('empty-state');
    const grid = document.getElementById('recipe-grid');

    let visibleCount = 0;

    cards.forEach(card => {
        const index = parseInt(card.getAttribute('data-index'));
        const recipe = recipesData.recipes[index];

        let visible = true;
        if (query.length > 0) {
            // Search recipe name
            const nameMatch = recipe.name.toLowerCase().includes(query);

            // Search ingredient names across all steps
            let ingredientMatch = false;
            const allSteps = [...recipe.steps, recipe.final_step];
            for (const step of allSteps) {
                for (const ing of step.ingredients) {
                    if (ing.name.toLowerCase().includes(query)) {
                        ingredientMatch = true;
                        break;
                    }
                }
                if (ingredientMatch) break;
            }

            visible = nameMatch || ingredientMatch;
        }

        if (visible) {
            card.classList.remove('filter-hidden');
            visibleCount++;
        } else {
            card.classList.add('filter-hidden');
            // Collapse detail if the active recipe is filtered out
            if (recipe.id === activeRecipeId) {
                closeDetail();
            }
        }
    });

    document.getElementById('visible-count').textContent = visibleCount;

    if (visibleCount === 0) {
        emptyState.style.display = 'block';
        grid.style.display = 'none';
    } else {
        emptyState.style.display = 'none';
        grid.style.display = 'grid';
    }
}

// =================================================================
// Detail Panel
// =================================================================

/**
 * Toggle detail panel for a recipe card.
 * @param {string} recipeId - Recipe ID
 * @param {number} index - Index in recipesData.recipes
 */
function toggleDetail(recipeId, index) {
    if (activeRecipeId === recipeId) {
        closeDetail();
        return;
    }

    activeRecipeId = recipeId;
    const recipe = recipesData.recipes[index];

    // Highlight active card
    document.querySelectorAll('.recipe-card').forEach(c => c.classList.remove('active'));
    const card = document.querySelector(`[data-recipe-id="${recipeId}"]`);
    if (card) card.classList.add('active');

    // Build and show detail
    const detail = document.getElementById('recipe-detail');
    detail.innerHTML = buildDetailHTML(recipe);
    detail.style.display = 'block';

    // Bind detail event listeners (no inline onclick)
    detail.querySelector('.detail-close').addEventListener('click', closeDetail);
    detail.querySelectorAll('.detail-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            switchStep(tab.getAttribute('data-step-id'));
        });
    });

    // Position detail below the grid
    positionDetail();

    // Initialize first tab
    const isMultiStep = recipe.steps.length > 0;
    if (isMultiStep) {
        switchStep(recipe.steps[0].id);
    } else {
        switchStep(recipe.final_step.id);
    }

    // Scroll detail into view
    detail.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Close the detail panel.
 */
function closeDetail() {
    activeRecipeId = null;
    activeStepId = null;

    document.querySelectorAll('.recipe-card').forEach(c => c.classList.remove('active'));

    const detail = document.getElementById('recipe-detail');
    detail.style.display = 'none';
    detail.innerHTML = '';

    // Move detail back to end of page
    const page = document.querySelector('.recipes-page');
    page.appendChild(detail);
}

/**
 * Position the detail panel after the recipe grid (full width below all cards).
 */
function positionDetail() {
    const detail = document.getElementById('recipe-detail');
    const grid = document.getElementById('recipe-grid');
    grid.after(detail);
}

/**
 * Build the HTML for the detail panel.
 * @param {Object} recipe - Recipe data object
 * @returns {string} HTML string
 */
function buildDetailHTML(recipe) {
    const isMultiStep = recipe.steps.length > 0;
    const allSteps = isMultiStep ? [...recipe.steps, recipe.final_step] : [recipe.final_step];

    let html = `
        <div class="detail-header">
            <h3>${escapeHTML(recipe.name)}</h3>
            <button class="detail-close" aria-label="Закрыть">✕</button>
        </div>
    `;

    // Tabs (only for multi-step)
    if (isMultiStep) {
        html += '<div class="detail-tabs">';
        allSteps.forEach((step, i) => {
            const isLast = i === allSteps.length - 1;
            const label = isLast ? `✨ ${escapeHTML(step.name)}` : `${i + 1}. ${escapeHTML(step.name)}`;
            html += `<button class="detail-tab" data-step-id="${escapeHTML(step.id)}">${label}</button>`;
        });
        html += '</div>';
    }

    // Step contents
    allSteps.forEach(step => {
        html += `<div class="step-content" data-step-content="${step.id}">`;

        // Ingredients
        if (step.ingredients.length > 0) {
            html += `
                <div class="step-section">
                    <div class="step-section-title">Ингредиенты</div>
                    <div class="step-items">
            `;
            step.ingredients.forEach(ing => {
                const cls = ing.is_recipe ? 'step-item-recipe' : 'step-item-ingredient';
                html += `<span class="step-item ${cls}">${escapeHTML(ing.name)}</span>`;
            });
            html += '</div></div>';
        }

        // Tools
        if (step.tools.length > 0) {
            html += `
                <div class="step-section">
                    <div class="step-section-title">Инструменты</div>
                    <div class="step-items">
            `;
            step.tools.forEach(tool => {
                html += `<span class="step-item step-item-tool">${escapeHTML(tool.name)}</span>`;
            });
            html += '</div></div>';
        }

        html += '</div>';
    });

    // Summary panels (shopping list + all tools)
    const hasShoppingList = recipe.shopping_list.length > 0;
    const hasTools = recipe.all_tools.length > 0;

    if (hasShoppingList || hasTools) {
        html += '<div class="detail-summary">';

        if (hasShoppingList) {
            html += `
                <div class="summary-panel">
                    <div class="summary-panel-title">🛒 Список покупок</div>
                    <div class="summary-items">
            `;
            recipe.shopping_list.forEach(item => {
                const cls = item.type === 'fishing' ? 'summary-item-fish' : 'summary-item-shop';
                let countStr = '';
                if (item.count > 1 || item.pack_size > 1) {
                    countStr = ` <span class="summary-item-count">×${item.count}</span>`;
                    if (item.pack_size > 1) {
                        const packs = Math.ceil(item.count / item.pack_size);
                        countStr += ` <span class="summary-item-packs">(${packs} уп. по ${item.pack_size})</span>`;
                    }
                }
                html += `<span class="summary-item ${cls}">${escapeHTML(item.name)}${countStr}</span>`;
            });
            html += '</div></div>';
        }

        if (hasTools) {
            html += `
                <div class="summary-panel">
                    <div class="summary-panel-title">🔧 Все инструменты</div>
                    <div class="summary-items">
            `;
            recipe.all_tools.forEach(tool => {
                html += `<span class="summary-item summary-item-tool">${escapeHTML(tool.name)}</span>`;
            });
            html += '</div></div>';
        }

        html += '</div>';
    }

    return html;
}

/**
 * Switch the active step tab in the detail panel.
 * @param {string} stepId - Step ID to activate
 */
function switchStep(stepId) {
    activeStepId = stepId;

    // Update tab styles
    document.querySelectorAll('.detail-tab').forEach(tab => {
        if (tab.getAttribute('data-step-id') === stepId) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    // Show/hide step content
    document.querySelectorAll('.step-content').forEach(content => {
        if (content.getAttribute('data-step-content') === stepId) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
}

// =================================================================
// Utilities
// =================================================================

/**
 * Escape HTML special characters.
 * @param {string} str - String to escape
 * @returns {string} Escaped string
 */
function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// =================================================================
// Initialization
// =================================================================

document.addEventListener('DOMContentLoaded', () => {
    recipesData = loadRecipesData();

    // Card click handlers
    document.querySelectorAll('.recipe-card').forEach(card => {
        card.addEventListener('click', () => {
            const recipeId = card.getAttribute('data-recipe-id');
            const index = parseInt(card.getAttribute('data-index'));
            toggleDetail(recipeId, index);
        });
    });

    initializeSearch();
});
