
import { useEffect, useState } from 'react'
import axios from 'axios'
import L from 'leaflet'

import {
  MapContainer,
  TileLayer,
  GeoJSON,
  ImageOverlay,
  LayersControl
} from 'react-leaflet'

import 'leaflet/dist/leaflet.css'
import './App.css'
import AnalystChat from './AnalystChat'

const API = '/api'
const { BaseLayer, Overlay } = LayersControl

function App() {
  const [meta, setMeta] = useState(null)
  const [targets, setTargets] = useState([])
  const [targetGeoJSON, setTargetGeoJSON] = useState(null)
  const [depositGeoJSON, setDepositGeoJSON] = useState(null)
  const [prospectivityBounds, setProspectivityBounds] = useState(null)
  const [health, setHealth] = useState(false)
  const [selected, setSelected] = useState(null)
  const [cellId, setCellId] = useState('1')
  const [cell, setCell] = useState(null)
  const [explanation, setExplanation] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    async function loadData() {
      try {
        const [h, m, t, geo, deposits, bounds] = await Promise.all([
          axios.get(`${API}/health`),
          axios.get(`${API}/meta`),
          axios.get(`${API}/targets`),
          axios.get('/targets.geojson'),
          axios.get('/deposits.geojson'),
          axios.get('/prospectivity_bounds.json')
        ])

        setHealth(h.data.status === 'healthy')
        setMeta(m.data)
        setTargets(t.data.targets || [])
        setTargetGeoJSON(geo.data)
        setDepositGeoJSON(deposits.data)
        setProspectivityBounds(bounds.data)

        if (t.data.targets?.length) {
          setSelected(t.data.targets[0])
        }
      } catch (err) {
        console.error(err)
        setError(
          'Unable to load GeoMine data. Check Flask, GeoJSON and prospectivity files.'
        )
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  async function analyseCell(event) {
    event.preventDefault()
    setCell(null)
    setExplanation(null)
    setError('')

    try {
      const [c, e] = await Promise.all([
        axios.get(`${API}/cell`, {
          params: { grid_fid: cellId }
        }),
        axios.get(`${API}/explain`, {
          params: { grid_fid: cellId }
        })
      ])

      setCell(c.data)
      setExplanation(e.data)
    } catch (err) {
      setError(
        err.response?.data?.error ||
        'Unable to retrieve cell information.'
      )
    }
  }

  const score = value => Number(value ?? 0).toFixed(4)

  const components = [
    ['Sources', cell?.components?.sources],
    ['Energy', cell?.components?.energy],
    ['Pathways', cell?.components?.pathways],
    ['Deposition', cell?.components?.deposition]
  ]

  function getTargetStyle(feature) {
    const isSelected =
      selected?.target_id === feature.properties.target_id

    return {
      color: isSelected ? '#f59e0b' : '#1d4ed8',
      weight: isSelected ? 4 : 2,
      fillColor: isSelected ? '#f59e0b' : '#3b82f6',
      fillOpacity: isSelected ? 0.55 : 0.30
    }
  }

  function handleTargetFeature(feature, layer) {
    const p = feature.properties

    layer.bindPopup(`
      <strong>${p.target_id}</strong><br/>
      Mean PU score: ${Number(p.mean_score).toFixed(4)}<br/>
      Maximum PU score: ${Number(p.max_score).toFixed(4)}<br/>
      Area: ${Number(p.area_km2).toFixed(2)} km²<br/>
      Known deposit cells: ${p.deposit_cells}
    `)

    layer.on('click', () => {
      const target = targets.find(
        item => item.target_id === p.target_id
      )

      if (target) setSelected(target)
    })
  }

  function depositPoint(feature, latlng) {
    return L.circleMarker(latlng, {
      radius: 6,
      color: '#ffffff',
      weight: 1.5,
      fillColor: '#dc2626',
      fillOpacity: 1
    })
  }

  function handleDepositFeature(feature, layer) {
    const p = feature.properties || {}

    const name =
      p.deposit_name ||
      p.name ||
      p.deposit ||
      p.Name ||
      'Known IOCG deposit'

    layer.bindPopup(
      `<strong>${name}</strong><br/>Known IOCG deposit`
    )
  }

  const imageBounds = prospectivityBounds
    ? [
        [prospectivityBounds.south, prospectivityBounds.west],
        [prospectivityBounds.north, prospectivityBounds.east]
      ]
    : null

  return (
    <div className="app-shell">

      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">G</div>
          <div>
            <h1>GeoMine</h1>
            <span>IOCG PROSPECTIVITY INTELLIGENCE</span>
          </div>
        </div>

        <div className="connection">
          <span className={health ? 'online-dot' : 'offline-dot'} />
          {health ? 'API Connected' : 'API Offline'}
        </div>
      </header>

      <main className="dashboard">

        <section className="welcome">
          <p>EXPLORATION INTELLIGENCE PLATFORM</p>
          <h2>IOCG Prospectivity Dashboard</h2>
          <span>
            Tennant Creek – Mount Isa Investigation Area, Australia
          </span>
        </section>

        {error && <div className="error">{error}</div>}

        {loading ? (
          <p>Loading GeoMine data...</p>
        ) : (
          <>

            <section className="stats">
              <Stat
                title="Grid Cells"
                value={meta?.grid_cells?.toLocaleString()}
              />
              <Stat
                title="Predictors"
                value={meta?.predictor_count}
              />
              <Stat
                title="Known Deposits"
                value={meta?.known_positive_cells}
              />
              <Stat
                title="Refined Targets"
                value={targets.length}
              />
            </section>

            <section className="content-grid">

              <div className="panel">
                <h3>IOCG Prospectivity Map</h3>

                <p className="muted">
                  ML-based Positive-Unlabelled prospectivity scores
                  with refined exploration targets and known deposits.
                </p>

                <div className="map">
                  <MapContainer
                    center={[-19.5, 137]}
                    zoom={6}
                    scrollWheelZoom
                    className="leaflet-map"
                  >
                    <LayersControl position="topright">

                      <BaseLayer checked name="OpenStreetMap">
                        <TileLayer
                          attribution="© OpenStreetMap contributors"
                          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        />
                      </BaseLayer>

                      <Overlay
                        checked
                        name="ML Prospectivity Surface"
                      >
                        {imageBounds && (
                          <ImageOverlay
                            url="/prospectivity.png"
                            bounds={imageBounds}
                            opacity={0.85}
                            zIndex={1}
                          />
                        )}
                      </Overlay>

                      <Overlay checked name="Refined Target Polygons">
                        {targetGeoJSON && (
                          <GeoJSON
                            key={selected?.target_id || 'all-targets'}
                            data={targetGeoJSON}
                            style={getTargetStyle}
                            onEachFeature={handleTargetFeature}
                          />
                        )}
                      </Overlay>

                      <Overlay checked name="Known IOCG Deposits">
                        {depositGeoJSON && (
                          <GeoJSON
                            data={depositGeoJSON}
                            pointToLayer={depositPoint}
                            onEachFeature={handleDepositFeature}
                          />
                        )}
                      </Overlay>

                    </LayersControl>
                  </MapContainer>
                </div>

                <div className="prospectivity-legend">
                  <strong>ML Prospectivity Score</strong>

                  <div className="gradient-bar" />

                  <div className="gradient-labels">
                    <span>Low (0)</span>
                    <span>Moderate (0.5)</span>
                    <span>High (1)</span>
                  </div>
                </div>

                <div className="map-legend">
                  <span>
                    <i className="legend-blue" /> Other targets
                  </span>
                  <span>
                    <i className="legend-orange" /> Selected target
                  </span>
                  <span>
                    <i className="legend-red" /> Known deposits
                  </span>
                </div>
              </div>

              <div className="panel">
                <h3>Exploration Targets</h3>

                <p className="muted">
                  Select a target to view its summary.
                </p>

                <div className="target-list">
                  {targets.map((target, index) => (
                    <button
                      key={target.target_id}
                      className={`target-row ${
                        selected?.target_id === target.target_id
                          ? 'active'
                          : ''
                      }`}
                      onClick={() => setSelected(target)}
                    >
                      <span>
                        {index + 1}. {target.target_id}
                      </span>
                      <span>{score(target.mean_pu_score)}</span>
                    </button>
                  ))}
                </div>
              </div>

            </section>

            {selected && (
              <section className="panel">
                <h3>Selected Target: {selected.target_id}</h3>

                <div className="target-summary">
                  <Stat
                    title="Mean PU Score"
                    value={score(selected.mean_pu_score)}
                  />
                  <Stat
                    title="Maximum PU Score"
                    value={score(selected.maximum_pu_score)}
                  />
                  <Stat
                    title="Area (km²)"
                    value={Number(selected.area_km2).toFixed(2)}
                  />
                  <Stat
                    title="Known Deposit Cells"
                    value={selected.known_deposit_cells}
                  />
                </div>
              </section>
            )}

            <section className="panel">
              <h3>Cell-Level Geological Explanation</h3>

              <p className="muted">
                Enter a grid cell FID to retrieve its geological information.
              </p>

              <form
                className="search-form"
                onSubmit={analyseCell}
              >
                <input
                  type="number"
                  min="1"
                  value={cellId}
                  onChange={event => setCellId(event.target.value)}
                  required
                />

                <button type="submit">Analyse Cell</button>
              </form>

              {cell && explanation && (
                <>
                  <div className="cell-summary">
                    <Stat title="Grid FID" value={cell.grid_fid} />

                    <Stat
                      title="PU Score"
                      value={score(cell.prospectivity.pu_score)}
                    />

                    <Stat
                      title="PU Percentile"
                      value={`${score(cell.prospectivity.pu_percentile)}%`}
                    />

                    <Stat
                      title="Data Completeness"
                      value={`${cell.data_coverage.completeness_percent}%`}
                    />
                  </div>

                  <h4>Mineral-System Components</h4>

                  <div className="component-grid">
                    {components.map(([name, value]) => (
                      <div className="component-card" key={name}>
                        <span>{name}</span>
                        <strong>{score(value)}</strong>

                        <div className="progress">
                          <div
                            style={{
                              width: `${Math.max(
                                0,
                                Math.min(100, value || 0)
                              )}%`
                            }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  <h4>Top Three Geological Drivers</h4>

                  {explanation.top_geological_drivers.map(
                    (driver, index) => (
                      <div className="driver" key={driver.criterion}>
                        <strong>
                          {index + 1}. {driver.criterion}
                        </strong>

                        <span>{driver.component}</span>

                        <b>
                          {score(
                            driver.weighted_component_contribution
                          )}
                        </b>
                      </div>
                    )
                  )}

                  <p className="muted">
                    {explanation.interpretation_note}
                  </p>
                </>
              )}
            </section>

            <section className="panel">
              <AnalystChat />
            </section>

            <section className="panel">
              <h3>Model Information</h3>

              <p>Model: {meta?.model}</p>
              <p>Coordinate System: {meta?.crs}</p>

              <p>
                Grid Resolution: {meta?.grid_resolution_metres} metres
              </p>

              <p>
                Unlabelled Cells: {meta?.unlabelled_cells?.toLocaleString()}
              </p>

              <p className="muted">
                PU scores are ranking scores, not calibrated probabilities.
                Unlabelled cells are not confirmed negative locations.
              </p>
            </section>

          </>
        )}

        <footer>GeoMine IOCG Prospectivity Prototype</footer>

      </main>
    </div>
  )
}

function Stat({ title, value }) {
  return (
    <div className="stat-card">
      <span>{title}</span>
      <strong>{value ?? '—'}</strong>
    </div>
  )
}

export default App
