// ====================
// IMAGE FOLDER HELPER
// ====================
function getImageFolder(name) {
  return name
    .toLowerCase()
    .replace(/ /g, "_")
    .replace(/[^a-z_]/g, "");
}

// ====================
// MAP INITIALIZATION
// ====================
const map = L.map("map").setView([26.9124, 75.7873], 12);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  attribution: "© OpenStreetMap contributors"
}).addTo(map);

function addMarker(lat, lng, text) {
  if (lat && lng) {
    L.marker([lat, lng]).addTo(map).bindPopup(text);
  }
}

// ====================
// TOP HIDDEN GEMS ONLY
// ====================
const topGemsContainer = document.getElementById("topGems");

if (topGemsContainer) {
  fetch("/ml/top-gems")
    .then(res => res.json())
    .then(vendors => {

      topGemsContainer.innerHTML = "";

      vendors.forEach(v => {
        const folder = getImageFolder(v.name);
        const imgSrc = `/static/images/vendors/${folder}/1.jpg`;

        addMarker(
          v.latitude,
          v.longitude,
          `<b>${v.name}</b><br>${v.category}`
        );

        const card = document.createElement("div");
        card.className = "vendor-card";

        card.innerHTML = `
          <a href="/vendor/name/${encodeURIComponent(v.name)}"
             class="vendor-card-link">

            <h4>${v.name} ⭐</h4>

            <img
              src="${imgSrc}"
              class="vendor-thumbnail"
              alt="${v.name}"
              onerror="this.src='/static/images/vendors/default/default.jpg'"
            >

            <p>${v.category} • ${v.area}</p>
            <p>⭐ ${v.rating}</p>
          </a>
        `;

        topGemsContainer.appendChild(card);
      });
    })
    .catch(err => console.error("Top gems error:", err));
}
