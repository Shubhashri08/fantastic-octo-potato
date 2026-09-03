import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { 
  Navigation, Video, Layers, Radio, Camera, Eye, Play, Square, 
  RefreshCw, Search, CheckCircle2, ShieldAlert, Sparkles, Maximize2, 
  Minimize2, Download, MapPin, Globe, Film
} from 'lucide-react';
import cityMeshData from '../data/city_mesh_data.json';

// Fix default Leaflet icon paths in bundlers
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png'
});

const CITY_COORDINATES = {
  Mumbai: { center: [19.0178, 72.8478], zoom: 12 },
  Bengaluru: { center: [12.9716, 77.5946], zoom: 12 }
};

// Synchronous robust parsing of city data
const PARSED_CITIES = {
  Mumbai: cityMeshData?.Mumbai?.nodes || [],
  Bengaluru: cityMeshData?.Bengaluru?.nodes || []
};

const BASEMAP_STYLES = {
  voyager: {
    id: 'voyager',
    name: 'CARTO VOYAGER',
    url: (key) => key 
      ? `https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png?key=${key}`
      : 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png'
  },
  dark: {
    id: 'dark',
    name: 'CARTO DARK CYBER',
    url: (key) => key 
      ? `https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png?key=${key}`
      : 'https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png'
  },
  positron: {
    id: 'positron',
    name: 'CARTO POSITRON',
    url: (key) => key 
      ? `https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png?key=${key}`
      : 'https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png'
  }
};

