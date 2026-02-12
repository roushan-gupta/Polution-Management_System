const role = localStorage.getItem("role");

if (role !== "ADMIN") {
  window.location.href = "index.html";
}

// Load incidents
function loadIncidents() {
  fetch("http://127.0.0.1:5000/incidents")
    .then((res) => res.json())
    .then((data) => {
      const table = document.getElementById("incidentTable");
      table.innerHTML = "";

      data.forEach((i) => {
        const row = document.createElement("tr");

        let options = "";

        if (i.status === "OPEN") {
          options = `<option value="IN_PROGRESS">IN_PROGRESS</option>`;
        } else if (i.status === "IN_PROGRESS") {
          options = `<option value="RESOLVED">RESOLVED</option>`;
        }

        // Create location display with links
        let locationDisplay = "";
        if (i.place_name) {
          const mapsUrl = `https://www.google.com/maps?q=${i.latitude},${i.longitude}`;
          const osmUrl = `https://www.openstreetmap.org/?mlat=${i.latitude}&mlon=${i.longitude}&zoom=16`;
          locationDisplay = `
            <div>
              <strong>${i.place_name}</strong><br>
              <small class="text-muted">Lat: ${i.latitude?.toFixed(6)} | Lng: ${i.longitude?.toFixed(6)}</small><br>
              <a href="${mapsUrl}" target="_blank" class="btn btn-sm btn-primary me-1">🗺️ Google Maps</a>
              <a href="${osmUrl}" target="_blank" class="btn btn-sm btn-secondary">🌍 OpenStreetMap</a>
            </div>
          `;
        } else if (i.location_name) {
          locationDisplay = `<strong>${i.location_name}</strong>`;
        } else {
          const mapsUrl = `https://www.google.com/maps?q=${i.latitude},${i.longitude}`;
          locationDisplay = `
            <div>
              <small class="text-muted">Lat: ${i.latitude?.toFixed(6)} | Lng: ${i.longitude?.toFixed(6)}</small><br>
              <a href="${mapsUrl}" target="_blank" class="btn btn-sm btn-primary">🗺️ View on Map</a>
            </div>
          `;
        }

        row.innerHTML = `
              <td>${i.incident_id}</td>
              <td><button class="btn btn-link p-0" onclick="openCitizenDetails(${i.user_id})">${i.citizen_name}</button></td>
                    <td>${locationDisplay}</td>
                    <td>${i.incident_type}</td>
                    <td>${i.description || ""}</td>
                    <td>${i.status}</td>
                    <td>
                        ${
                          i.image_path
                            ? `<a href="http://127.0.0.1:5000/${i.image_path}" target="_blank">View</a>`
                            : "No image"
                        }
                    </td>
                    <td>
                        <select onchange="updateStatus(${i.incident_id}, this.value)">
                            <option value="">Change</option>
                            ${options}
                        </select>
                    </td>
                `;

        table.appendChild(row);
      });
    })
    .catch((err) => console.error("Fetch error:", err));
}

function updateStatus(id, status) {
  if (!status) return;

  fetch(`http://127.0.0.1:5000/incident/${id}/status`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status: status }),
  }).then(() => loadIncidents());
}

function logout() {
  localStorage.clear();
  window.location.href = "index.html";
}

loadIncidents();

function openCitizenDetails(userId) {
  fetch(`http://127.0.0.1:5000/users/${userId}`)
    .then((res) => res.json())
    .then((data) => {
      if (data.message) {
        return;
      }

      document.getElementById("modalName").innerText = data.name || "";
      document.getElementById("modalEmail").innerText = data.email || "";
      document.getElementById("modalContact").innerText = data.contact_number || "";
      document.getElementById("modalHouse").innerText = data.address_house || "";
      document.getElementById("modalStreet").innerText = data.address_street || "";
      document.getElementById("modalCity").innerText = data.address_city || "";
      document.getElementById("modalState").innerText = data.address_state || "";
      document.getElementById("modalPincode").innerText = data.address_pincode || "";

      const modal = new bootstrap.Modal(document.getElementById("citizenModal"));
      modal.show();
    })
    .catch((err) => console.error("Failed to load citizen details", err));
}
