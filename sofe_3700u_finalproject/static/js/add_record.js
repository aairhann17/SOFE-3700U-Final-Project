// ===========================
// Add Record Page Functionality
// ===========================

document.addEventListener('DOMContentLoaded', function() {
    console.log('Add record page loaded');
    const tableSelect = document.getElementById('addTableSelect');
    const formFieldsDiv = document.getElementById('formFields');
    console.log('Table select element:', tableSelect);
    console.log('Form fields div:', formFieldsDiv);
    
    // Table selection change
    if (tableSelect) {
        tableSelect.addEventListener('change', function() {
            const selectedTable = this.value;
            console.log('Selected table:', selectedTable);
            if (selectedTable) {
                generateFormFields(selectedTable);
            } else {
                document.getElementById('formFields').innerHTML = `
                    <div class="alert alert-info">
                        <i class="fas fa-info-circle"></i> Please select a table to display the form fields.
                    </div>
                `;
            }
        });
    } else {
        console.error('addTableSelect element not found!');
    }

    // Form submission
    document.getElementById('addRecordForm').addEventListener('submit', function(e) {
        e.preventDefault();
        handleFormSubmit();
    });
});

/**
 * Generate form fields based on selected table
 */
function generateFormFields(tableName) {
    const formFields = document.getElementById('formFields');
    
    if (tableName === 'artworks') {
        formFields.innerHTML = `
            <div class="mb-3">
                <label for="Title" class="form-label">Title <span class="text-danger">*</span></label>
                <input type="text" class="form-control" name="Title" id="Title">
                <div class="invalid-feedback">Title is required.</div>
            </div>
            <div class="mb-3">
                <label for="ObjectType" class="form-label">Object Type</label>
                <input type="text" class="form-control" name="ObjectType" id="ObjectType" placeholder="e.g., Painting, Sculpture">
            </div>
            <div class="mb-3">
                <label for="Medium" class="form-label">Medium</label>
                <input type="text" class="form-control" name="Medium" id="Medium" placeholder="e.g., Oil on Canvas">
            </div>
            <div class="mb-3">
                <label for="YearCreated" class="form-label">Year Created</label>
                <input type="number" class="form-control" name="YearCreated" id="YearCreated" min="1" max="2025">
            </div>
            <div class="mb-3">
                <label for="OriginID" class="form-label">Origin</label>
                <select class="form-select" name="OriginID" id="OriginID">
                    <option value="">-- Select Origin --</option>
                </select>
            </div>
            <div class="mb-3">
                <label for="GalleryID" class="form-label">Gallery</label>
                <select class="form-select" name="GalleryID" id="GalleryID">
                    <option value="">-- Select Gallery --</option>
                </select>
            </div>
            <div class="alert alert-warning">
                <small><i class="fas fa-exclamation-triangle"></i> Fields marked with <span class="text-danger">*</span> are required.</small>
            </div>
            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                <button type="button" class="btn btn-secondary" onclick="resetForm()">
                    <i class="fas fa-undo"></i> Reset
                </button>
                <button type="submit" class="btn btn-success">
                    <i class="fas fa-save"></i> Save Item
                </button>
            </div>
        `;
        loadDropdownOptions();
    } else if (tableName === 'artists') {
        formFields.innerHTML = `
            <div class="mb-3">
                <label for="ArtistName" class="form-label">Artist Name <span class="text-danger">*</span></label>
                <input type="text" class="form-control" name="ArtistName" id="ArtistName">
                <div class="invalid-feedback">This field is required.</div>
            </div>
            <div class="mb-3">
                <label for="Nationality" class="form-label">Nationality</label>
                <input type="text" class="form-control" name="Nationality" id="Nationality">
            </div>
            <div class="mb-3">
                <label for="BirthYear" class="form-label">Birth Year</label>
                <input type="number" class="form-control" name="BirthYear" id="BirthYear" min="1000" max="2025">
            </div>
            <div class="mb-3">
                <label for="DeathYear" class="form-label">Death Year</label>
                <input type="number" class="form-control" name="DeathYear" id="DeathYear" min="1000" max="2025">
            </div>
            <div class="mb-3">
                <label for="ArtistBio" class="form-label">Biography</label>
                <textarea class="form-control" name="ArtistBio" id="ArtistBio" rows="3"></textarea>
            </div>
            <div class="alert alert-warning">
                <small><i class="fas fa-exclamation-triangle"></i> Fields marked with <span class="text-danger">*</span> are required.</small>
            </div>
            <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                <button type="button" class="btn btn-secondary" onclick="resetForm()">
                    <i class="fas fa-undo"></i> Reset
                </button>
                <button type="submit" class="btn btn-success">
                    <i class="fas fa-save"></i> Save Item
                </button>
            </div>
        `;
    } else {
        formFields.innerHTML = `
            <div class="alert alert-info">
                <i class="fas fa-info-circle"></i> Form for ${tableName} coming soon.
            </div>
        `;
    }
}

