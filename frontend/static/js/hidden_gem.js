// ====================
// NEAR ME – LOCATION BASED HIDDEN GEMS
// ====================

const detectBtn = document.getElementById("detectLocationBtn");
const gemsContainer = document.getElementById("gemsContainer");

if (detectBtn) {
  detectBtn.addEventListener("click", () => {

    if (!navigator.geolocation) {
      alert("Geolocation not supported by your browser");
      return;
    }

    detectBtn.innerText = "📍 Detecting...";
    detectBtn.disabled = true;

    navigator.geolocation.getCurrentPosition(
      position => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;

        fetch(`/api/hidden-gems?lat=${lat}&lng=${lng}&radius=5`)
          .then(res => res.json())
          .then(data => renderHiddenGems(data))
          .catch(err => {
            console.error(err);
            gemsContainer.innerHTML =
              "<p>Failed to load nearby places 😕</p>";
          })
          .finally(() => {
            detectBtn.innerText = "📍 Near Me";
            detectBtn.disabled = false;
          });
      },
      () => {
        alert("Location permission denied");
        detectBtn.innerText = "📍 Near Me";
        detectBtn.disabled = false;
      }
    );
  });
}

// ====================
// RENDER HIDDEN GEMS
// ====================

function renderHiddenGems(gems) {
  if (!gemsContainer) return;

  gemsContainer.innerHTML = "";

  if (!Array.isArray(gems) || gems.length === 0) {
    gemsContainer.innerHTML =
      "<p>No hidden gems found near you 😕</p>";
    return;
  }

  gems.forEach(v => {
    const card = document.createElement("div");
    card.className = "vendor-card";

    card.innerHTML = `
      <span class="vendor-badge">${v.category}</span>
      <span class="vendor-rating">⭐ ${v.rating}</span>

      <h3>${v.name}</h3>
      <p>${v.area}</p>
      <p style="font-size:13px;color:#9ca3af">
        📍 ${v.distance_km} km away
      </p>
    `;

    gemsContainer.appendChild(card);
  });
}
