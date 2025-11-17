// ===========================
// Search Page Functionality
// ===========================

let searchResults = [];

document.addEventListener('DOMContentLoaded', function() {
    // Search form submission
    document.getElementById('searchForm').addEventListener('submit', function(e) {
        e.preventDefault();
        performSearch();
    });

    // Table selection change
    document.getElementById('searchTable').addEventListener('change', function() {
        const selectedTable = this.value;
        updateSearchFields(selectedTable);
    });
});

/**
 * Update search field options based on selected table
 */
function updateSearchFields(tableName) {
    const searchField = document.getElementById('searchField');
    
    if (!tableName) {
        searchField.innerHTML = `
            <option value="">-- All Fields --</option>
            <option value="Title">Title</option>
            <option value="ArtistName">Artist Name</option>
        `;
        return;
    }
    
    if (tableName === 'artworks') {
        searchField.innerHTML = `
            <option value="">-- All Fields --</option>
            <option value="Title">Title</option>
            <option value="Medium">Medium</option>
            <option value="ObjectType">Object Type</option>
            <option value="YearCreated">Year</option>
        `;
    } else if (tableName === 'artists') {
        searchField.innerHTML = `
            <option value="">-- All Fields --</option>
            <option value="ArtistName">Name</option>
            <option value="Nationality">Nationality</option>
            <option value="BirthYear">Birth Year</option>
        `;
    } else {
        searchField.innerHTML = '<option value="">-- All Fields --</option>';
    }
}

/**
 * Perform search
 */
async function performSearch() {
    const searchTable = document.getElementById('searchTable').value;
    const searchField = document.getElementById('searchField').value;
    const searchQuery = document.getElementById('searchQuery').value.trim();
    const matchType = document.querySelector('input[name="matchType"]:checked').value;
    
    if (!searchQuery) {
        dbApp.showAlert('Please enter a search query', 'warning');
        return;
    }
    
    try {
        dbApp.showLoading();
        
        const params = new URLSearchParams({
            category: searchTable,
            field: searchField,
            query: searchQuery,
            matchType: matchType
        });
        
        const response = await fetch(`http://localhost:5000/api/search?${params}`);
        const data = await response.json();
        
        displaySearchResults(data.records || [], searchTable);
        updateResultCount((data.records || []).length);
        
        if (data.records && data.records.length > 0) {
            dbApp.showAlert(`Found ${data.records.length} matching record(s)`, 'success');
        } else {
            dbApp.showAlert('No matching records found', 'info');
        }
        
    } catch (error) {
        console.error('Search error:', error);
        dbApp.showAlert('Search failed. Please try again.', 'danger');
    } finally {
        dbApp.hideLoading();
    }
}

/**
 * Display search results
 */
function displaySearchResults(results, category) {
    const resultsBody = document.getElementById('searchResultsBody');
    resultsBody.innerHTML = '';
    
    if (!results || results.length === 0) {
        resultsBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    <i class="fas fa-search"></i> No results found. Try adjusting your search criteria.
                </td>
            </tr>
        `;
        return;
    }
    
    results.forEach(result => {
        let id, field1, field2, field3;
        
        if (category === 'artworks') {
            id = result.ObjectID;
            field1 = result.Title;
            field2 = result.Medium || '-';
            field3 = result.YearCreated || '-';
        } else if (category === 'artists') {
            id = result.ArtistID;
            field1 = result.ArtistName;
            field2 = result.Nationality || '-';
            field3 = `${result.BirthYear || '?'}-${result.DeathYear || 'Present'}`;
        } else {
            id = result.id || result.ObjectID || result.ArtistID;
            field1 = result.Title || result.ArtistName || '-';
            field2 = result.Medium || result.Nationality || '-';
            field3 = result.YearCreated || result.BirthYear || '-';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${id}</td>
            <td>${field1}</td>
            <td>${field2}</td>
            <td>${field3}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewDetails(${id})" title="View Details">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-primary" onclick="editFromSearch(${id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        `;
        resultsBody.appendChild(row);
    });
    
    searchResults = results;
}

/**
 * Update result count badge
 */
function updateResultCount(count) {
    const resultCount = document.getElementById('resultCount');
    resultCount.textContent = `${count} result${count !== 1 ? 's' : ''}`;
}

/**
 * Reset search form
 */
function resetSearch() {
    document.getElementById('searchForm').reset();
    document.getElementById('searchResultsBody').innerHTML = `
        <tr>
            <td colspan="5" class="text-center text-muted">
                <i class="fas fa-search"></i> Enter search criteria and click Search to find records
            </td>
        </tr>
    `;
    updateResultCount(0);
    dbApp.showAlert('Search form has been reset', 'info');
}

/**
 * View record details
 */
function viewDetails(id) {
    const record = searchResults.find(r => r.id === id);
    if (!record) return;
    
    // Create a modal or alert to show details
    const detailsHTML = `
        <div class="alert alert-info">
            <h5>Record Details</h5>
            <p><strong>ID:</strong> ${record.id}</p>
            <p><strong>Field 1:</strong> ${record.field1}</p>
            <p><strong>Field 2:</strong> ${record.field2}</p>
            <p><strong>Field 3:</strong> ${record.field3}</p>
        </div>
    `;
    
    dbApp.showAlert(detailsHTML, 'info');
}

/**
 * Edit record from search results
 */
function editFromSearch(id) {
    // Redirect to view page or open edit modal
    window.location.href = `view_records.html?edit=${id}`;
}

/**
 * Generate sample search results (for demonstration)
 */
function generateSearchResults(query) {
    // Simulate search results
    const results = [];
    const count = Math.floor(Math.random() * 10) + 1;
    
    for (let i = 1; i <= count; i++) {
        results.push({
            id: i,
            field1: `${query} Result ${i}`,
            field2: `Match ${i}`,
            field3: `Data ${i}`
        });
    }
    
    return results;
}

/**
 * Export search results (future feature)
 */
function exportResults(format = 'csv') {
    if (searchResults.length === 0) {
        dbApp.showAlert('No results to export', 'warning');
        return;
    }
    
    dbApp.showAlert(`Exporting ${searchResults.length} results as ${format.toUpperCase()}...`, 'info');
    // Implement export logic here
}

// Make functions globally accessible
window.resetSearch = resetSearch;
window.viewDetails = viewDetails;
window.editFromSearch = editFromSearch;
window.exportResults = exportResults;
