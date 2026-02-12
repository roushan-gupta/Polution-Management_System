// ====================================================================
// PUBLIC AQI DASHBOARD - MAIN JAVASCRIPT
// ====================================================================

const API_BASE = "http://127.0.0.1:5000";
const NOMINATIM_BASE = "https://nominatim.openstreetmap.org";
let map;
let userLat, userLng;
let geocodingCache = {}; // Cache geocoding results

// ====================================================================
// INITIALIZATION
// ====================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log('📍 AirWatch Dashboard loaded - Requesting location...');
    
    // Request user location
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            onLocationSuccess,
            onLocationError,
            { enableHighAccuracy: true, timeout: 30000, maximumAge: 0 }  // 30 second timeout
        );
    } else {
        console.error('❌ Geolocation not supported');
        onLocationError({ code: 0, message: 'Geolocation not supported' });
    }

    // Setup search functionality
    setupSearch();
});

// ====================================================================
// LOCATION HANDLING
// ====================================================================

function onLocationSuccess(position) {
    userLat = position.coords.latitude;
    userLng = position.coords.longitude;
    
    console.log(`✅ Location detected! Lat: ${userLat}, Lng: ${userLng}`);
    
    // Load current location AQI
    loadCurrentLocationAQI(userLat, userLng);
    
    // Initialize map
    initializeMap(userLat, userLng);
}

function onLocationError(error) {
    console.error('❌ Geolocation error:', error.code, error.message);
    
    // Show prompt for user to allow location or search manually
    document.getElementById('loadingText').innerHTML = `
        <div style="padding: 20px; background: #fff9e6; border-radius: 8px; margin: 20px auto; max-width: 500px; text-align: center;">
            <i class="fas fa-map-marker-alt me-2" style="color: #ff9800; font-size: 24px;"></i>
            <h5 style="margin-top: 10px;">Location Access Needed</h5>
            <p style="margin: 10px 0; color: #666;">Please allow location access to see AQI for your area.</p>
            <p style="margin: 10px 0; color: #999; font-size: 12px;">Error: ${error.message}</p>
            <p style="margin: 10px 0; color: #666;"><strong>OR</strong> use the search box above to find your city/location</p>
            <button onclick="location.reload()" class="btn btn-sm btn-primary me-2">
                <i class="fas fa-redo"></i> Retry Location Access
            </button>
            <button onclick="document.querySelector('.search-container input').focus()" class="btn btn-sm btn-outline-primary">
                <i class="fas fa-search"></i> Search Location
            </button>
        </div>
    `;
    
    // Don't load any data until user allows location or searches
    return;
}

// ====================================================================
// LOAD CURRENT LOCATION AQI
// ====================================================================

async function loadCurrentLocationAQI(lat, lng) {
    try {
        const apiUrl = `${API_BASE}/aqi/current?lat=${lat}&lng=${lng}`;
        console.log(`🌐 Fetching AQI from: ${apiUrl}`);
        
        const response = await fetch(apiUrl);
        const data = await response.json();
        
        console.log('📊 API Response:', data);
        
        // Hide loading, show AQI display
        document.getElementById('loadingSpinner').classList.add('d-none');
        document.getElementById('loadingText').classList.add('d-none');
        document.getElementById('aqiDisplay').classList.remove('d-none');
        
        // Update AQI display
        updateAQIDisplay(data);
        
    } catch (error) {
        console.error('Error loading current AQI:', error);
        showErrorMessage('Unable to fetch air quality data');
    }
}

