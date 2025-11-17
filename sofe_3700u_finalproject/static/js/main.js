// ===========================
// Global Variables and Configuration
// ===========================
const API_BASE_URL = 'http://localhost:5000/api';
let currentPage = 1;
let recordsPerPage = 25;

// ===========================
// Utility Functions
// ===========================

/**
 * Display alert messages
 */
function showAlert(message, type = 'info', containerId = 'alertContainer') {
    const container = document.getElementById(containerId);
    if (!container) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    container.innerHTML = '';
    container.appendChild(alertDiv);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alertDiv.classList.remove('show');
        setTimeout(() => alertDiv.remove(), 300);
    }, 5000);
}

/**
 * Show loading spinner
 */
function showLoading() {
    const loadingHTML = `
        <div class="loading-overlay" id="loadingOverlay">
            <div class="spinner-border text-light" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', loadingHTML);
}

/**
 * Hide loading spinner
 */
function hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.remove();
}

/**
 * Format date to readable string
 */
function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('en-US', options);
}

/**
 * Validate form inputs
 */
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (!form) return false;
    
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

/**
 * Clear form validation
 */
function clearValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const inputs = form.querySelectorAll('.is-invalid');
    inputs.forEach(input => input.classList.remove('is-invalid'));
}

// ===========================
// API Functions (Ready for backend integration)
// ===========================

/**
 * Fetch data from API
 */
async function fetchData(endpoint, options = {}) {
    try {
        showLoading();
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Fetch error:', error);
        showAlert(`Error: ${error.message}`, 'danger');
        return null;
    } finally {
        hideLoading();
    }
}

/**
 * Get all records from a table
 */
async function getRecords(tableName, page = 1, limit = 25) {
    // Placeholder for backend integration
    return fetchData(`/records/${tableName}?page=${page}&limit=${limit}`);
}

/**
 * Get single record by ID
 */
async function getRecord(tableName, id) {
    return fetchData(`/records/${tableName}/${id}`);
}

/**
 * Create new record
 */
async function createRecord(tableName, data) {
    return fetchData(`/records/${tableName}`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * Update existing record
 */
async function updateRecord(tableName, id, data) {
    return fetchData(`/records/${tableName}/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data)
    });
}

/**
 * Delete record
 */
async function deleteRecord(tableName, id) {
    return fetchData(`/records/${tableName}/${id}`, {
        method: 'DELETE'
    });
}

/**
 * Search records
 */
async function searchRecords(tableName, searchParams) {
    const queryString = new URLSearchParams(searchParams).toString();
    return fetchData(`/search/${tableName}?${queryString}`);
}

// ===========================
// Event Listeners
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Add input validation listeners
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                if (this.value.trim()) {
                    this.classList.remove('is-invalid');
                }
            });
        });
    });

    // Load initial stats on homepage
    if (document.getElementById('totalRecords')) {
        loadStats();
    }
});

/**
 * Load statistics for dashboard
 */

/**
 * Load statistics for dashboard - UPDATED FOR REAL DATABASE
 */
async function loadStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/stats`);
        const data = await response.json();
        document.getElementById('totalRecords').textContent = data.artworks || '0';
        document.getElementById('totalTables').textContent = data.artists || '0';
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Refresh data
 */
function refreshData() {
    showAlert('Refreshing data...', 'info');
    // Implement actual refresh logic based on current page
    setTimeout(() => {
        showAlert('Data refreshed successfully!', 'success');
    }, 1000);
}

// ===========================
// Export functions for use in other scripts
// ===========================
window.dbApp = {
    showAlert,
    showLoading,
    hideLoading,
    formatDate,
    validateForm,
    clearValidation,
    getRecords,
    getRecord,
    createRecord,
    updateRecord,
    deleteRecord,
    searchRecords,
    refreshData
};
