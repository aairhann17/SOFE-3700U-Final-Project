const API_BASE_URL = 'http://localhost:5000/api';

// Search Met Museum API
document.getElementById('searchBtn').addEventListener('click', searchMetMuseum);
document.getElementById('searchQuery').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') searchMetMuseum();
});

async function searchMetMuseum() {
    const query = document.getElementById('searchQuery').value.trim();
    
    if (!query) {
        alert('Please enter a search term');
        return;
    }

    showLoading(true);
    hideResults();

    try {
        // Call Flask API which calls external Met Museum API
        const response = await fetch(`${API_BASE_URL}/external/met/search?q=${encodeURIComponent(query)}&hasImages=true`);
        const data = await response.json();

        showLoading(false);

        if (data.success && data.objectIDs && data.objectIDs.length > 0) {
            displayResults(data.objectIDs, data.total);
        } else {
            showNoResults();
        }
    } catch (error) {
        showLoading(false);
        console.error('Error searching Met Museum:', error);
        alert('Error connecting to Met Museum API. Please try again.');
    }
}

async function displayResults(objectIDs, total) {
    const resultsContainer = document.getElementById('resultsContainer');
    const resultsCount = document.getElementById('resultsCount');
    
    resultsContainer.innerHTML = '';
    resultsCount.textContent = `${objectIDs.length} of ${total} results`;
    
    document.getElementById('resultsSection').style.display = 'block';

    // Fetch details for each artwork
    for (const objectID of objectIDs) {
        try {
            const response = await fetch(`${API_BASE_URL}/external/met/object/${objectID}`);
            const result = await response.json();

            if (result.success) {
                const artwork = result.data;
                const card = createArtworkCard(artwork);
                resultsContainer.innerHTML += card;
            }
        } catch (error) {
            console.error(`Error fetching object ${objectID}:`, error);
        }
    }

    // Add event listeners to import buttons
    document.querySelectorAll('.import-artwork-btn').forEach(btn => {
        btn.addEventListener('click', importArtwork);
    });
}

function createArtworkCard(artwork) {
    const imageHtml = artwork.primaryImage 
        ? `<img src="${artwork.primaryImage}" class="artwork-image" alt="${artwork.title}">`
        : `<div class="artwork-image-placeholder"><i class="fas fa-image"></i></div>`;

    const yearDisplay = artwork.yearCreated || 'Date Unknown';
    const locationDisplay = [artwork.city, artwork.country].filter(x => x).join(', ') || 'Location Unknown';

    return `
        <div class="col-md-4">
            <div class="artwork-card">
                ${imageHtml}
                <h5 class="card-title">${artwork.title || 'Untitled'}</h5>
                <p class="card-text">
                    <strong>Artist:</strong> ${artwork.artistName || 'Unknown'}<br>
                    <strong>Type:</strong> ${artwork.objectType || 'N/A'}<br>
                    <strong>Medium:</strong> ${artwork.medium || 'N/A'}<br>
                    <strong>Date:</strong> ${yearDisplay}<br>
                    <strong>Origin:</strong> ${locationDisplay}<br>
                    <strong>Department:</strong> ${artwork.department || 'N/A'}
                </p>
                ${artwork.metURL ? `<a href="${artwork.metURL}" target="_blank" class="btn btn-sm btn-outline-primary mb-2 w-100">
                    <i class="fas fa-external-link-alt"></i> View on Met Website
                </a>` : ''}
                <button class="btn btn-success import-artwork-btn import-btn" data-met-id="${artwork.metObjectID}">
                    <i class="fas fa-download"></i> Import to Database
                </button>
            </div>
        </div>
    `;
}

async function importArtwork(event) {
    const button = event.currentTarget;
    const metObjectID = button.getAttribute('data-met-id');
    
    if (confirm('Import this artwork into your database?')) {
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Importing...';

        try {
            const response = await fetch(`${API_BASE_URL}/external/met/import`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ metObjectID: parseInt(metObjectID) })
            });

            const result = await response.json();

            if (result.success) {
                button.innerHTML = '<i class="fas fa-check"></i> Imported!';
                button.classList.remove('btn-success');
                button.classList.add('btn-secondary');
                
                // Show success message
                showSuccessMessage(`Successfully imported "${result.title}" by ${result.artist}`);
            } else {
                throw new Error(result.error || 'Import failed');
            }
        } catch (error) {
            console.error('Error importing artwork:', error);
            button.disabled = false;
            button.innerHTML = '<i class="fas fa-download"></i> Import to Database';
            
            if (error.message.includes('403')) {
                alert('Admin access required to import artworks. Please contact an administrator.');
            } else if (error.message.includes('Duplicate')) {
                alert('This artwork may already exist in the database.');
            } else {
                alert('Error importing artwork: ' + error.message);
            }
        }
    }
}

function showLoading(show) {
    document.getElementById('loadingSpinner').style.display = show ? 'block' : 'none';
}

function hideResults() {
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('noResults').style.display = 'none';
}

function showNoResults() {
    document.getElementById('noResults').style.display = 'block';
}

function showSuccessMessage(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        <i class="fas fa-check-circle"></i> ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
}

// Load some results on page load
window.addEventListener('load', () => {
    searchMetMuseum();
});