function updateAQIDisplay(data) {
    const aqiValue = document.getElementById('aqiValue');
    const aqiCategory = document.getElementById('aqiCategory');
    const aqiHealthMessage = document.getElementById('aqiHealthMessage');
    const pm25Value = document.getElementById('pm25Value');
    const pm10Value = document.getElementById('pm10Value');
    const sourceText = document.getElementById('sourceText');
    
    if (data.aqi) {
        // Show test data warning if using database fallback
        if (data.source && data.source.includes('Nearest Station')) {
            const warningDiv = document.createElement('div');
            warningDiv.className = 'alert alert-warning alert-modern mt-3';
            warningDiv.innerHTML = '<i class="fas fa-exclamation-triangle me-2"></i><strong>Note:</strong> This is sample test data. For real-time AQI, monitoring stations need to be configured with live data sources.';
            const card = document.getElementById('currentAqiCard');
            if (!card.querySelector('.alert-warning')) {
                card.appendChild(warningDiv);
            }
        }
        
        // Update AQI value with animation
        animateValue(aqiValue, 0, data.aqi, 1000);
        
        // Update category badge
        const categoryClass = getCategoryClass(data.category);
        aqiCategory.textContent = data.category;
        aqiCategory.className = `aqi-badge ${categoryClass}`;
        
        // Update health message
        aqiHealthMessage.textContent = data.health_message;
        
        // Update PM values
        pm25Value.textContent = data.pm25 ? Math.round(data.pm25) : '--';
        pm10Value.textContent = data.pm10 ? Math.round(data.pm10) : '--';
        
        // Update source
        sourceText.textContent = data.source || 'Unknown source';
        
        // Change AQI value color based on category
        aqiValue.style.color = getCategoryColor(data.aqi);
        
    } else {
        aqiValue.textContent = 'N/A';
        aqiCategory.textContent = data.category;
        aqiCategory.className = 'aqi-badge bg-secondary';
        aqiHealthMessage.textContent = data.health_message;
        sourceText.textContent = data.source || 'Data unavailable';
    }

    updateSourceComparison(data);
}

function updateSourceComparison(data) {
    console.log('WAQI Data:', data.waqi);
    console.log('OpenAQ Data:', data.openaq);
    updateSourceCard('waqi', data.waqi, 'WAQI');
    updateSourceCard('openaq', data.openaq, 'OpenAQ');
}

function updateSourceCard(prefix, sourceData, sourceLabel) {
    const aqiEl = document.getElementById(`${prefix}Aqi`);
    const categoryEl = document.getElementById(`${prefix}Category`);
    const stationEl = document.getElementById(`${prefix}Station`);
    const pm25El = document.getElementById(`${prefix}Pm25`);
    const pm10El = document.getElementById(`${prefix}Pm10`);

    if (!aqiEl || !categoryEl || !stationEl || !pm25El || !pm10El) {
        return;
    }

    if (sourceData && sourceData.aqi !== undefined && sourceData.aqi !== null) {
        aqiEl.textContent = sourceData.aqi;
        let stationText = `Station: ${sourceData.station_name || sourceLabel}`;
        if (sourceData.station_distance_km !== undefined && sourceData.station_distance_km !== null) {
            stationText += ` | ${sourceData.station_distance_km} km`;
        }
        if (sourceData.is_stale && sourceData.age_hours !== undefined && sourceData.age_hours !== null) {
            stationText += ` | stale (${sourceData.age_hours}h)`;
        }
        stationEl.textContent = stationText;
        pm25El.textContent = sourceData.pm25 ? Math.round(sourceData.pm25) : '--';
        pm10El.textContent = sourceData.pm10 ? Math.round(sourceData.pm10) : '--';

        const categoryClass = getCategoryClass(sourceData.category);
        categoryEl.textContent = sourceData.category || 'Unknown';
        categoryEl.className = `aqi-badge ${categoryClass}`;
    } else {
        aqiEl.textContent = '--';
        if (prefix === 'openaq') {
            stationEl.innerHTML = `<small>⚠️ Requires API key (<a href="https://explore.openaq.org/register" target="_blank">Get free key</a>)</small>`;
        } else if (prefix === 'waqi') {
            stationEl.innerHTML = `<small>🔍 No nearby monitoring station</small>`;
        } else {
            stationEl.textContent = `Station: No data`;
        }
        pm25El.textContent = '--';
        pm10El.textContent = '--';
        categoryEl.textContent = 'Unavailable';
        categoryEl.className = 'aqi-badge bg-secondary';
    }
}

// Animate number counting
function animateValue(element, start, end, duration) {
    let startTimestamp = null;
    const step = (timestamp) => {
        if (!startTimestamp) startTimestamp = timestamp;
        const progress = Math.min((timestamp - startTimestamp) / duration, 1);
        element.textContent = Math.floor(progress * (end - start) + start);
        if (progress < 1) {
            window.requestAnimationFrame(step);
        }
    };
    window.requestAnimationFrame(step);
}

// ====================================================================
// MAP FUNCTIONS
// ====================================================================

