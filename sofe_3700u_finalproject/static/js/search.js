// ===========================
// Search Page Functionality
// ===========================

let searchResults = [];
let searchInitialized = false;

document.addEventListener('DOMContentLoaded', function() {
    if(searchInitialized) return;
    searchInitialized = true;
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
    let searchTable = document.getElementById('searchTable').value;
    if(!searchTable){
        // Default to artworks if user hasn't selected
        searchTable = 'artworks';
    }
    const searchField = document.getElementById('searchField').value;
    const searchQuery = document.getElementById('searchQuery').value.trim();
    const matchType = document.querySelector('input[name="matchType"]:checked').value;
    // Allow empty query to list records (acts as browsing with optional filters)
    try {
        dbApp.showLoading();
        const data = await dbApp.searchRecords(searchTable, {
            field: searchField,
            query: searchQuery,
            matchType: matchType
        });
        console.log('Search response data:', data);
        const debugEl = document.getElementById('searchDebug');
        if(debugEl){
            debugEl.textContent = JSON.stringify(data, null, 2);
        }
        if(!data){
            dbApp.showAlert('Search failed (no data returned)', 'danger');
            updateResultCount(0);
            displaySearchResults([], searchTable);
            return;
        }
        
        displaySearchResults(data.records || [], searchTable);
        updateResultCount((data.records || []).length);
        
        // Defer hideLoading to ensure DOM updates complete
        setTimeout(() => {
            dbApp.hideLoading();
            const tbody = document.getElementById('searchResultsBody');
            console.log('Final tbody child count:', tbody ? tbody.children.length : 'TBODY NOT FOUND');
        }, 100);
        
        if (data.records && data.records.length > 0) {
            dbApp.showAlert(`Found ${data.records.length} matching record(s)`, 'success');
        } else {
            dbApp.showAlert('No matching records found (try different field or query)', 'info');
        }
        
    } catch (error) {
        console.error('Search error:', error);
        dbApp.showAlert('Search failed. Please try again.', 'danger');
        dbApp.hideLoading();
    }
}

/**
 * Display search results
 */
function displaySearchResults(results, category) {
    const resultsBody = document.getElementById('searchResultsBody');
    resultsBody.innerHTML = '';
    console.log('Display invoked. Category:', category, 'Result sample:', results && results[0]);
    
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
    
    // Show available keys for first record for debugging
    const firstKeys = Object.keys(results[0] || {}).join(', ');
    const debugEl = document.getElementById('searchDebug');
    if (debugEl) {
        debugEl.textContent += `\nKeys: ${firstKeys}`;
    }
    
    results.forEach((result, idx) => {
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
        
        if (id === undefined) {
            console.warn('Record missing ID field. Raw record:', result);
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${id ?? '(no id)'}</td>
            <td>${field1 ?? '-'}</td>
            <td>${field2 ?? '-'}</td>
            <td>${field3 ?? '-'}</td>
            <td>
                <button class="btn btn-sm btn-info" onclick="viewDetails(${id})" title="View Details">
                    <i class="fas fa-eye"></i>
                </button>
                <button class="btn btn-sm btn-primary" onclick="editFromSearch(${id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
            </td>
        `;
        console.log(`Appending row ${idx}: ID=${id}, Title=${field1}`);
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
    const rec = searchResults.find(r => r.ObjectID === id || r.ArtistID === id);
    if (!rec) { dbApp.showAlert('Record not found in result set', 'warning'); return; }
    const title = rec.Title || rec.ArtistName || '(untitled)';
    const extra = rec.Medium || rec.Nationality || '';
    const year = rec.YearCreated || rec.BirthYear || '';
    dbApp.showAlert(`<strong>${title}</strong><br>${extra} ${year}`, 'info');
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
