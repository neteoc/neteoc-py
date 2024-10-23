const osm = "https://www.openstreetmap.org/copyright";
const copy = `© <a href='${osm}'>OpenStreetMap</a>`;
const url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const layer = L.tileLayer(url, { attribution: copy });
const map = L.map("map", { layers: [layer] });
// map.fitWorld();
const data = document.getElementById("markers-data");
const markers = JSON.parse(data.textContent);
let feature = L.geoJSON(markers)
  .bindPopup(function (layer) {
    let returntext = "";
    return returntext.concat(layer.feature.properties.name, "<br>", layer.feature.properties.description);

  })
  .addTo(map);
map.fitBounds(feature.getBounds());
