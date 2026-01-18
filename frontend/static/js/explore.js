console.log("EXPLORE JS LOADED");

const vendorList = document.getElementById("vendorList");
const searchInput = document.getElementById("searchInput");
const categoryFilter = document.getElementById("categoryFilter");
const nearMeBtn = document.getElementById("nearMeBtn");
const resetBtn = document.getElementById("resetBtn");
const title = document.getElementById("exploreTitle");

let allVendors = [];

/* ================= RENDER VENDORS ================= */
function renderVendors(vendors) {
    vendorList.innerHTML = "";

    if (!vendors || vendors.length === 0) {
        vendorList.innerHTML = "<p>No places found.</p>";
        return;
    }

    vendors.forEach(v => {
        const zomato = 'https://www.zomato.com/jaipur/search?q=${encodeURIComponent(v.name)}';
        const swiggy = 'https://www.swiggy.com/jaipur/search?query=${encodeURIComponent(v.name)}';
        const map = 'https://www.google.com/maps?q=${v.latitude},${v.longitude}';

        vendorList.innerHTML += `
            <div class="vendor-card">
                <span class="vendor-badge">${v.category}</span>
                <span class="vendor-rating">⭐ ${v.rating || "N/A"}</span>

                <h3>${v.name}</h3>
                <p>${v.area}</p>

                <div class="card-actions">
                    <a href="${map}" target="_blank" class="direction-btn">Directions</a>
                    ${
                        v.category.toLowerCase().includes("food") ? `
                        <a href="${zomato}" target="_blank" class="zomato-btn">Zomato</a>
                        <a href="${swiggy}" target="_blank" class="swiggy-btn">Swiggy</a>
                        ` : ""
                    }
                </div>
            </div>
        `;
    });
}

/* ================= FETCH ALL ================= */
fetch("/vendors")
    .then(res => res.json())
    .then(data => {
        console.log("VENDORS RECEIVED:", data);
        allVendors = data;
        renderVendors(allVendors);
    })
    .catch(err => console.error("Fetch error:", err));

/* ================= FILTER ================= */
function applyFilters() {
    const search = searchInput.value.toLowerCase();
    const category = categoryFilter.value;

    const filtered = allVendors.filter(v =>
        (v.name.toLowerCase().includes(search) ||
         v.area.toLowerCase().includes(search)) &&
        (!category || v.category === category)
    );

    renderVendors(filtered);
}

searchInput.addEventListener("input", applyFilters);
categoryFilter.addEventListener("change", applyFilters);

/* ================= NEAR ME ================= */
nearMeBtn.addEventListener("click", () => {
    if (!navigator.geolocation) {
        alert("Geolocation not supported");
        return;
    }

    nearMeBtn.innerText = "Detecting...";
    nearMeBtn.disabled = true;

    navigator.geolocation.getCurrentPosition(pos => {
        const userLat = pos.coords.latitude;
        const userLng = pos.coords.longitude;

        const nearby = allVendors.filter(v => {
            if (!v.latitude || !v.longitude) return false;

            const dist = Math.sqrt(
                Math.pow(userLat - v.latitude, 2) +
                Math.pow(userLng - v.longitude, 2)
            );

            return dist < 0.05; // ~5 km approx
        });

        title.innerText = "Places Near You";
        renderVendors(nearby);

        nearMeBtn.innerText = "📍 Near Me";
        nearMeBtn.disabled = false;
    });
});

/* ================= RESET ================= */
resetBtn.addEventListener("click", () => {
    searchInput.value = "";
    categoryFilter.value = "";
    title.innerText = "Explore Hidden Places";
    renderVendors(allVendors);
});