let map;

if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
        pos => {
            const lat = pos.coords.latitude;
            const lng = pos.coords.longitude;

            initMap(lat, lng);
            loadMyAQI(lat, lng);
            loadAllAQI();
        },
        () => alert("Location permission required")
    );
}

function initMap(lat, lng) {
    map = L.map("map").setView([lat, lng], 11);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap contributors"
    }).addTo(map);

    L.marker([lat, lng])
        .addTo(map)
        .bindPopup("You are here")
        .openPopup();
}

function loadMyAQI(lat, lng) {
    fetch(`http://127.0.0.1:5000/aqi/current?lat=${lat}&lng=${lng}`)
        .then(res => res.json())
        .then(data => {
            if (!data.aqi) {
                document.getElementById("myAqi").innerHTML = `
                    AQI: <b>${data.category}</b><br>
                    <small>${data.health_message}</small> <br>
                    <small>Source: ${data.source}</small>
                `;
                return;
            }

            // Build PM info if available
            let pmInfo = '';
            if (data.pm25) {
                pmInfo += `PM2.5: ${data.pm25} μg/m³`;
                if (data.pm10) {
                    pmInfo += ` | PM10: ${Math.round(data.pm10)} μg/m³`;
                }
                pmInfo = `<small class="text-muted">${pmInfo}</small><br>`;
            }

            document.getElementById("myAqi").innerHTML = `
                Your Location AQI: 
                <b class="display-6">${data.aqi}</b> 
                <span class="badge bg-${getColorBadge(data.aqi)}">${data.category}</span><br>
                ${pmInfo}
                <small>${data.health_message}</small><br>
                <small class="text-muted">📍 ${data.source}</small>
            `;
        })
        .catch(() => {
            document.getElementById("myAqi").innerHTML =
                "Unable to fetch AQI data.";
        });
}

function getColorBadge(aqi) {
    if (aqi <= 50) return "success";
    if (aqi <= 100) return "info";
    if (aqi <= 200) return "warning";
    if (aqi <= 300) return "danger";
    return "dark";
}


function getColor(aqi) {
    if (aqi <= 100) return "green";
    if (aqi <= 200) return "orange";
    return "red";
}

function loadAllAQI() {
    fetch("http://127.0.0.1:5000/aqi/all")
        .then(res => res.json())
        .then(data => {
            data.forEach(a => {
                if (!a.latitude || !a.longitude) return;

                L.circleMarker([a.latitude, a.longitude], {
                    radius: 8,
                    color: getColor(a.aqi),
                    fillOpacity: 0.7
                })
                .addTo(map)
                .bindPopup(`
                    AQI: ${a.aqi}<br>
                    ${a.category}<br>
                    <small>${a.health_message}</small>
                `);
            });
        });
}