function initializeMap(lat, lng) {
    // Initialize Leaflet map
    map = L.map('aqiMap').setView([lat, lng], 6);
    
    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors',
        maxZoom: 18
    }).addTo(map);
    
    // Add user location marker
    L.marker([lat, lng], {
        icon: L.divIcon({
            className: 'custom-user-marker',
            html: '<div style="background: #667eea; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
            iconSize: [30, 30]
        })
    }).addTo(map)
        .bindPopup('<strong>Your Location</strong>')
        .openPopup();
}

// ====================================================================
// SEARCH FUNCTIONALITY
// ====================================================================

function setupSearch() {
    const searchInput = document.getElementById('citySearch');
    const suggestionsDiv = document.getElementById('searchSuggestions');
    let searchTimeout;
    
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.trim();
        
        if (query.length < 3) {
            suggestionsDiv.classList.add('d-none');
            return;
        }
        
        // Debounce search requests
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            searchCitiesFromGeocoding(query);
        }, 500);
    });
    
    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !suggestionsDiv.contains(e.target)) {
            suggestionsDiv.classList.add('d-none');
        }
    });
    
    // Handle Enter key
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchCity();
        }
    });
}

// Geocoding search function
async function searchCitiesFromGeocoding(query) {
    const suggestionsDiv = document.getElementById('searchSuggestions');
    
    try {
        suggestionsDiv.innerHTML = '<div class="suggestion-item text-muted"><i class="fas fa-spinner fa-spin me-2"></i>Searching...</div>';
        suggestionsDiv.classList.remove('d-none');
        
        const response = await fetch(
            `${NOMINATIM_BASE}/search?q=${encodeURIComponent(query)},India&format=json&limit=8&addressdetails=1`,
            {
                headers: {
                    'User-Agent': 'PollutionManagementSystem/1.0'
                }
            }
        );
        
        const places = await response.json();
        
        if (places && places.length > 0) {
            suggestionsDiv.innerHTML = places.map(place => {
                const displayName = place.display_name.split(',').slice(0, 3).join(', ');
                return `
                    <div class="suggestion-item" onclick='selectCityFromGeocode(${place.lat}, ${place.lon}, "${displayName.replace(/"/g, '&quot;')}")'>
                        <i class="fas fa-map-marker-alt me-2 text-primary"></i>
                        ${displayName}
                    </div>
                `;
            }).join('');
        } else {
            suggestionsDiv.innerHTML = '<div class="suggestion-item text-muted">No results found</div>';
        }
    } catch (error) {
        console.error('Geocoding error:', error);
        suggestionsDiv.innerHTML = '<div class="suggestion-item text-danger"><i class="fas fa-exclamation-triangle me-2"></i>Search error</div>';
    }
}

function searchCity() {
    const query = document.getElementById('citySearch').value.trim();
    if (query) {
        searchCitiesFromGeocoding(query);
    }
}