/**
 * Load dropdown options for origins and galleries
 */
async function loadDropdownOptions() {
    try {
        // Load origins
        const originsResponse = await fetch(`${API_BASE_URL}/origins`);
        const origins = await originsResponse.json();
        const originSelect = document.getElementById('OriginID');
        if (originSelect) {
            origins.forEach(origin => {
                const option = document.createElement('option');
                option.value = origin.OriginID;
                option.textContent = `${origin.Country} - ${origin.City || ''}`;
                originSelect.appendChild(option);
            });
        }
        
        // Load galleries
        const galleriesResponse = await fetch(`${API_BASE_URL}/galleries`);
        const galleries = await galleriesResponse.json();
        const gallerySelect = document.getElementById('GalleryID');
        if (gallerySelect) {
            galleries.forEach(gallery => {
                const option = document.createElement('option');
                option.value = gallery.GalleryID;
                option.textContent = gallery.GalleryName;
                gallerySelect.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading dropdown options:', error);
    }
}

/**
 * Handle form submission
 */
async function handleFormSubmit() {
    const form = document.getElementById('addRecordForm');
    const selectedTable = document.getElementById('addTableSelect').value;
    
    // Manual validation for required fields only
    const titleField = document.getElementById('Title');
    const artistNameField = document.getElementById('ArtistName');
    
    if (selectedTable === 'artworks' && titleField && !titleField.value.trim()) {
        titleField.classList.add('is-invalid');
        dbApp.showAlert('Title is required', 'warning', 'alertContainer');
        titleField.focus();
        return;
    }
    
    if (selectedTable === 'artists' && artistNameField && !artistNameField.value.trim()) {
        artistNameField.classList.add('is-invalid');
        dbApp.showAlert('Artist Name is required', 'warning', 'alertContainer');
        artistNameField.focus();
        return;
    }
    
    // Get form data
    const formData = new FormData(form);
    const data = {};
    for (const [key, value] of formData.entries()) {
        // Convert empty strings to null for optional fields
        data[key] = value.trim() === '' ? null : value;
    }
    
    console.log('Submitting to:', `${API_BASE_URL}/${selectedTable}`, 'Data:', data);
    try {
        dbApp.showLoading();
        
        const response = await fetch(`${API_BASE_URL}/${selectedTable}`, {
            method: 'POST',
            credentials: 'include',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        
        console.log('Response status:', response.status);
        if (response.ok) {
            const result = await response.json();
            console.log('Success:', result);
            dbApp.showAlert('Record added successfully!', 'success', 'alertContainer');
            form.reset();
            form.classList.remove('was-validated');
        } else {
            let errorMsg = 'Failed to add record';
            try {
                const error = await response.json();
                errorMsg = error.error || errorMsg;
                console.error('Server error:', error);
            } catch(e) {
                const text = await response.text();
                console.error('Response text:', text);
            }
            if (response.status === 401) {
                errorMsg = 'Not authenticated. Please log in as admin.';
            } else if (response.status === 403) {
                errorMsg = 'Admin access required to add records.';
            }
            throw new Error(errorMsg);
        }
        
    } catch (error) {
        console.error('Error adding record:', error);
        dbApp.showAlert(error.message || 'Failed to add record. Please try again.', 'danger', 'alertContainer');
    } finally {
        dbApp.hideLoading();
    }
}

/**
 * Reset form
 */
function resetForm() {
    const form = document.getElementById('addRecordForm');
    form.reset();
    form.classList.remove('was-validated');
    
    // Clear any validation errors
    const invalidInputs = form.querySelectorAll('.is-invalid');
    invalidInputs.forEach(input => input.classList.remove('is-invalid'));
    
    dbApp.showAlert('Form has been reset', 'info', 'alertContainer');
}

/**
 * Validate specific field
 */
function validateField(fieldId) {
    const field = document.getElementById(fieldId);
    if (!field) return true;
    
    if (field.hasAttribute('required') && !field.value.trim()) {
        field.classList.add('is-invalid');
        return false;
    } else {
        field.classList.remove('is-invalid');
        return true;
    }
}

// Add real-time validation
document.addEventListener('DOMContentLoaded', function() {
    // Add blur event listeners for validation
    document.getElementById('addRecordForm').addEventListener('blur', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT' || e.target.tagName === 'TEXTAREA') {
            validateField(e.target.id);
        }
    }, true);
});

// Make functions globally accessible
window.resetForm = resetForm;
window.validateField = validateField;
