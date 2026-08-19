import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Navigation, Video, Layers, Radio } from 'lucide-react';
import cityMeshData from '../data/city_mesh_data.json';

const CITY_COORDINATES = {
  Mumbai: { center: [19.0178, 72.8478], zoom: 12 },
  Bengaluru: { center: [12.9716, 77.5946], zoom: 12 }
};

// Synchronous robust parsing of city data
const PARSED_CITIES = {
  Mumbai: cityMeshData?.Mumbai?.nodes || [],
  Bengaluru: cityMeshData?.Bengaluru?.nodes || []
};

export default function CameraMap({ cameras, events, selectedCameraId, onSelectCamera, onNavigateToLive }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);

  const [selectedCity, setSelectedCity] = useState('Mumbai');
  const [cityNodes, setCityNodes] = useState(PARSED_CITIES.Mumbai);
  const [activeNode, setActiveNode] = useState(PARSED_CITIES.Mumbai[0] || null);

  // 1. City Switch Handler
  const handleCityChange = (cityName) => {
    setSelectedCity(cityName);
    const nodes = PARSED_CITIES[cityName] || [];
    setCityNodes(nodes);
    setActiveNode(nodes[0] || null);

    if (mapInstanceRef.current) {
      const cityCfg = CITY_COORDINATES[cityName] || CITY_COORDINATES.Mumbai;
      mapInstanceRef.current.flyTo(cityCfg.center, cityCfg.zoom, { duration: 1.2 });
      setTimeout(() => {
        if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
      }, 300);
    }
  };

  // 2. Initialize Leaflet Map Instance Once
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const initialCfg = CITY_COORDINATES[selectedCity] || CITY_COORDINATES.Mumbai;
      const map = L.map(mapContainerRef.current, {
        center: initialCfg.center,
        zoom: initialCfg.zoom,
        zoomControl: false,
        preferCanvas: true
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // Clean Voyager Dark Basemap Tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO &copy; OpenStreetMap',
        maxZoom: 19,
        subdomains: 'abcd'
      }).addTo(map);

      const markerLayer = L.layerGroup().addTo(map);
      layerGroupRef.current = markerLayer;
      mapInstanceRef.current = map;

      setTimeout(() => {
        map.invalidateSize();
      }, 300);
    }
  }, []);

  // 3. Render High-Visibility Glowing Map Pins
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current || cityNodes.length === 0) return;

    const layerGroup = layerGroupRef.current;
    layerGroup.clearLayers();

    cityNodes.forEach((node) => {
      const isCurrentActive = activeNode?.id === node.id;
      const markerLatLng = [node.lat, node.lon];

      const marker = L.circleMarker(markerLatLng, {
        radius: isCurrentActive ? 10 : 7,
        fillColor: isCurrentActive ? '#00F2FE' : '#FFB703',
        color: '#FFFFFF',
        weight: isCurrentActive ? 3.5 : 2,
        opacity: 1,
        fillOpacity: 0.95
      });

      marker.bindPopup(`
        <div style="font-family: monospace; font-size: 11px; padding: 6px; min-width: 180px;">
          <div style="font-weight: bold; color: #0f172a; font-size: 12px;">${node.name}</div>
          <div style="color: #64748b; margin-top: 3px;">📍 ${node.zone || 'Surveillance Node'}</div>
          <div style="color: #475569; font-size: 10px; margin-top: 2px;">LAT: ${node.lat} | LON: ${node.lon}</div>
          <div style="color: #0284c7; font-weight: 700; margin-top: 6px; font-size: 11px;">▶ CCTV Feed: ${node.video_filename || 'fight_1.mp4'}</div>
        </div>
      `);

      marker.on('click', () => {
        setActiveNode(node);
      });

      marker.addTo(layerGroup);
    });

  }, [cityNodes, activeNode]);

  const streamSrc = activeNode?.video_filename 
    ? `/stream/video/${activeNode.video_filename}` 
    : '/stream/1';

  return (
    <div className="flex flex-col lg:flex-row h-full overflow-hidden bg-[#060709] text-[#e5e2e1]">
      {/* Main Map Viewport */}
      <div className="flex-1 h-full relative overflow-hidden border-r border-white/[0.06]">
        <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: '100%' }} />
        
        {/* Floating City Switcher HUD */}
        <div className="absolute top-4 left-4 z-[400] flex flex-wrap items-center gap-3 bg-[#0d0e14]/95 border border-white/[0.1] px-4 py-2.5 backdrop-blur-md rounded-xl shadow-2xl">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-[#f5dfc0]" />
            <span className="text-xs font-bold font-mono text-[#f5dfc0] uppercase tracking-wider">
              GEOSPATIAL MESH
            </span>
          </div>

          {/* 2-City Selector */}
          <div className="flex items-center gap-2 border-l border-white/[0.08] pl-3">
            <span className="text-[11px] font-mono text-[#858585]">CITY:</span>
            <select
              value={selectedCity}
              onChange={(e) => handleCityChange(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-[#141620] border border-white/[0.15] text-xs font-mono text-[#f5dfc0] font-bold outline-none cursor-pointer hover:border-cyan-400/50 transition"
            >
              <option value="Mumbai">🔵 Mumbai ({PARSED_CITIES.Mumbai.length} Verified CCTV Nodes)</option>
              <option value="Bengaluru">🟢 Bengaluru ({PARSED_CITIES.Bengaluru.length} OpenCity Nodes)</option>
            </select>
          </div>

          <span className="text-[10px] font-mono px-2 py-0.5 bg-[#142820] text-[#9ed1c1] border border-[#1d4f43] rounded font-bold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>{cityNodes.length} PINS ACTIVE</span>
          </span>
        </div>
      </div>

      {/* Right Side Video Stream & Selected Node Inspector */}
      <div className="w-full lg:w-[380px] flex-shrink-0 bg-[#0a0b10] p-4 flex flex-col justify-between overflow-y-auto border-t lg:border-t-0 border-white/[0.06] space-y-4">
        <div className="space-y-4">
          <div className="border-b border-white/[0.06] pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider font-mono flex items-center gap-2">
                <Video className="w-3.5 h-3.5 text-[#9ed1c1]" /> Unique CCTV Node Stream
              </h3>
              <p className="text-[10px] text-[#858585] font-mono">Real-Time MJPEG Stream for Selected Intersection</p>
            </div>
            {activeNode && (
              <span className="px-2 py-0.5 rounded bg-[#f5dfc0] text-[#0A0A0A] font-mono font-black text-[10px]">
                {activeNode.id}
              </span>
            )}
          </div>

          {/* Selected Node Unique Video Player */}
          {activeNode ? (
            <div className="bg-[#0e0f17] border border-white/[0.08] rounded-xl p-3 space-y-3 shadow-xl">
              <div>
                <span className="text-[10px] font-mono text-[#858585] uppercase">Selected Intersection</span>
                <div className="text-sm font-bold text-[#f5dfc0] mt-0.5">
                  {activeNode.name}
                </div>
                <span className="text-[10px] font-mono text-[#00F2FE] block mt-0.5">
                  🎥 CCTV Feed: {activeNode.video_filename || 'fight_1.mp4'}
                </span>
              </div>

              {/* Robust MJPEG Live Stream Player */}
              <div className="relative aspect-video bg-black rounded-lg border border-white/[0.08] overflow-hidden flex items-center justify-center">
                <img
                  key={streamSrc}
                  src={streamSrc}
                  alt={activeNode.name}
                  className="w-full h-full object-cover"
                />
                <div className="absolute top-2 left-2 flex items-center gap-1.5 bg-black/80 px-2 py-0.5 rounded border border-white/[0.1] text-[9px] font-mono text-[#00F2FE]">
                  <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                  <span>LIVE CCTV STREAM</span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="p-2 bg-[#06070a] border border-white/[0.06] rounded">
                  <span className="text-[#858585] text-[9px] block">LATITUDE</span>
                  <span className="text-[#cfc5b9] font-bold">{activeNode.lat}°N</span>
                </div>
                <div className="p-2 bg-[#06070a] border border-white/[0.06] rounded">
                  <span className="text-[#858585] text-[9px] block">LONGITUDE</span>
                  <span className="text-[#cfc5b9] font-bold">{activeNode.lon}°E</span>
                </div>
              </div>

              <div className="p-2 bg-[#06070a] border border-white/[0.06] rounded text-[11px] font-mono flex items-center justify-between">
                <span className="text-[#858585]">STREAM STATUS</span>
                <span className="text-[#9ed1c1] font-bold uppercase">● ONLINE // 1080P</span>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs font-mono text-[#858585] bg-[#0e0f17] rounded-xl border border-white/[0.06]">
              Click any pin on the map to stream its unique CCTV footage.
            </div>
          )}

          {/* Node Quick Selector List */}
          <div className="space-y-1.5">
            <span className="text-[10px] font-mono text-[#858585] uppercase">
              {selectedCity} CCTV Grid Nodes ({cityNodes.length})
            </span>
            <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
              {cityNodes.slice(0, 40).map((node) => (
                <button
                  key={node.id}
                  onClick={() => setActiveNode(node)}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs font-mono flex items-center justify-between border transition ${
                    activeNode?.id === node.id
                      ? 'bg-[#181a24] text-[#f5dfc0] border-[#f5dfc0]'
                      : 'bg-[#0d0e14] text-[#cfc5b9] border-white/[0.06] hover:bg-[#141620]'
                  }`}
                >
                  <span className="truncate max-w-[220px]">{node.name}</span>
                  <span className="text-[10px] text-[#00F2FE] font-bold">▶ STREAM</span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-3 border-t border-white/[0.06]">
          <button
            onClick={() => onNavigateToLive(1)}
            className="w-full py-2.5 bg-[#f5dfc0] hover:bg-[#d8c3a5] text-[#0A0A0A] font-bold text-xs font-mono uppercase tracking-wider rounded-lg transition shadow"
          >
            Switch to Live Grid View →
          </button>
        </div>
      </div>
    </div>
  );
}