function selectCityFromGeocode(lat, lon, name) {
    // Close suggestions
    document.getElementById('searchSuggestions').classList.add('d-none');
    document.getElementById('citySearch').value = name;
    
    // Load AQI for this location
    loadAQIForLocation(lat, lon, name);
    
    // Focus on map
    if (map) {
        map.setView([lat, lon], 12);
        
        // Add temporary marker
        const searchMarker = L.marker([lat, lon], {
            icon: L.divIcon({
                className: 'search-location-marker',
                html: '<div style="background: #667eea; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); animation: pulse 1s infinite;"></div>',
                iconSize: [30, 30]
            })
        }).addTo(map);
        
        searchMarker.bindPopup(`<strong>${name}</strong><br>Searching for AQI data...`).openPopup();
        
        // Scroll to map
        document.getElementById('aqiMap').scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

async function loadAQIForLocation(lat, lon, locationName) {
    try {
        const response = await fetch(`${API_BASE}/aqi/current?lat=${lat}&lng=${lon}`);
        const data = await response.json();
        
        // Show result in a modal or alert
        const resultDiv = document.createElement('div');
        resultDiv.className = 'alert alert-info alert-modern mt-3';
        resultDiv.style.position = 'fixed';
        resultDiv.style.top = '100px';
        resultDiv.style.right = '20px';
        resultDiv.style.zIndex = '10000';
        resultDiv.style.maxWidth = '400px';
        resultDiv.style.boxShadow = '0 10px 40px rgba(0,0,0,0.3)';
        
        if (data.aqi) {
            const categoryColor = getCategoryColor(data.aqi);
            const categoryClass = getCategoryClass(data.category);
            const waqi = data.waqi;
            const openaq = data.openaq;

            const waqiLine = waqi
                ? `<div><strong>WAQI</strong>: ${waqi.aqi} (${waqi.category || 'Unknown'}) - ${waqi.station_name || 'Station'}</div>`
                : `<div><strong>WAQI</strong>: No data</div>`;

            const openaqLine = openaq
                ? `<div><strong>OpenAQ</strong>: ${openaq.aqi} (${openaq.category || 'Unknown'}) - ${openaq.station_name || 'Station'}</div>`
                : `<div><strong>OpenAQ</strong>: No data</div>`;
            
            resultDiv.innerHTML = `
                <button type="button" class="btn-close float-end" onclick="this.parentElement.remove()"></button>
                <h5><i class="fas fa-map-marker-alt me-2"></i>${locationName}</h5>
                <div class="text-center my-3">
                    <div style="font-size: 48px; font-weight: 800; color: ${categoryColor};">${data.aqi}</div>
                    <span class="aqi-badge ${categoryClass}">${data.category}</span>
                </div>
                <p class="mb-2"><small>${data.health_message}</small></p>
                ${data.pm25 ? `<p class="mb-1"><small><strong>PM2.5:</strong> ${Math.round(data.pm25)} μg/m³ | <strong>PM10:</strong> ${Math.round(data.pm10)} μg/m³</small></p>` : ''}
                <div class="mt-2" style="font-size: 12px;">
                    ${waqiLine}
                    ${openaqLine}
                </div>
                <p class="mb-0"><small class="text-muted"><i class="fas fa-info-circle me-1"></i>${data.source}</small></p>
            `;
        } else {
            resultDiv.className = 'alert alert-warning alert-modern mt-3';
            resultDiv.style.position = 'fixed';
            resultDiv.style.top = '100px';
            resultDiv.style.right = '20px';
            resultDiv.style.zIndex = '10000';
            resultDiv.style.maxWidth = '400px';
            resultDiv.innerHTML = `
                <button type="button" class="btn-close float-end" onclick="this.parentElement.remove()"></button>
                <h5><i class="fas fa-exclamation-triangle me-2"></i>No AQI Data</h5>
                <p class="mb-0">${data.health_message || 'No monitoring station found near this location.'}</p>
            `;
        }
        
        document.body.appendChild(resultDiv);
        setTimeout(() => resultDiv.remove(), 8000);
        
    } catch (error) {
        console.error('Error loading AQI:', error);
    }
}

// ====================================================================
// HELPER FUNCTIONS
// ====================================================================

function getCategoryClass(category) {
    const categoryMap = {
        'Good': 'aqi-good',
        'Satisfactory': 'aqi-satisfactory',
        'Moderate': 'aqi-moderate',
        'Poor': 'aqi-poor',
        'Very Poor': 'aqi-very-poor',
        'Severe': 'aqi-severe'
    };
    return categoryMap[category] || 'bg-secondary';
}

function getCategoryColor(aqi) {
    if (aqi <= 50) return '#00e400';
    if (aqi <= 100) return '#7fc800';
    if (aqi <= 200) return '#ffff00';
    if (aqi <= 300) return '#ff7e00';
    if (aqi <= 400) return '#ff0000';
    return '#8f3f97';
}

function getMarkerColor(aqi) {
    return getCategoryColor(aqi);
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} min ago`;
    if (diffMins < 1440) return `${Math.floor(diffMins / 60)} hours ago`;
    return date.toLocaleDateString();
}

function showErrorMessage(message) {
    document.getElementById('loadingSpinner').classList.add('d-none');
    document.getElementById('loadingText').innerHTML = `
        <i class="fas fa-exclamation-triangle me-2"></i>
        ${message}
    `;
}

// ====================================================================
// CONSOLE STYLING (Development Helper)
// ====================================================================

console.log('%c🌍 Public AQI Dashboard Loaded ', 'background: #667eea; color: white; padding: 8px 16px; border-radius: 4px; font-size: 14px; font-weight: bold;');
console.log('%cAPI Base: ' + API_BASE, 'color: #667eea; font-weight: bold;');
