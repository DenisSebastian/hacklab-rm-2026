const puntoLimpio = [-33.5246, -70.5951];

const map = L.map('map', { zoomControl: true }).setView(puntoLimpio, 15);
let dark = true;
let tiles;

function setTiles() {
  if (tiles) map.removeLayer(tiles);
  tiles = L.tileLayer(
    dark
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    { attribution: '&copy; OpenStreetMap contributors &copy; CARTO', maxZoom: 20 }
  ).addTo(map);
}

setTiles();

const icon = L.divIcon({
  className: 'eco-marker',
  html: '<div style="width:32px;height:32px;display:grid;place-items:center;border-radius:50%;background:#0b6b57;border:3px solid #20d69a;color:#fff;box-shadow:0 0 0 5px rgba(32,214,154,.16)"><i class="fa-solid fa-recycle"></i></div>',
  iconSize: [32, 32], iconAnchor: [16, 16]
});

L.marker(puntoLimpio, { icon })
  .addTo(map)
  .bindPopup('<strong>Punto Limpio Club Vive</strong><br>El Ulmo 824, La Florida');

L.circle(puntoLimpio, {
  radius: 500,
  color: '#20d69a',
  weight: 2,
  dashArray: '5 5',
  fillColor: '#0b8c70',
  fillOpacity: 0.20
}).addTo(map).bindTooltip('Radio peatonal recomendado: 500 metros');

document.getElementById('btn-recenter').addEventListener('click', () => map.setView(puntoLimpio, 15));
document.getElementById('btn-toggle-theme').addEventListener('click', () => { dark = !dark; setTiles(); });

const slider = document.getElementById('kg-slider');
function updateImpact() {
  const kg = Number(slider.value);
  document.getElementById('kg-value').textContent = `${kg} kg`;
  document.getElementById('co2-saved').textContent = (kg * 1.16).toFixed(1);
  document.getElementById('water-saved').textContent = Math.round(kg * 30);
}
slider.addEventListener('input', updateImpact);
updateImpact();
window.addEventListener('resize', () => map.invalidateSize());