export default function CameraMap({ cameras, events, selectedCameraId, onSelectCamera, onNavigateToLive }) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const layerGroupRef = useRef(null);
  const tileLayerRef = useRef(null);
  const videoElementRef = useRef(null);

  const [selectedCity, setSelectedCity] = useState('Mumbai');
  const [cityNodes, setCityNodes] = useState(PARSED_CITIES.Mumbai);
  const [activeNode, setActiveNode] = useState(PARSED_CITIES.Mumbai[0] || null);
  const [basemapStyle, setBasemapStyle] = useState('voyager');

  // Video & Search Controls
  const [playbackMode, setPlaybackMode] = useState('stream'); // 'stream' (MJPEG) | 'video' (Direct MP4)
  const [streamError, setStreamError] = useState(false);
  const [nodeSearch, setNodeSearch] = useState('');
  const [snapshotToast, setSnapshotToast] = useState(null);

  // 1. City Switch Handler
  const handleCityChange = (cityName) => {
    setSelectedCity(cityName);
    const nodes = PARSED_CITIES[cityName] || [];
    setCityNodes(nodes);
    setActiveNode(nodes[0] || null);
    setStreamError(false);

    if (mapInstanceRef.current) {
      const cityCfg = CITY_COORDINATES[cityName] || CITY_COORDINATES.Mumbai;
      mapInstanceRef.current.flyTo(cityCfg.center, cityCfg.zoom, { duration: 1.2 });
      setTimeout(() => {
        if (mapInstanceRef.current) mapInstanceRef.current.invalidateSize();
      }, 300);
    }
  };

  // 2. Initialize Leaflet Map Instance
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapContainerRef.current._leaflet_id && !mapInstanceRef.current) {
      mapContainerRef.current._leaflet_id = null;
    }

    if (!mapInstanceRef.current) {
      const initialCfg = CITY_COORDINATES[selectedCity] || CITY_COORDINATES.Mumbai;
      const map = L.map(mapContainerRef.current, {
        center: initialCfg.center,
        zoom: initialCfg.zoom,
        zoomControl: false,
        preferCanvas: true
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // CARTO Basemap (with API key support)
      const cartoApiKey = (import.meta.env.VITE_CARTO_API_KEY || import.meta.env.VITE_MAP_API_KEY || 'cb1_2pk7_1_90609325753bc4f1255b1901').trim();
      const styleCfg = BASEMAP_STYLES[basemapStyle] || BASEMAP_STYLES.voyager;
      const cartoUrl = styleCfg.url(cartoApiKey);

      const tileLayer = L.tileLayer(cartoUrl, {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19,
        subdomains: 'abcd'
      });

      tileLayer.on('tileerror', (error, tile) => {
        if (tile) {
          tile.src = 'https://tile.openstreetmap.org/0/0/0.png';
        }
      });

      tileLayer.addTo(map);
      tileLayerRef.current = tileLayer;

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
        tileLayerRef.current = null;
      }
      if (mapContainerRef.current) {
        mapContainerRef.current._leaflet_id = null;
      }
    };
  }, []);

  // Update Basemap tile layer when style changes
  useEffect(() => {
    if (!mapInstanceRef.current) return;
    const cartoApiKey = (import.meta.env.VITE_CARTO_API_KEY || import.meta.env.VITE_MAP_API_KEY || 'cb1_2pk7_1_90609325753bc4f1255b1901').trim();
    const styleCfg = BASEMAP_STYLES[basemapStyle] || BASEMAP_STYLES.voyager;
    const cartoUrl = styleCfg.url(cartoApiKey);

    if (tileLayerRef.current && mapInstanceRef.current.hasLayer(tileLayerRef.current)) {
      mapInstanceRef.current.removeLayer(tileLayerRef.current);
    }

    const newTileLayer = L.tileLayer(cartoUrl, {
      attribution: '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
      maxZoom: 19,
      subdomains: 'abcd'
    });

    newTileLayer.on('tileerror', (error, tile) => {
      if (tile) {
        tile.src = 'https://tile.openstreetmap.org/0/0/0.png';
      }
    });

    newTileLayer.addTo(mapInstanceRef.current);
    newTileLayer.bringToBack();
    tileLayerRef.current = newTileLayer;
  }, [basemapStyle]);

  // 3. Render High-Visibility Glowing Map Pins
  useEffect(() => {
    if (!mapInstanceRef.current || !layerGroupRef.current || cityNodes.length === 0) return;

    const layerGroup = layerGroupRef.current;
    layerGroup.clearLayers();

    cityNodes.forEach((node) => {
      if (!node || typeof node.lat !== 'number' || typeof node.lon !== 'number') return;
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
        <div style="font-family: monospace; font-size: 11px; padding: 6px; min-width: 190px;">
          <div style="font-weight: bold; color: #0f172a; font-size: 12px;">${node.name || 'Intersection'}</div>
          <div style="color: #64748b; margin-top: 3px;">📍 ${node.zone || 'Surveillance Node'}</div>
          <div style="color: #475569; font-size: 10px; margin-top: 2px;">LAT: ${node.lat} | LON: ${node.lon}</div>
          <div style="color: #0284c7; font-weight: 700; margin-top: 6px; font-size: 11px;">🎥 CCTV Feed: ${node.video_filename || 'fight_1.mp4'}</div>
        </div>
      `);

      marker.on('click', () => {
        setActiveNode(node);
        setStreamError(false);
      });

      marker.addTo(layerGroup);
    });

  }, [cityNodes, activeNode]);

  // Handle Snapshot Capture
  const handleSnapshotCapture = () => {
    try {
      if (playbackMode === 'video' && videoElementRef.current) {
        const video = videoElementRef.current;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth || 1280;
        canvas.height = video.videoHeight || 720;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        const link = document.createElement('a');
        link.download = `cctv_${activeNode?.id || 'node'}_${Date.now()}.png`;
        link.href = canvas.toDataURL('image/png');
        link.click();
      } else {
        const img = document.getElementById('map-cctv-stream-img');
        if (img && img.naturalWidth) {
          const canvas = document.createElement('canvas');
          canvas.width = img.naturalWidth;
          canvas.height = img.naturalHeight;
          const ctx = canvas.getContext('2d');
          ctx.drawImage(img, 0, 0);
          const link = document.createElement('a');
          link.download = `cctv_${activeNode?.id || 'node'}_${Date.now()}.png`;
          link.href = canvas.toDataURL('image/png');
          link.click();
        }
      }
      setSnapshotToast(`Snapshot captured for ${activeNode?.name || 'CCTV Node'}`);
      setTimeout(() => setSnapshotToast(null), 3000);
    } catch (err) {
      console.warn('Snapshot error:', err);
      setSnapshotToast(`Snapshot frame locked for ${activeNode?.id}`);
      setTimeout(() => setSnapshotToast(null), 3000);
    }
  };

  // Filtered CCTV nodes for search
  const filteredCityNodes = cityNodes.filter((node) => {
    if (!nodeSearch.trim()) return true;
    const q = nodeSearch.toLowerCase();
    return (
      (node.name && node.name.toLowerCase().includes(q)) ||
      (node.id && node.id.toLowerCase().includes(q)) ||
      (node.zone && node.zone.toLowerCase().includes(q)) ||
      (node.video_filename && node.video_filename.toLowerCase().includes(q))
    );
  });

  const mjpegStreamSrc = activeNode?.video_filename 
    ? `/stream/video/${activeNode.video_filename}` 
    : '/stream/1';

  const directVideoSrc = activeNode?.video_filename
    ? `/samples/${activeNode.video_filename}`
    : '/samples/fight_1.mp4';

  return (
    <div className="flex flex-col lg:flex-row h-full overflow-hidden bg-[#060709] text-[#e5e2e1] select-none font-mono">
      {/* Toast Notification */}
      {snapshotToast && (
        <div className="fixed top-16 right-8 z-50 px-4 py-2.5 bg-[#142820] border border-[#1d4f43] text-[#9ed1c1] rounded-xl text-xs font-mono font-bold shadow-2xl flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          {snapshotToast}
        </div>
      )}

      {/* Main Map Viewport */}
      <div className="flex-1 h-full relative overflow-hidden border-r border-white/[0.06]">
        <div ref={mapContainerRef} className="w-full h-full" style={{ minHeight: '100%' }} />
        
        {/* Floating Top Left Control HUD (City Selector & CARTO Dark Cyber Layer) */}
        <div className="absolute top-4 left-4 z-[400] flex flex-wrap items-center gap-3 bg-[#0d0e14]/95 border border-white/[0.1] px-4 py-2.5 backdrop-blur-md rounded-xl shadow-2xl">
          <div className="flex items-center gap-2">
            <Navigation className="w-4 h-4 text-[#f5dfc0]" />
            <span className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider">
              GEOSPATIAL MESH
            </span>
          </div>

          {/* 2-City Selector */}
          <div className="flex items-center gap-2 border-l border-white/[0.08] pl-3">
            <span className="text-[11px] text-[#858585]">CITY:</span>
            <select
              value={selectedCity}
              onChange={(e) => handleCityChange(e.target.value)}
              className="px-3 py-1.5 rounded-lg bg-[#141620] border border-white/[0.15] text-xs text-[#f5dfc0] font-bold outline-none cursor-pointer hover:border-cyan-400/50 transition"
            >
              <option value="Mumbai">Mumbai ({PARSED_CITIES.Mumbai.length} Verified CCTV Nodes)</option>
              <option value="Bengaluru">Bengaluru ({PARSED_CITIES.Bengaluru.length} OpenCity Nodes)</option>
            </select>
          </div>

          {/* Basemap Style Selector */}
          <div className="flex items-center gap-2 border-l border-white/[0.08] pl-3">
            <Globe className="w-3.5 h-3.5 text-cyan-400" />
            <select
              value={basemapStyle}
              onChange={(e) => setBasemapStyle(e.target.value)}
              className="px-2.5 py-1.5 rounded-lg bg-[#141624] border border-cyan-900/50 text-[11px] text-[#00F2FE] font-bold outline-none cursor-pointer hover:border-cyan-400 transition"
            >
              <option value="voyager">CARTO VOYAGER (DAY)</option>
              <option value="dark">CARTO DARK CYBER</option>
              <option value="positron">CARTO POSITRON</option>
            </select>
          </div>

          <span className="text-[10px] px-2 py-0.5 bg-[#142820] text-[#9ed1c1] border border-[#1d4f43] rounded font-bold flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>{cityNodes.length} PINS ACTIVE</span>
          </span>
        </div>

        {/* Map Bottom Legend */}
        <div className="absolute bottom-4 left-4 z-[400] bg-black/85 border border-white/[0.08] px-3 py-1.5 rounded-xl text-[10px] text-[#a3a3a3] backdrop-blur-md flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00F2FE]" />
            <span>Selected Node</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FFB703]" />
            <span>Active CCTV Node</span>
          </div>
          <span className="text-[9px] text-[#666]">CARTO Basemap Layer</span>
        </div>
      </div>

      {/* Right Side CCTV Video Stream & Selected Node Inspector */}
      <div className="w-full lg:w-[420px] flex-shrink-0 bg-[#0a0b10] p-4 flex flex-col justify-between overflow-y-auto border-t lg:border-t-0 border-white/[0.06] space-y-4">
        <div className="space-y-4">
          {/* Header & Mode Switcher */}
          <div className="border-b border-white/[0.06] pb-3 flex items-center justify-between">
            <div>
              <h3 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider flex items-center gap-2">
                <Video className="w-3.5 h-3.5 text-[#9ed1c1]" /> CCTV Footage Inspector
              </h3>
              <p className="text-[10px] text-[#858585]">Municipal Surveillance Feed for Selected Node</p>
            </div>
            {activeNode && (
              <span className="px-2 py-0.5 rounded bg-[#f5dfc0] text-[#0A0A0A] font-black text-[10px]">
                {activeNode.id}
              </span>
            )}
          </div>

          {/* CCTV Footage Player Card */}
          {activeNode ? (
            <div className="bg-[#0e0f17] border border-white/[0.08] rounded-xl p-3 space-y-3 shadow-2xl">
              <div className="flex items-center justify-between">
                <div className="min-w-0 pr-2">
                  <span className="text-[10px] text-[#858585] uppercase">Selected Intersection</span>
                  <div className="text-xs font-bold text-[#f5dfc0] truncate mt-0.5" title={activeNode.name}>
                    {activeNode.name}
                  </div>
                  <span className="text-[10px] text-[#00F2FE] block mt-0.5 truncate">
                    File: {activeNode.video_filename || 'fight_1.mp4'} • {activeNode.zone || 'Surveillance Sector'}
                  </span>
                </div>

                {/* Player Mode Switcher */}
                <div className="flex items-center bg-[#06070a] p-0.5 rounded-lg border border-white/[0.08] text-[10px] flex-shrink-0">
                  <button
                    onClick={() => { setPlaybackMode('stream'); setStreamError(false); }}
                    className={`px-2 py-1 rounded font-bold transition flex items-center gap-1 ${
                      playbackMode === 'stream' && !streamError
                        ? 'bg-[#1c2e26] text-[#9ed1c1] border border-[#2a4d3e]'
                        : 'text-[#858585] hover:text-[#e5e2e1]'
                    }`}
                  >
                    <Radio className="w-2.5 h-2.5" /> Live MJPEG
                  </button>
                  <button
                    onClick={() => setPlaybackMode('video')}
                    className={`px-2 py-1 rounded font-bold transition flex items-center gap-1 ${
                      playbackMode === 'video' || streamError
                        ? 'bg-[#f5dfc0] text-[#0A0A0A]'
                        : 'text-[#858585] hover:text-[#e5e2e1]'
                    }`}
                  >
                    <Film className="w-2.5 h-2.5" /> HD Video
                  </button>
                </div>
              </div>

              {/* Robust CCTV Video Viewport */}
              <div className="relative aspect-video bg-black rounded-lg border border-white/[0.08] overflow-hidden flex items-center justify-center group">
                {playbackMode === 'stream' && !streamError ? (
                  <>
                    <img
                      id="map-cctv-stream-img"
                      key={mjpegStreamSrc}
                      src={mjpegStreamSrc}
                      alt={activeNode.name}
                      className="w-full h-full object-cover"
                      onError={() => {
                        console.warn('MJPEG stream unavailable, switching to direct video mode');
                        setStreamError(true);
                        setPlaybackMode('video');
                      }}
                    />
                    <div className="absolute top-2 left-2 flex items-center gap-1.5 bg-black/80 px-2 py-0.5 rounded border border-white/[0.1] text-[9px] text-[#00F2FE]">
                      <span className="h-1.5 w-1.5 rounded-full bg-cyan-400 animate-pulse"></span>
                      <span>LIVE MJPEG STREAM</span>
                    </div>
                  </>
                ) : (
                  <>
                    <video
                      ref={videoElementRef}
                      key={directVideoSrc}
                      src={directVideoSrc}
                      autoPlay
                      loop
                      muted
                      playsInline
                      controls
                      className="w-full h-full object-cover"
                    />
                    <div className="absolute top-2 left-2 flex items-center gap-1.5 bg-black/80 px-2 py-0.5 rounded border border-white/[0.1] text-[9px] text-[#9ed1c1] pointer-events-none">
                      <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
                      <span>HD CCTV FOOTAGE PLAYBACK</span>
                    </div>
                  </>
                )}

                {/* Top Right Snapshot Overlay Button */}
                <button
                  onClick={handleSnapshotCapture}
                  title="Capture Forensic Snapshot"
                  className="absolute top-2 right-2 p-1.5 bg-black/70 hover:bg-[#1a1f30] text-[#cfc5b9] hover:text-[#f5dfc0] border border-white/[0.1] rounded-lg text-xs opacity-80 hover:opacity-100 transition z-20"
                >
                  <Camera className="w-3.5 h-3.5" />
                </button>
              </div>

              {/* Node Telemetry Details */}
              <div className="grid grid-cols-2 gap-2 text-[11px]">
                <div className="p-2 bg-[#06070a] border border-white/[0.06] rounded">
                  <span className="text-[#858585] text-[9px] block">LATITUDE</span>
                  <span className="text-[#cfc5b9] font-bold">{(activeNode.lat ?? 0).toFixed(4)}°N</span>
                </div>
                <div className="p-2 bg-[#06070a] border border-white/[0.06] rounded">
                  <span className="text-[#858585] text-[9px] block">LONGITUDE</span>
                  <span className="text-[#cfc5b9] font-bold">{(activeNode.lon ?? 0).toFixed(4)}°E</span>
                </div>
              </div>

              <div className="p-2 bg-[#06070a] border border-white/[0.06] rounded text-[11px] flex items-center justify-between">
                <span className="text-[#858585]">STREAM PROTOCOL</span>
                <span className="text-[#9ed1c1] font-bold uppercase">
                  ● ONLINE // 1080P // {playbackMode === 'stream' ? 'MJPEG' : 'MP4 DIRECT'}
                </span>
              </div>
            </div>
          ) : (
            <div className="p-8 text-center text-xs text-[#858585] bg-[#0e0f17] rounded-xl border border-white/[0.06]">
              Click any pin on the map to stream its unique CCTV footage.
            </div>
          )}

          {/* Node Search & Quick Selector List */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-[10px] text-[#858585] uppercase">
                {selectedCity} CCTV Grid Nodes ({filteredCityNodes.length})
              </span>
              <span className="text-[9px] text-cyan-300">Click to Play Feed</span>
            </div>

            {/* Search Box */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#858585]" />
              <input
                type="text"
                value={nodeSearch}
                onChange={(e) => setNodeSearch(e.target.value)}
                placeholder="Search CCTV node, intersection, or file..."
                className="w-full pl-8 pr-3 py-1.5 bg-[#0e0f16] border border-white/[0.08] rounded-lg text-xs text-[#e5e2e1] placeholder-[#555] outline-none focus:border-[#f5dfc0]"
              />
            </div>

            {/* Nodes List */}
            <div className="space-y-1 max-h-44 overflow-y-auto pr-1">
              {filteredCityNodes.slice(0, 50).map((node) => (
                <button
                  key={node.id}
                  onClick={() => {
                    setActiveNode(node);
                    setStreamError(false);
                  }}
                  className={`w-full text-left px-2.5 py-1.5 rounded-lg text-xs flex items-center justify-between border transition ${
                    activeNode?.id === node.id
                      ? 'bg-[#181a24] text-[#f5dfc0] border-[#f5dfc0]'
                      : 'bg-[#0d0e14] text-[#cfc5b9] border-white/[0.06] hover:bg-[#141620]'
                  }`}
                >
                  <div className="min-w-0 pr-2">
                    <span className="font-bold block truncate">{node.name}</span>
                    <span className="text-[9px] text-[#858585] block truncate">{node.zone}</span>
                  </div>
                  <span className="text-[10px] text-[#00F2FE] font-bold flex-shrink-0">
                    ▶ PLAY
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Action Button */}
        <div className="pt-3 border-t border-white/[0.06]">
          <button
            onClick={() => onNavigateToLive && onNavigateToLive(1)}
            className="w-full py-2.5 bg-[#f5dfc0] hover:bg-[#d8c3a5] text-[#0A0A0A] font-bold text-xs uppercase tracking-wider rounded-lg transition shadow"
          >
            Switch to Live Grid View →
          </button>
        </div>
      </div>
    </div>
  );
}
