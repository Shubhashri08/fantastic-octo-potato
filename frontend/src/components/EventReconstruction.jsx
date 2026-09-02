import React, { useEffect, useRef, useState, useMemo } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Navigation, MapPin, Clock, ShieldAlert, Sparkles, Activity, 
  RefreshCw, CheckCircle2, ChevronRight, AlertTriangle, Eye, Compass, 
  Layers, ArrowRight, ShieldCheck, Info, CornerDownRight, Radio, Filter,
  Flame, Car, User, AlertOctagon
} from 'lucide-react';
import { analyzeReconstruction } from '../api/events';

export default function EventReconstruction({ events = [], cameras = [], onNavigateToLive }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);

  // Filters for Event Dropdown
  const [filterThreat, setFilterThreat] = useState('ALL');
  const [filterCamera, setFilterCamera] = useState('ALL');

  // Filtered Events
  const filteredEvents = useMemo(() => {
    return events.filter((ev) => {
      let matchThreat = true;
      if (filterThreat !== 'ALL') {
        const evType = (ev.event_type || '').toLowerCase();
        const tf = filterThreat.toLowerCase();
        if (tf === 'fighting') matchThreat = evType.includes('fight') || evType.includes('violenc');
        else if (tf === 'vehicle collision') matchThreat = evType.includes('collision') || evType.includes('crash');
        else if (tf === 'fire') matchThreat = evType.includes('fire') || evType.includes('flame');
        else if (tf === 'smoke') matchThreat = evType.includes('smoke');
        else if (tf === 'accident') matchThreat = evType.includes('accident');
        else if (tf === 'person') matchThreat = evType.includes('person') || evType.includes('pedestrian');
        else if (tf === 'vehicle') matchThreat = evType.includes('vehicle') || evType.includes('car');
        else matchThreat = evType.includes(tf);
      }

      let matchCam = true;
      if (filterCamera !== 'ALL') {
        const cid = parseInt(filterCamera.replace('CAM-0', '').replace('CAM-', ''), 10);
        matchCam = ev.camera_id === cid;
      }

      return matchThreat && matchCam;
    });
  }, [events, filterThreat, filterCamera]);

  // Selected Event & Reconstruction State
  const [selectedEventId, setSelectedEventId] = useState(events[0]?.id || '');
  const [analysisState, setAnalysisState] = useState('idle'); // 'idle' | 'analyzing' | 'complete' | 'error'
  const [analysisStep, setAnalysisStep] = useState('');
  const [reconstructionData, setReconstructionData] = useState(null);
  const [selectedPathId, setSelectedPathId] = useState('PATH-01');
  const [analysisError, setAnalysisError] = useState(null);

  // Keep selected event synced when filter changes
  useEffect(() => {
    if (filteredEvents.length > 0) {
      if (!filteredEvents.some(e => e.id === parseInt(selectedEventId, 10))) {
        setSelectedEventId(filteredEvents[0].id);
      }
    }
  }, [filteredEvents, selectedEventId]);

  // Initialize Leaflet Map Instance Once with robust cleanup
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapContainerRef.current._leaflet_id && !mapInstanceRef.current) {
      mapContainerRef.current._leaflet_id = null;
    }

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [12.9756, 77.6067],
        zoom: 13,
        zoomControl: false,
        preferCanvas: true
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // CARTO Dark Cyber Basemap (with API key support)
      const cartoApiKey = (import.meta.env.VITE_CARTO_API_KEY || import.meta.env.VITE_MAP_API_KEY || 'cb1_2pk7_1_90609325753bc4f1255b1901').trim();
      const cartoUrl = cartoApiKey 
        ? `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?api_key=${cartoApiKey}`
        : 'https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png';

      const tileLayer = L.tileLayer(cartoUrl, {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        subdomains: 'abcd'
      });


      tileLayer.on('tileerror', (err, tile) => {
        if (tile) tile.src = 'https://tile.openstreetmap.org/0/0/0.png';
      });

      tileLayer.addTo(map);



      const markerLayer = L.layerGroup().addTo(map);
      layerGroupRef.current = markerLayer;
      mapInstanceRef.current = map;

      setTimeout(() => {
        if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
      }, 300);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
        layerGroupRef.current = null;
      }
      if (mapContainerRef.current) {
        mapContainerRef.current._leaflet_id = null;
      }
    };
  }, []);

  // Execute Event Reconstruction Analysis
  const handleExecuteReconstruction = async () => {
    if (!selectedEventId) return;
    setAnalysisState('analyzing');
    setAnalysisError(null);
    setReconstructionData(null);

    try {
      setAnalysisStep('ANALYZING INCIDENT TELEMETRY...');
      await new Promise(r => setTimeout(r, 180));

      setAnalysisStep('LOADING GEOSPATIAL CAMERA GRAPH...');
      await new Promise(r => setTimeout(r, 220));

      setAnalysisStep('EVALUATING PRE-INCIDENT SIGHTINGS...');
      await new Promise(r => setTimeout(r, 220));

      setAnalysisStep('GENERATING CORRIDOR GRAPH...');
      const data = await analyzeReconstruction(selectedEventId);

      setAnalysisStep('COMPUTING DYNAMIC LIKELIHOOD FACTOR SCORES...');
      await new Promise(r => setTimeout(r, 200));

      setReconstructionData(data);
      setSelectedPathId(data.candidate_paths?.[0]?.path_id || 'PATH-01');
      setAnalysisState('complete');
    } catch (err) {
      console.error('Reconstruction failed:', err);
      setAnalysisError(err.message || 'Geospatial reconstruction failed. Insufficient trajectory data for this event.');
      setAnalysisState('error');
    }
  };

  // Render Geospatial Map Layers (Event Origin, Observed Path, Candidate Paths, Checkpoints)
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current || !reconstructionData) return;

    const map = mapInstanceRef.current;
    const layerGroup = layerGroupRef.current;
    layerGroup.clearLayers();

    const { event, mode, observed_path, candidate_paths, next_checkpoints } = reconstructionData;
    const bounds = L.latLngBounds();

    // 1. EVENT ORIGIN MARKER (Pulsing Highlighted Red Pin)
    if (event && typeof event.lat === 'number' && typeof event.lon === 'number') {
      const eventLatLng = [event.lat, event.lon];
      bounds.extend(eventLatLng);

      const eventMarker = L.circleMarker(eventLatLng, {
        radius: 12,
        fillColor: '#EF4444',
        color: '#FFFFFF',
        weight: 3.5,
        opacity: 1,
        fillOpacity: 0.95
      });

      const latStr = (event.lat ?? 0).toFixed(4);
      const lonStr = (event.lon ?? 0).toFixed(4);

      eventMarker.bindPopup(`
        <div style="font-family: monospace; font-size: 11px; padding: 6px; min-width: 190px;">
          <div style="font-weight: 900; color: #EF4444; font-size: 12px;">🔴 INCIDENT GROUND ZERO</div>
          <div style="font-weight: bold; color: #0f172a; margin-top: 3px;">${event.event_type || 'Incident'} (#EVT-${event.id || '0'})</div>
          <div style="color: #64748b; font-size: 10px; margin-top: 2px;">${event.camera_name || 'Surveillance Node'}</div>
          <div style="color: #0284c7; font-weight: bold; margin-top: 4px;">Lat: ${latStr} · Lon: ${lonStr}</div>
          <div style="color: #475569; font-size: 10px;">Logged: ${event.timestamp || 'Recent'}</div>
        </div>
      `);
      eventMarker.addTo(layerGroup);


      // Add Exclusion Radius Circle for Fire/Smoke
      if (mode === 'incident_spread') {
        const fireCircle = L.circle(eventLatLng, {
          radius: 500,
          color: '#EF4444',
          fillColor: '#EF4444',
          fillOpacity: 0.15,
          dashArray: '4, 4'
        });
        fireCircle.bindTooltip('500m Containment Exclusion Perimeter', { sticky: true });
        fireCircle.addTo(layerGroup);
      }
    }

    // 2. OBSERVED HISTORICAL TRAJECTORY (Solid Line)
    if (observed_path && observed_path.geometry && observed_path.geometry.length > 1) {
      observed_path.geometry.forEach(pt => bounds.extend(pt));

      const observedPolyline = L.polyline(observed_path.geometry, {
        color: '#00F2FE',
        weight: 4.5,
        opacity: 0.85
      });
      observedPolyline.bindTooltip('OBSERVED SIGHTINGS (Verified Telemetry)', { sticky: true });
      observedPolyline.addTo(layerGroup);

      // Checkpoints along observed path
      observed_path.checkpoints?.forEach(cp => {
        const cpMarker = L.circleMarker([cp.lat, cp.lon], {
          radius: 6,
          fillColor: '#00F2FE',
          color: '#FFFFFF',
          weight: 2,
          fillOpacity: 1
        });
        cpMarker.bindPopup(`
          <div style="font-family: monospace; font-size: 11px; padding: 4px;">
            <div style="font-weight: bold; color: #00F2FE;">CONFIRMED SIGHTING</div>
            <div style="color: #0f172a;">${cp.camera_name || cp.camera_id}</div>
            <div style="color: #64748b; font-size: 10px;">Time: ${cp.timestamp} • Speed: ${cp.speed_kmh} km/h</div>
          </div>
        `);
        cpMarker.addTo(layerGroup);
      });
    }

    // 3. CANDIDATE PREDICTED ROUTES (Dashed Polylines)
    if (candidate_paths && candidate_paths.length > 0) {
      candidate_paths.forEach((path) => {
        const isSelected = path.path_id === selectedPathId;
        const isMostLikely = path.is_most_likely;

        path.geometry.forEach(pt => bounds.extend(pt));

        const pathColor = isMostLikely ? '#10B981' : path.path_id.includes('02') ? '#F59E0B' : '#8B5CF6';
        const polyline = L.polyline(path.geometry, {
          color: pathColor,
          weight: isSelected ? 6.5 : (isMostLikely ? 4.5 : 3),
          dashArray: isSelected ? '10, 8' : '6, 6',
          opacity: isSelected ? 1 : 0.6
        });

        polyline.bindTooltip(`${path.name} (${path.likelihood_percent}% Likelihood)`, { sticky: true });
        polyline.on('click', () => setSelectedPathId(path.path_id));
        polyline.addTo(layerGroup);
      });
    }

    // 4. NEXT CCTV CHECKPOINT MARKERS
    if (next_checkpoints && next_checkpoints.length > 0) {
      next_checkpoints.forEach((cp) => {
        const cpLatLng = [cp.lat, cp.lon];
        bounds.extend(cpLatLng);

        const cpMarker = L.circleMarker(cpLatLng, {
          radius: 8,
          fillColor: '#38BDF8',
          color: '#0A0A0A',
          weight: 2.5,
          opacity: 1,
          fillOpacity: 0.95
        });

        cpMarker.bindPopup(`
          <div style="font-family: monospace; font-size: 11px; padding: 6px; min-width: 180px;">
            <div style="font-weight: bold; color: #0284c7; font-size: 12px;">★ NEXT CCTV CHECKPOINT</div>
            <div style="font-weight: bold; color: #0f172a; margin-top: 2px;">${cp.camera_id}: ${cp.camera_name}</div>
            <div style="color: #64748b; font-size: 10px; margin-top: 3px;">Distance: ${cp.distance_km} km</div>
            <div style="color: #059669; font-weight: bold; font-size: 11px;">ETA Window: ${cp.eta_window}</div>
            <div style="color: #2563eb; font-weight: bold;">Likelihood: ${cp.likelihood_percent}%</div>
          </div>
        `);
        cpMarker.addTo(layerGroup);
      });
    }

    // Fit Map View to Active Bounds
    if (bounds.isValid()) {
      map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
    }
  }, [reconstructionData, selectedPathId]);

  return (
    <div className="flex flex-col lg:flex-row h-full overflow-hidden bg-[#0A0A0A] text-[#e5e2e1]">
      {/* LEFT: Leaflet Map Viewport */}
      <div className="flex-1 h-full relative overflow-hidden border-r border-[#222]">
        <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: '100%' }} />

        {/* Floating Top Left Control Panel */}
        <div className="absolute top-4 left-4 z-[400] bg-[#111111]/95 border border-[#2A2A2A] p-4 backdrop-blur-md rounded-2xl shadow-2xl space-y-3 max-w-md w-full font-mono">
          <div className="flex items-center justify-between border-b border-[#222] pb-2">
            <div className="flex items-center gap-2">
              <Compass className="w-4 h-4 text-[#f5dfc0]" />
              <h2 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider">
                Event Reconstruction
              </h2>
            </div>
            <span className="text-[10px] text-[#9ed1c1] bg-[#142820] px-2 py-0.5 rounded border border-[#1d4f43] font-bold">
              DEMO DATASET ACTIVE
            </span>
          </div>

          {/* Compact Filter Toolbar */}
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <label className="text-[9px] text-[#858585] block uppercase mb-0.5">Threat Class</label>
              <select
                value={filterThreat}
                onChange={(e) => setFilterThreat(e.target.value)}
                className="w-full px-2 py-1 bg-[#0a0a0a] border border-[#333] rounded-lg text-[11px] text-[#e5e2e1] outline-none"
              >
                <option value="ALL">All Threat Types</option>
                <option value="VEHICLE COLLISION">Vehicle Collision</option>
                <option value="FIGHTING">Fighting / Altercation</option>
                <option value="FIRE">Fire Outbreak</option>
                <option value="SMOKE">Smoke Sensor</option>
                <option value="ACCIDENT">Accident</option>
                <option value="VEHICLE">Vehicle BOLO</option>
                <option value="PERSON">Person / Pedestrian</option>
              </select>
            </div>

            <div>
              <label className="text-[9px] text-[#858585] block uppercase mb-0.5">Camera Node</label>
              <select
                value={filterCamera}
                onChange={(e) => setFilterCamera(e.target.value)}
                className="w-full px-2 py-1 bg-[#0a0a0a] border border-[#333] rounded-lg text-[11px] text-[#e5e2e1] outline-none"
              >
                <option value="ALL">All 6 Cameras</option>
                <option value="CAM-01">CAM-01: Mumbai CSMT</option>
                <option value="CAM-02">CAM-02: Bengaluru MG Road</option>
                <option value="CAM-03">CAM-03: Mumbai Marine Drive</option>
                <option value="CAM-04">CAM-04: Bengaluru Trinity Circle</option>
                <option value="CAM-05">CAM-05: Bengaluru Ring Road</option>
                <option value="CAM-06">CAM-06: Mumbai Worli Sea Face</option>
              </select>
            </div>
          </div>

          {/* Incident Selector Dropdown */}
          <div className="space-y-1.5">
            <label className="text-[10px] text-[#858585] uppercase block">
              Select Investigative Incident ({filteredEvents.length} Available):
            </label>
            <select
              value={selectedEventId}
              onChange={(e) => setSelectedEventId(e.target.value)}
              className="w-full px-3 py-2 bg-[#0a0a0a] border border-[#333] rounded-xl text-xs text-[#f5dfc0] font-bold outline-none focus:border-[#00F2FE]"
            >
              {filteredEvents.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  #EVT-{ev.id} · {ev.event_type} · CAM-0{ev.camera_id} ({ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Recent'})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleExecuteReconstruction}
            disabled={analysisState === 'analyzing' || filteredEvents.length === 0}
            className="w-full py-2.5 bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] hover:opacity-95 text-[#0A0A0A] font-black text-xs uppercase tracking-wider rounded-xl transition shadow-lg flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {analysisState === 'analyzing' ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                {analysisStep}
              </>
            ) : (
              <>
                <Navigation className="w-3.5 h-3.5" />
                RECONSTRUCT EVENT MOVEMENT
              </>
            )}
          </button>
        </div>

        {/* Floating Map Legend (Bottom Left) */}
        <div className="absolute bottom-4 left-4 z-[400] bg-black/85 border border-[#222] px-3 py-2 rounded-xl text-[10px] font-mono text-[#a3a3a3] backdrop-blur-md flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500" />
            <span>Event Origin</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00F2FE]" />
            <span>Observed (Solid)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 bg-emerald-400 border-t border-dashed border-white" />
            <span>Most Likely (Dashed)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-400" />
            <span>Next Checkpoint</span>
          </div>
        </div>
      </div>

      {/* RIGHT: Reconstruction Analysis Sidebar */}
      <div className="w-full lg:w-[460px] flex-shrink-0 bg-[#0d0d0d] p-5 flex flex-col justify-between overflow-y-auto space-y-5 font-mono">
        {analysisState === 'complete' && reconstructionData ? (
          <div className="space-y-5">
            {/* Header Summary Card */}
            <div className="bg-[#141414] border border-[#262626] rounded-2xl p-4 shadow-xl space-y-3">
              <div className="flex items-center justify-between border-b border-[#222] pb-2">
                <span className="text-[10px] text-emerald-400 bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800 font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> RECONSTRUCTION COMPLETE
                </span>
                <span className="text-[10px] text-[#858585]">
                  {reconstructionData.event.timestamp}
                </span>
              </div>

              {/* Mode Badge */}
              <div className="text-[11px] font-bold text-cyan-300 bg-cyan-950/60 border border-cyan-800/80 p-2 rounded-lg">
                MODE: {reconstructionData.mode_label}
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-[9px] text-[#858585] block uppercase">Event Type</span>
                  <span className="font-bold text-[#f5dfc0]">{reconstructionData.event.event_type}</span>
                </div>
                <div>
                  <span className="text-[9px] text-[#858585] block uppercase">Last Observed</span>
                  <span className="font-bold text-cyan-300 truncate block">{reconstructionData.summary.last_known_checkpoint}</span>
                </div>
                <div>
                  <span className="text-[9px] text-[#858585] block uppercase">Most Likely Next</span>
                  <span className="font-bold text-emerald-400 truncate block">{reconstructionData.summary.most_likely_next_checkpoint}</span>
                </div>
                <div>
                  <span className="text-[9px] text-[#858585] block uppercase">Likelihood / Window</span>
                  <span className="font-bold text-white">{reconstructionData.summary.likelihood_percent}% ({reconstructionData.summary.estimated_window})</span>
                </div>
              </div>
            </div>

            {/* Candidate Predicted Paths List */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#f5dfc0] uppercase">
                  {reconstructionData.mode === 'incident_spread' ? 'EMERGENCY INGRESS CORRIDORS' : `PREDICTED MOVEMENT CORRIDORS (${reconstructionData.candidate_paths.length})`}
                </span>
                <span className="text-[10px] text-[#858585]">Click route to highlight</span>
              </div>

              <div className="space-y-2.5">
                {reconstructionData.candidate_paths.map((p) => {
                  const isSelected = p.path_id === selectedPathId;
                  return (
                    <motion.div
                      key={p.path_id}
                      whileHover={{ scale: 1.01 }}
                      onClick={() => setSelectedPathId(p.path_id)}
                      className={`p-3.5 rounded-xl border cursor-pointer transition text-xs space-y-2 ${
                        isSelected 
                          ? 'bg-[#181818] border-[#f5dfc0] shadow-lg' 
                          : 'bg-[#121212] border-[#242424] hover:border-[#383838]'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-[#f5dfc0] flex items-center gap-1.5">
                          {p.is_most_likely ? '★ MOST LIKELY CORRIDOR' : `ALTERNATIVE ROUTE ${p.path_id.split('-')[1]}`}
                        </span>
                        <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                          p.is_most_likely 
                            ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' 
                            : 'bg-[#222] text-[#aaa] border border-[#333]'
                        }`}>
                          {p.likelihood_percent}% LIKELIHOOD
                        </span>
                      </div>

                      <div className="text-[11px] text-[#c5c5c5] leading-relaxed">
                        {p.name}
                      </div>

                      <div className="grid grid-cols-3 gap-2 text-[10px] text-[#858585] pt-1 border-t border-[#222]">
                        <div>Est. Time: <span className="text-white font-bold">{p.estimated_minutes} min</span></div>
                        <div>Distance: <span className="text-white font-bold">{p.distance_km} km</span></div>
                        <div>Cameras: <span className="text-cyan-300 font-bold">{p.camera_count} Checkpoints</span></div>
                      </div>

                      {/* Factor Breakdown */}
                      {isSelected && (
                        <div className="p-2.5 bg-[#090909] rounded-lg border border-[#222] text-[10px] space-y-1.5 mt-2">
                          <div className="text-[#f5dfc0] font-bold uppercase flex items-center gap-1">
                            <Info className="w-3 h-3 text-[#00F2FE]" /> Why this route? (Factor Breakdown):
                          </div>
                          <div className="grid grid-cols-1 gap-1 text-[#858585]">
                            <div>• Road Connectivity: <span className="text-white font-medium">{p.factors.road_connectivity}</span></div>
                            <div>• Travel Time: <span className="text-white font-medium">{p.factors.travel_time}</span></div>
                            <div>• Direction Alignment: <span className="text-white font-medium">{p.factors.direction_compatibility}</span></div>
                            <div>• Camera Surveillance: <span className="text-white font-medium">{p.factors.camera_coverage}</span></div>
                          </div>
                        </div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Next Checkpoints */}
            <div className="space-y-3">
              <span className="text-xs font-bold text-[#f5dfc0] uppercase block">
                {reconstructionData.mode === 'incident_spread' ? 'PERIMETER SENSOR NODES' : 'NEXT CCTV CHECKPOINTS'}
              </span>

              <div className="space-y-2">
                {reconstructionData.next_checkpoints.map((cp, idx) => (
                  <div key={idx} className="p-3 bg-[#121212] border border-[#242424] rounded-xl text-xs flex items-center justify-between">
                    <div>
                      <div className="font-bold text-[#e5e2e1]">{cp.camera_id}: {cp.camera_name}</div>
                      <div className="text-[10px] text-[#858585]">
                        Distance: {cp.distance_km} km • ETA Window: <span className="text-emerald-400 font-bold">{cp.eta_window}</span>
                      </div>
                    </div>
                    <span className="px-2 py-0.5 rounded bg-sky-950 text-sky-300 border border-sky-800 text-[10px] font-bold">
                      {cp.likelihood_percent}%
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Step-by-Step Chronological Timeline */}
            <div className="bg-[#141414] border border-[#262626] rounded-2xl p-4 space-y-3 text-xs">
              <span className="text-xs font-bold text-[#f5dfc0] uppercase block">
                CHRONOLOGICAL TIMELINE
              </span>

              <div className="space-y-2 text-[11px] relative pl-4 border-l-2 border-[#333]">
                {reconstructionData.observed_path.checkpoints?.map((cp, idx) => (
                  <div key={idx} className="space-y-0.5">
                    <div className="text-cyan-300 font-bold">T - {idx === 0 ? '28m' : '11m'} · Observed Sighting</div>
                    <div className="text-[#858585]">{cp.camera_name} ({cp.timestamp})</div>
                  </div>
                ))}

                <div className="space-y-0.5 pt-2">
                  <div className="text-red-400 font-bold">T = 0m · Incident Detected</div>
                  <div className="text-[#858585]">{reconstructionData.event.event_type} at {reconstructionData.event.camera_name}</div>
                </div>

                <div className="space-y-0.5 pt-2">
                  <div className="text-emerald-400 font-bold">
                    T + {reconstructionData.candidate_paths[0]?.estimated_minutes}m · Predicted Checkpoint
                  </div>
                  <div className="text-[#858585]">
                    Estimated arrival at {reconstructionData.next_checkpoints[0]?.camera_name || 'Ground Zero'}
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : analysisState === 'analyzing' ? (
          <div className="py-24 text-center space-y-4 text-xs text-[#858585]">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-[#00F2FE]" />
            <div className="text-sm font-bold text-[#f5dfc0]">{analysisStep}</div>
            <p className="text-[11px] max-w-xs mx-auto">
              Calculating multi-camera reachability graphs, street geometries, and arrival time windows.
            </p>
          </div>
        ) : analysisError ? (
          <div className="p-6 bg-red-950/30 border border-red-900 rounded-2xl text-center space-y-3">
            <AlertTriangle className="w-8 h-8 text-red-400 mx-auto" />
            <div className="text-xs font-bold text-red-200 uppercase">RECONSTRUCTION UNAVAILABLE</div>
            <p className="text-[11px] text-red-300">{analysisError}</p>
          </div>
        ) : (
          <div className="py-24 text-center space-y-3 text-xs text-[#666]">
            <Compass className="w-10 h-10 text-[#444] mx-auto" />
            <div className="text-sm font-bold text-[#858585]">EVENT RECONSTRUCTION READY</div>
            <p className="text-[11px] text-[#555] max-w-xs mx-auto">
              Select an incident from the dropdown above and click "RECONSTRUCT EVENT MOVEMENT" to model trajectory and predict next CCTV checkpoints.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
