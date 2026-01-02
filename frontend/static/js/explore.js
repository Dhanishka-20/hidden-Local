// ====================
// MAP INITIALIZATION
// ====================
const map = L.map('map').setView([26.9124, 75.7873], 12);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

function addMarker(lat, lng, popupText) {
    if (lat && lng) {
        L.marker([lat, lng]).addTo(map).bindPopup(popupText);
    }
}

// ====================
// TOP HIDDEN GEMS (ML SELECTED – NO AI SCORE SHOWN)
// ====================
const topGemsContainer = document.getElementById("topGems");

if (topGemsContainer) {
    fetch("http://127.0.0.1:5000/ml/top-gems")
        .then(res => res.json())
        .then(data => {
            data.forEach(v => {

                addMarker(
                    v.latitude,
                    v.longitude,
                    `<b>${v.name}</b><br>${v.category}`
                );

                const div = document.createElement("div");
                div.style.border = "2px solid #22c55e";
                div.style.padding = "12px";
                div.style.marginBottom = "12px";
                div.style.borderRadius = "6px";

                div.innerHTML = `
                    <h4>${v.name} ⭐</h4>
                    <img 
                        src="http://127.0.0.1:5000/uploads/${v.image_path}" 
                        alt="${v.name}"
                        style="width:100%;max-width:250px;border-radius:5px;margin:8px 0;"
                    >
                    <p>${v.category} • ${v.area}</p>
                    <p>⭐ Rating: ${v.rating}</p>

                    <button onclick="likeVendor(${v.id})">
                        ❤️ Like (${v.likes || 0})
                    </button>
                `;

                topGemsContainer.appendChild(div);
            });
        })
        .catch(err => console.error("Error loading top gems:", err));
}

// ====================
// ALL APPROVED VENDORS
// ====================
const vendorList = document.getElementById("vendorList");

if (vendorList) {
    fetch("http://127.0.0.1:5000/vendors")
        .then(res => res.json())
        .then(data => {
            data.forEach(v => {

                addMarker(
                    v.latitude,
                    v.longitude,
                    `<b>${v.name}</b><br>${v.category}`
                );

                const card = document.createElement("div");
                card.style.marginBottom = "18px";
                card.style.padding = "10px";
                card.style.borderBottom = "1px solid #ddd";

                card.innerHTML = `
                    <h4>${v.name}</h4>
                    <img 
                        src="http://127.0.0.1:5000/uploads/${v.image_path}" 
                        alt="${v.name}"
                        style="width:100%;max-width:220px;border-radius:5px;margin:6px 0;"
                    >
                    <p>${v.category} • ${v.area}</p>
                    <p>⭐ ${v.rating}</p>

                    <button onclick="likeVendor(${v.id})">
                        ❤️ Like (${v.likes || 0})
                    </button>
                `;

                vendorList.appendChild(card);
            });
        })
        .catch(err => console.error("Error loading vendors:", err));
}

// ====================
// LIKE / UPVOTE ACTION
// ====================
function likeVendor(id) {
    fetch(`http://127.0.0.1:5000/vendor/like/${id}`, {
        method: "POST"
    })
    .then(() => {
        location.reload();
    })
    .catch(err => console.error("Like error:", err));
}
