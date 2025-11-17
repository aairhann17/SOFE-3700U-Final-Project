// ===========================
// View Records Page Functionality
// ===========================

let currentTable = '';
let currentData = [];

document.addEventListener('DOMContentLoaded', function() {
    // Table selection change
    document.getElementById('tableSelect').addEventListener('change', function() {
        currentTable = this.value;
        if (currentTable) {
            loadTableData(currentTable);
        } else {
            clearTableData();
        }
    });

    // Records per page change
    document.getElementById('recordsPerPage').addEventListener('change', function() {
        recordsPerPage = parseInt(this.value);
        if (currentTable) {
            loadTableData(currentTable);
        }
    });
});

/**
 * Load data for selected table
 */
async function loadTableData(tableName) {
    try {
        dbApp.showLoading();
        
        // Get actual data from database
        const response = await fetch(`${API_BASE_URL}/${tableName}?page=${currentPage}&limit=${recordsPerPage}`);
        const data = await response.json();
        
        displayTableData(data, tableName);
        updatePagination(data.totalPages);
        
        dbApp.showAlert(`Loaded ${data.records.length} records from ${tableName}`, 'success');
    } catch (error) {
        console.error('Error loading table data:', error);
        dbApp.showAlert('Failed to load table data', 'danger');
    } finally {
        dbApp.hideLoading();
    }
}

/**
 * Display table data in the UI
 */
function displayTableData(data, tableName) {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = '';
    
    if (!data.records || data.records.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted">
                    <i class="fas fa-inbox"></i> No records found
                </td>
            </tr>
        `;
        return;
    }
    
    // Map different table structures
    data.records.forEach(record => {
        let id, field1, field2, field3;
        
        if (tableName === 'artworks') {
            id = record.ObjectID;
            field1 = record.Title;
            field2 = record.Medium || '-';
            field3 = record.YearCreated || '-';
        } else if (tableName === 'artists') {
            id = record.ArtistID;
            field1 = record.ArtistName;
            field2 = record.Nationality || '-';
            field3 = `${record.BirthYear || '?'}-${record.DeathYear || 'Present'}`;
        } else {
            id = record.id || record.ObjectID || record.ArtistID;
            field1 = record.Title || record.ArtistName || record.name || '-';
            field2 = record.Medium || record.Nationality || '-';
            field3 = record.YearCreated || record.BirthYear || '-';
        }
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${id}</td>
            <td>${field1}</td>
            <td>${field2}</td>
            <td>${field3}</td>
            <td>
                <button class="btn btn-sm btn-primary" onclick="editRecord(${id})" title="Edit">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-sm btn-danger" onclick="openDeleteModal(${id})" title="Delete">
                    <i class="fas fa-trash"></i>
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
    
    currentData = data.records;
}

/**
 * Clear table data
 */
function clearTableData() {
    const tableBody = document.getElementById('tableBody');
    tableBody.innerHTML = `
        <tr>
            <td colspan="5" class="text-center text-muted">
                <i class="fas fa-info-circle"></i> Select a table to view records
            </td>
        </tr>
    `;
}

/**
 * Update pagination controls
 */
function updatePagination(totalPages) {
    const pagination = document.getElementById('pagination');
    pagination.innerHTML = '';
    
    // Previous button
    const prevLi = document.createElement('li');
    prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage - 1})">Previous</a>`;
    pagination.appendChild(prevLi);
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        const li = document.createElement('li');
        li.className = `page-item ${i === currentPage ? 'active' : ''}`;
        li.innerHTML = `<a class="page-link" href="#" onclick="changePage(${i})">${i}</a>`;
        pagination.appendChild(li);
    }
    
    // Next button
    const nextLi = document.createElement('li');
    nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextLi.innerHTML = `<a class="page-link" href="#" onclick="changePage(${currentPage + 1})">Next</a>`;
    pagination.appendChild(nextLi);
}

/**
 * Change page
 */
function changePage(page) {
    if (page < 1 || !currentTable) return;
    currentPage = page;
    loadTableData(currentTable);
}

/**
 * Open edit modal
 */
function editRecord(id) {
    const record = currentData.find(r => r.id === id);
    if (!record) return;
    
    document.getElementById('editRecordId').value = id;
    document.getElementById('editField1').value = record.field1 || '';
    document.getElementById('editField2').value = record.field2 || '';
    document.getElementById('editField3').value = record.field3 || '';
    
    const modal = new bootstrap.Modal(document.getElementById('editModal'));
    modal.show();
}

/**
 * Save edited record
 */
async function saveEdit() {
    const id = document.getElementById('editRecordId').value;
    const data = {
        field1: document.getElementById('editField1').value,
        field2: document.getElementById('editField2').value,
        field3: document.getElementById('editField3').value
    };
    
    try {
        dbApp.showLoading();
        await dbApp.updateRecord(currentTable, id, data);
        
        dbApp.showAlert('Record updated successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('editModal')).hide();
        loadTableData(currentTable);
    } catch (error) {
        console.error('Error updating record:', error);
        dbApp.showAlert('Failed to update record', 'danger');
    } finally {
        dbApp.hideLoading();
    }
}

/**
 * Open delete confirmation modal
 */
function openDeleteModal(id) {
    document.getElementById('deleteRecordId').value = id;
    const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
    modal.show();
}

/**
 * Confirm delete
 */
async function confirmDelete() {
    const id = document.getElementById('deleteRecordId').value;
    
    try {
        dbApp.showLoading();
        await dbApp.deleteRecord(currentTable, id);
        
        dbApp.showAlert('Record deleted successfully!', 'success');
        bootstrap.Modal.getInstance(document.getElementById('deleteModal')).hide();
        loadTableData(currentTable);
    } catch (error) {
        console.error('Error deleting record:', error);
        dbApp.showAlert('Failed to delete record', 'danger');
    } finally {
        dbApp.hideLoading();
    }
}

/**
 * Generate sample data (for demonstration)
 */
function generateSampleData(tableName) {
    const records = [];
    const count = Math.floor(Math.random() * 20) + 5;
    
    for (let i = 1; i <= count; i++) {
        records.push({
            id: i,
            field1: `${tableName} Record ${i}`,
            field2: `Data ${i}`,
            field3: `Value ${i}`
        });
    }
    
    return {
        records: records,
        totalPages: Math.ceil(count / recordsPerPage),
        currentPage: 1
    };
}

// Make functions globally accessible
window.editRecord = editRecord;
window.saveEdit = saveEdit;
window.openDeleteModal = openDeleteModal;
window.confirmDelete = confirmDelete;
window.changePage = changePage;
