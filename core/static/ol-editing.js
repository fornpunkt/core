const lineButton = document.querySelector('#lineButton');
const polygonButton = document.querySelector('#polygonButton');
const markerButton = document.querySelector('#markerButton');

const deleteButton = document.querySelector('#deleteButton');

const manualCoordsButton = document.querySelector('#manualCoordsButton');
const whereIStandButton = document.querySelector('#whereIStandButton');

function allowDrawing(bool) {
    lineButton.disabled = !bool;
    polygonButton.disabled = !bool;
    markerButton.disabled = !bool;
    manualCoordsButton.disabled = !bool;
    whereIStandButton.disabled = !bool;

    deleteButton.disabled = bool;
}

function writeGeoJSON(geojson) {
  const geojsonSingleInput = document.querySelector('[name=geojson]');
  if (geojsonSingleInput) {
    geojsonSingleInput.value = geojson;
  } else {
    currentGeojsonTarget.dataset.geojson = geojson;
  }
}

const editSource = new ol.source.Vector({
  format: new ol.format.GeoJSON({
    dataProjection: 'EPSG:4326',
    featureProjection: 'EPSG:3857'
  }),
});
const editLayer = new ol.layer.Vector({
  source: editSource,
  style: new ol.style.Style({
    fill: new ol.style.Fill({
      color: 'rgba(255, 255, 255, 0.2)',
    }),
    stroke: new ol.style.Stroke({
      color: '#ffcc33',
      width: 2,
    }),
    image: new ol.style.Circle({
      radius: 7,
      fill: new ol.style.Fill({
        color: '#ffcc33',
      }),
    }),
  }),
});

map.addLayer(editLayer);
editLayer.setZIndex(100);

const modify = new  ol.interaction.Modify({source: editSource});
map.addInteraction(modify);

let draw, snap; // global so we can remove them later
function addInteractions(geoType) {
  map.removeInteraction(draw);
  map.removeInteraction(snap);

  draw = new ol.interaction.Draw({
    source: editSource,
    type: geoType,
  });
  map.addInteraction(draw);
  snap = new ol.interaction.Snap({source: editSource});
  map.addInteraction(snap);
}

lineButton.addEventListener('click', () => addInteractions('LineString'));
polygonButton.addEventListener('click', () => addInteractions('Polygon'));
markerButton.addEventListener('click', () => addInteractions('Point'));

editSource.addEventListener('change', () => {
    if (editSource.getFeatures().length) {
        allowDrawing(false);
        const geojson  = new ol.format.GeoJSON;
        writeGeoJSON(geojson.writeFeature(editSource.getFeatures()[0], {
            dataProjection: 'EPSG:4326',
            featureProjection: 'EPSG:3857'
        }));
    } else {
        allowDrawing(true);
    }
    map.removeInteraction(draw);
    map.removeInteraction(snap);
});

deleteButton.addEventListener('click', () => {
  editSource.clear();
  writeGeoJSON('');
});

map.on('moveend', () => {
  window.localStorage.setItem('map_register_state_zoom', view.getZoom());
  window.localStorage.setItem('map_register_state_center', JSON.stringify(view.getCenter()));
});

if (document.querySelector('[name=tags]')) {
  document.querySelector('[name=tags]').addEventListener('change', (e) => {
    window.localStorage.setItem('last_used_tags', e.target.value);
  });
}

document.addEventListener('layerStateChange', () => {
  const state = builtInBaseLayers.map(layer => layer.steralizeState());
  window.localStorage.setItem('map_register_state_layers', JSON.stringify(state));
});

const urlParams = new URLSearchParams(window.location.search);
if (urlParams.get('continued')) {
  map.getView().setCenter(JSON.parse(window.localStorage.getItem('map_register_state_center')));
  map.getView().setZoom(window.localStorage.getItem('map_register_state_zoom'));

  document.querySelector('[name=tags]').value = window.localStorage.getItem('last_used_tags');

  const state = JSON.parse(window.localStorage.getItem('map_register_state_layers'));
  if (state) {
    // before reseting layers we need to remove all layers from map to avoid confilcts
    builtInBaseLayers.forEach(layer => map.removeLayer(layer.layer));
    builtInBaseLayers = [];
    state.forEach(layer => {
      const newLayer = new Layer(layer.serviceType, layer.serviceOptions, layer.name, layer.dataString);
      builtInBaseLayers.push(newLayer);
      newLayer.setOpacity(layer.opacity);
      if (layer.active) {
        newLayer.addToMap(map);
      }
    });
    refreshBaseLayerSelector();
  }
}

manualCoordsButton.addEventListener('click', function() {
  const coordValue = document.querySelector('[name=manualCoords]').value;

  let coordinate;
  try {
    coordinate = new Coordinates(coordValue);
  } catch (error) {
    return;
  }

  const pointFeature = new ol.Feature(
    new ol.geom.Point(
      ol.proj.fromLonLat([coordinate.longitude, coordinate.latitude])
    )
  );

  editSource.addFeature(pointFeature);
});

whereIStandButton.addEventListener('click', function() {
  enableGeolocation(() => {
    zoomToGeoLocation();
    setTimeout(() => {
      const pointFeature = new ol.Feature(
        new ol.geom.Point(view.getCenter())
      );

      editSource.addFeature(pointFeature);

    }, 500);
  });
});

openLamningInNewTab = true;

// editing view only
if (document.querySelector('[name=geojson]')) {
  const geojsonInput = document.querySelector('[name=geojson]');
  if (geojsonInput.value != '') {
    const existing = editSource.getFormat().readFeatures(geojsonInput.value);
    editSource.addFeatures(existing);
    view.fit(editSource.getExtent(), {padding: [10, 10, 10, 10]});
  }
}


// hide register menu-btn in editing/create/multicreate views to avoid confusion
document.querySelector('#register-btn').style.display = 'none';
