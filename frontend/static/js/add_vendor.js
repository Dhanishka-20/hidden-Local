document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("vendorForm");
  const imageInput = document.getElementById("vendorImages");
  const preview = document.getElementById("imagePreviewContainer");

  /* ====================
     MAP INITIALIZATION
  ==================== */
  const map = L.map("map").setView([26.9124, 75.7873], 13);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap contributors"
  }).addTo(map);

  let marker;
  map.on("click", e => {
    if (marker) marker.setLatLng(e.latlng);
    else marker = L.marker(e.latlng).addTo(map);

    document.getElementById("latitude").value = e.latlng.lat;
    document.getElementById("longitude").value = e.latlng.lng;
  });

  /* ====================
     IMAGE PREVIEW
  ==================== */
  imageInput.addEventListener("change", () => {
    preview.innerHTML = "";
    const files = imageInput.files;

    if (files.length > 5) {
      alert("You can upload a maximum of 5 images.");
      imageInput.value = "";
      return;
    }

    [...files].forEach(file => {
      const reader = new FileReader();
      reader.onload = e => {
        const img = document.createElement("img");
        img.src = e.target.result;
        img.style.width = "120px";
        img.style.margin = "6px";
        img.style.borderRadius = "6px";
        preview.appendChild(img);
      };
      reader.readAsDataURL(file);
    });
  });

  /* ====================
     FORM SUBMIT
  ==================== */
  form.addEventListener("submit", e => {
    e.preventDefault();

    const formData = new FormData(form);

    fetch("/add-vendor", {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(() => {
        alert("Vendor added successfully!");
        window.location.href = "/explore"; // 👈 SHOW IMMEDIATELY
      })
      .catch(() => {
        alert("Error submitting vendor");
      });
  });
});
