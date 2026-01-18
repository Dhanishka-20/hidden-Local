document.addEventListener("DOMContentLoaded", function () {

    // Default Jaipur center
    const map = L.map("map").setView([26.9124, 75.7873], 14);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "© OpenStreetMap"
    }).addTo(map);

    let marker = null;

    map.on("click", function (e) {
        const lat = e.latlng.lat.toFixed(6);
        const lng = e.latlng.lng.toFixed(6);

        if (marker) {
            marker.setLatLng(e.latlng);
        } else {
            marker = L.marker(e.latlng).addTo(map);
        }

        document.getElementById("latitude").value = lat;
        document.getElementById("longitude").value = lng;

        console.log("📍 Location selected:", lat, lng);
    });

});
