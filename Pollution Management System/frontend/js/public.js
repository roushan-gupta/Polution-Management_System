fetch("http://127.0.0.1:5000/aqi/all")
    .then(res => res.json())
    .then(data => {
        const container = document.getElementById("aqiCards");
        container.innerHTML = "";

        data.forEach(a => {
            let bg = "success";

            if (a.aqi > 300) bg = "danger";
            else if (a.aqi > 200) bg = "warning";
            else if (a.aqi > 100) bg = "info";

            const card = document.createElement("div");
            card.className = "col-md-4 mb-3";

            card.innerHTML = `
                <div class="card border-${bg}">
                    <div class="card-body">
                        <h5 class="card-title">${a.location_name || "GPS Area"}</h5>
                        <h2 class="text-${bg}">${a.aqi}</h2>
                        <p>${a.category}</p>
                        <small>${a.health_message}</small>
                    </div>
                </div>
            `;

            container.appendChild(card);
        });
    })
    .catch(err => console.error(err));
