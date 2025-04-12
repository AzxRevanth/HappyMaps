let latitudes = [];
let longitudes = [];
let map, heatmap;

function initMap() {
  fetch("data.csv")
    .then(response => response.text())
    .then(data => {
      Papa.parse(data, {
        header: true,
        skipEmptyLines: true,
        complete: function (results) {
          results.data.forEach(row => {
            latitudes.push(parseFloat(row.latitude));
            longitudes.push(parseFloat(row.longitude));
          });

          map = new google.maps.Map(document.getElementById("map"), {
            zoom: 6,
            center: { lat: latitudes[0], lng: longitudes[0] },
            mapTypeId: "satellite",
          });

          heatmap = new google.maps.visualization.HeatmapLayer({
            data: getPoints(),
            map: map,
          });

          document
            .getElementById("toggle-heatmap")
            .addEventListener("click", toggleHeatmap);
          document
            .getElementById("change-gradient")
            .addEventListener("click", changeGradient);
          document
            .getElementById("change-opacity")
            .addEventListener("click", changeOpacity);
          document
            .getElementById("change-radius")
            .addEventListener("click", changeRadius);
        },
      });
    })
    .catch(error => {
      console.error("Error fetching data:", error);
    });
}

function toggleHeatmap() {
  heatmap.setMap(heatmap.getMap() ? null : map);
}

function changeGradient() {
  const gradient = [
    "rgba(0, 255, 255, 0)",
    "rgba(0, 255, 255, 1)",
    "rgba(0, 191, 255, 1)",
    "rgba(0, 127, 255, 1)",
    "rgba(0, 63, 255, 1)",
    "rgba(0, 0, 255, 1)",
    "rgba(0, 0, 223, 1)",
    "rgba(0, 0, 191, 1)",
    "rgba(0, 0, 159, 1)",
    "rgba(0, 0, 127, 1)",
    "rgba(63, 0, 91, 1)",
    "rgba(127, 0, 63, 1)",
    "rgba(191, 0, 31, 1)",
    "rgba(255, 0, 0, 1)",
  ];
  heatmap.set("gradient", heatmap.get("gradient") ? null : gradient);
}

function changeRadius() {
  heatmap.set("radius", heatmap.get("radius") ? null : 20);
}

function changeOpacity() {
  heatmap.set("opacity", heatmap.get("opacity") ? null : 0.2);
}

function getPoints() {
  return latitudes.map((lat, index) => new google.maps.LatLng(lat, longitudes[index]));
}

window.initMap = initMap;
