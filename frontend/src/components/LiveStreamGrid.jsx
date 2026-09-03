import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Maximize2, Minimize2, Play, Square, Settings, Radio, Video, Camera, 
  ShieldAlert, Activity, RefreshCw, Layers, Grid, LayoutGrid, Eye, 
  Download, Zap, CheckCircle2, AlertTriangle, Search, Filter, Cpu,
  Sparkles, Flame, Shield, Compass, SlidersHorizontal, X
} from 'lucide-react';

const SOURCE_PRESETS = [
  { label: 'Mobile / Phone IP Camera', type: 'rtsp', source: 'http://10.49.119.32:8080/video', desc: 'Android IP Webcam / DroidCam MJPEG stream' },
  { label: 'Built-in / USB Webcam', type: 'webcam', source: '0', desc: 'Hardware camera node #0' },
  { label: 'Violence Altercation #1', type: 'video', source: 'samples/fight_1.mp4', desc: 'CSMT CCTV fight scenario' },
  { label: 'Violence Altercation #2', type: 'video', source: 'samples/fight_2.mp4', desc: 'Dadar Junction altercation' },
  { label: 'Fire & Smoke Detection', type: 'video', source: 'samples/fire_1.mp4', desc: 'Thermal flame & smoke outbreak' },
  { label: 'Traffic Collision #1', type: 'video', source: 'samples/accident_1.mp4', desc: 'Intersection vehicle crash' },
  { label: 'Traffic Collision #2', type: 'video', source: 'samples/accident_2.mp4', desc: 'Expressway multi-car incident' },
  { label: 'Mumbai CSMT Concourse', type: 'video', source: 'samples/mumbai_csmt_station.mp4', desc: 'Transit concourse CCTV node' },
  { label: 'Marine Drive Coastal', type: 'video', source: 'samples/mumbai_marine_drive_north.mp4', desc: 'Coastal promenade wide-angle' },
  { label: 'Bandra Sea Link Toll', type: 'video', source: 'samples/mumbai_sealink_toll.mp4', desc: 'Expressway toll plaza CCTV' },
  { label: 'Bengaluru MG Road Metro', type: 'video', source: 'samples/blr_mg_road_metro.mp4', desc: 'MG Road station entrance' },
  { label: 'RTSP IP Network Stream', type: 'rtsp', source: 'rtsp://192.168.1.100:554/stream1', desc: 'H.264 / ONVIF Network Camera' }
];


const FALLBACK_CAMERAS = [
  { id: 1, name: "CAM-01: Mumbai CSMT Concourse Altercation", source: "samples/fight_1.mp4", source_type: "video", lat: 18.9401, lon: 72.8351, is_active: true },
  { id: 2, name: "CAM-02: Bengaluru MG Road Commercial Corridor", source: "samples/fire_1.mp4", source_type: "video", lat: 12.9756, lon: 77.6067, is_active: true },
  { id: 3, name: "CAM-03: Mumbai Marine Drive Coastal Unit", source: "http://10.49.119.32:8080/video", source_type: "rtsp", lat: 18.9438, lon: 72.8233, is_active: true },
  { id: 4, name: "CAM-04: Bengaluru Trinity Circle Transit Node", source: "samples/fire_1.mp4", source_type: "video", lat: 12.9725, lon: 77.6200, is_active: true },
  { id: 5, name: "CAM-05: Bengaluru Outer Ring Road Hub", source: "samples/fight_1.mp4", source_type: "video", lat: 12.9820, lon: 77.6200, is_active: true },
  { id: 6, name: "CAM-06: Mumbai Worli Sea Face Intercept", source: "samples/fight_1.mp4", source_type: "video", lat: 18.9650, lon: 72.8180, is_active: true }
];

export default function LiveStreamGrid({
  cameras = [],
  selectedCameraId,
  onSelectCamera,
  onStartDetection,
  onStopDetection
}) {
  const activeCameraList = (cameras && cameras.length > 0) ? cameras : FALLBACK_CAMERAS;

  const [editingCamId, setEditingCamId] = useState(null);
  const [editSource, setEditSource] = useState('');
  const [editSourceType, setEditSourceType] = useState('video');
  const [selectedPreset, setSelectedPreset] = useState(null);

  const [viewMode, setViewMode] = useState('primary'); // 'primary' (1-3) | 'all' (1-6) | 'dual' (2-split) | number (focused camId)
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL'); // 'ALL' | 'ACTIVE' | 'OFFLINE'

  // Live HUD Timecode State
  const [timecode, setTimecode] = useState('');
  const [snapshotToast, setSnapshotToast] = useState(null);
  const [streamErrors, setStreamErrors] = useState({});

  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      const ms = String(Math.floor(now.getMilliseconds() / 10)).padStart(2, '0');
      setTimecode(`${h}:${m}:${s}.${ms}`);
    }, 50);
    return () => clearInterval(timer);
  }, []);

  const openConfigDrawer = (cam) => {
    setEditingCamId(cam.id);
    setEditSource(cam.source || '');
    setEditSourceType(cam.source_type || 'video');
    setSelectedPreset(null);
  };

  const handleSaveConfig = (camId) => {
    setStreamErrors(prev => ({ ...prev, [camId]: false }));
    if (onStartDetection) {
      onStartDetection(camId, editSource, editSourceType);
    }
    setEditingCamId(null);
  };

  const handleApplyPreset = (preset) => {
    setSelectedPreset(preset.label);
    setEditSourceType(preset.type);
    setEditSource(preset.source);
  };

  const handleSnapshot = (cam) => {
    try {
      const img = document.getElementById(`cam-feed-${cam.id}`);
      if (img && img.naturalWidth) {
        const canvas = document.createElement('canvas');
        canvas.width = img.naturalWidth;
        canvas.height = img.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(img, 0, 0);
        
        const dataUrl = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = `vigrah_NODE-0${cam.id}_${Date.now()}.png`;
        link.href = dataUrl;
        link.click();

        setSnapshotToast(`Snapshot captured from NODE-0${cam.id}`);
        setTimeout(() => setSnapshotToast(null), 3000);
      } else {
        setSnapshotToast(`Snapshot frame locked for NODE-0${cam.id}`);
        setTimeout(() => setSnapshotToast(null), 3000);
      }
    } catch (err) {
      console.warn('Snapshot capture handled gracefully:', err);
      setSnapshotToast(`Snapshot frame locked for NODE-0${cam.id}`);
      setTimeout(() => setSnapshotToast(null), 3000);
    }
  };

  const handleStartAll = () => {
    activeCameraList.forEach((cam) => {
      if (!cam.is_active && onStartDetection) {
        onStartDetection(cam.id, cam.source, cam.source_type);
      }
    });
  };

  const handleStopAll = () => {
    activeCameraList.forEach((cam) => {
      if (cam.is_active && onStopDetection) {
        onStopDetection(cam.id);
      }
    });
  };

  const activeCamerasCount = activeCameraList.filter(c => c && c.is_active).length;

  // Filter cameras based on search and status
  const filteredCameras = activeCameraList.filter((cam) => {
    if (!cam) return false;
    const matchSearch = !searchQuery.trim() || 
      (cam.name && cam.name.toLowerCase().includes(searchQuery.toLowerCase())) ||
      String(cam.id).includes(searchQuery) ||
      (cam.source && cam.source.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchStatus = 
      filterStatus === 'ALL' ? true :
      filterStatus === 'ACTIVE' ? cam.is_active :
      !cam.is_active;

    return matchSearch && matchStatus;
  });

  // Determine which cameras to display
  let displayCameras = [];
  if (selectedCameraId) {
    const focused = filteredCameras.find((c) => c.id === selectedCameraId) || activeCameraList.find(c => c.id === selectedCameraId);
    displayCameras = focused ? [focused] : filteredCameras.slice(0, 3);
  } else if (viewMode === 'all') {
    displayCameras = filteredCameras;
  } else if (viewMode === 'dual') {
    displayCameras = filteredCameras.slice(0, 2);
  } else if (viewMode === 'primary') {
    displayCameras = filteredCameras.length >= 3 ? filteredCameras.slice(0, 3) : filteredCameras;
  } else if (typeof viewMode === 'number') {
    const single = filteredCameras.find(c => c.id === viewMode) || activeCameraList.find(c => c.id === viewMode);
    displayCameras = single ? [single] : filteredCameras.slice(0, 3);
  } else {
    displayCameras = filteredCameras.slice(0, 3);
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-4 md:p-5 bg-[#060709] text-[#e5e2e1] gap-4 select-none">
      {/* Toast Notification */}
      <AnimatePresence>
        {snapshotToast && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-16 right-8 z-50 px-4 py-2.5 bg-[#142820] border border-[#1d4f43] text-[#9ed1c1] rounded-xl text-xs font-mono font-bold shadow-2xl flex items-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            {snapshotToast}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 1. TOP COMMAND BAR & TELEMETRY HUD */}
      <div className="flex flex-wrap items-center justify-between pb-3.5 border-b border-white/[0.08] gap-3">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-[#12131a] border border-[#f5dfc0]/30 flex items-center justify-center text-[#f5dfc0] shadow-lg">
            <Radio className="w-5 h-5 animate-pulse text-[#f5dfc0]" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h1 className="text-sm font-bold text-[#f5dfc0] uppercase tracking-wider font-mono">
                Sense Layer — Live Surveillance Matrix
              </h1>
              <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-[#1c2e26] text-[#9ed1c1] border border-[#2a4d3e] font-bold flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {activeCamerasCount} / {cameras.length} NODES LIVE
              </span>
              <span className="hidden sm:inline-flex text-[10px] font-mono px-2 py-0.5 rounded bg-[#161822] text-[#00F2FE] border border-cyan-900/50 font-bold items-center gap-1">
                <Sparkles className="w-3 h-3 text-[#00F2FE]" /> AI DETECTORS ONLINE
              </span>
            </div>
            <p className="text-[11px] text-[#858585] font-mono mt-0.5">
              Multi-threat neural stream inference: Violence, Fire Outbreak, Smoke Plumes & Traffic Accidents
            </p>
          </div>
        </div>

        {/* Global Controls & Layout Switcher */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Timecode HUD */}
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 bg-[#0e0f16] border border-white/[0.08] rounded-xl text-xs font-mono text-[#f5dfc0]">
            <Activity className="w-3.5 h-3.5 text-[#00F2FE] animate-pulse" />
            <span className="text-[#858585]">UTC/LIVE:</span>
            <span className="font-bold tracking-wider">{timecode || '00:00:00.00'}</span>
          </div>

          {/* Start/Stop All Group Action */}
          <div className="flex items-center bg-[#0e0f16] p-1 rounded-xl border border-white/[0.08] text-xs font-mono">
            <button
              onClick={handleStartAll}
              title="Start all camera feeds"
              className="px-2.5 py-1 rounded-lg text-[#9ed1c1] hover:bg-[#142820] transition flex items-center gap-1 font-bold text-[11px]"
            >
              <Play className="w-3 h-3 text-emerald-400" /> Start All
            </button>
            <span className="text-white/20 mx-0.5">|</span>
            <button
              onClick={handleStopAll}
              title="Stop all camera feeds"
              className="px-2.5 py-1 rounded-lg text-[#ffd9d7] hover:bg-[#2a1416] transition flex items-center gap-1 font-bold text-[11px]"
            >
              <Square className="w-3 h-3 text-red-400" /> Stop All
            </button>
          </div>

          {/* Layout Mode Selector */}
          <div className="flex items-center bg-[#0e0f16] p-1 rounded-xl border border-white/[0.08] text-xs font-mono">
            <button
              onClick={() => { setViewMode('primary'); onSelectCamera && onSelectCamera(null); }}
              title="Main 3-Camera Bento Matrix"
              className={`px-3 py-1 rounded-lg font-bold transition flex items-center gap-1.5 ${
                viewMode === 'primary' && !selectedCameraId
                  ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                  : 'text-[#858585] hover:text-[#e5e2e1]'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" /> 3-Matrix
            </button>
            <button
              onClick={() => { setViewMode('all'); onSelectCamera && onSelectCamera(null); }}
              title="All 6-Nodes Grid"
              className={`px-3 py-1 rounded-lg font-bold transition flex items-center gap-1.5 ${
                viewMode === 'all' && !selectedCameraId
                  ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                  : 'text-[#858585] hover:text-[#e5e2e1]'
              }`}
            >
              <Grid className="w-3.5 h-3.5" /> All ({cameras.length})
            </button>
            <button
              onClick={() => { setViewMode('dual'); onSelectCamera && onSelectCamera(null); }}
              title="Dual Split View"
              className={`px-3 py-1 rounded-lg font-bold transition flex items-center gap-1.5 ${
                viewMode === 'dual' && !selectedCameraId
                  ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                  : 'text-[#858585] hover:text-[#e5e2e1]'
              }`}
            >
              <Layers className="w-3.5 h-3.5" /> Dual
            </button>

            {selectedCameraId && (
              <button
                onClick={() => { onSelectCamera && onSelectCamera(null); setViewMode('primary'); }}
                className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#161822] hover:bg-[#202433] text-[#00F2FE] border border-cyan-900/50 text-[11px] font-bold transition ml-1"
              >
                <Minimize2 className="w-3 h-3" /> Reset Focus
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 2. CHANNELS QUICK SELECTOR & FILTER TOOLBAR */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-[#0a0b10] p-2.5 rounded-xl border border-white/[0.06] font-mono text-xs">
        {/* Quick Channel Buttons */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 max-w-full">
          <span className="text-[10px] text-[#858585] uppercase tracking-wider whitespace-nowrap pl-1">
            SECTORS:
          </span>
          {cameras.map((cam) => {
            const isCurrent = (selectedCameraId === cam.id) || (displayCameras.length === 1 && displayCameras[0]?.id === cam.id);
            return (
              <button
                key={cam.id}
                onClick={() => {
                  setViewMode(cam.id);
                  if (onSelectCamera) onSelectCamera(cam.id);
                }}
                className={`px-3 py-1.5 rounded-lg text-[11px] whitespace-nowrap transition flex items-center gap-2 border font-bold ${
                  isCurrent
                    ? 'bg-[#1e2333] text-[#f5dfc0] border-[#f5dfc0] shadow-lg shadow-cyan-950/30'
                    : cam.is_active
                    ? 'bg-[#10131a] text-[#cfc5b9] border-white/[0.08] hover:border-white/[0.2]'
                    : 'bg-[#0d0e14] text-[#858585] border-white/[0.04] hover:text-[#cfc5b9]'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${cam.is_active ? 'bg-[#00f2fe] animate-pulse shadow-[0_0_8px_#00f2fe]' : 'bg-[#444]'}`} />
                <span>CAM-0{cam.id}</span>
                <span className="text-[9px] text-[#858585] font-normal hidden sm:inline">
                  {cam.source_type === 'webcam' ? 'WEBCAM' : cam.source_type === 'rtsp' ? 'IP-CAM' : 'CCTV'}
                </span>
              </button>
            );
          })}
        </div>

        {/* Search & Status Filters */}
        <div className="flex items-center gap-2 ml-auto">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-[#858585]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter nodes..."
              className="pl-8 pr-3 py-1 bg-[#12131d] border border-white/[0.08] rounded-lg text-[11px] text-[#e5e2e1] placeholder-[#555] outline-none focus:border-[#f5dfc0] w-32 sm:w-40"
            />
          </div>

          <select
            value={filterStatus}
            onChange={(e) => setFilterStatus(e.target.value)}
            className="px-2.5 py-1 bg-[#12131d] border border-white/[0.08] rounded-lg text-[11px] text-[#cfc5b9] outline-none cursor-pointer"
          >
            <option value="ALL">All Status</option>
            <option value="ACTIVE">Active Feeds</option>
            <option value="OFFLINE">Standby Only</option>
          </select>
        </div>
      </div>

      {/* 3. SURVEILLANCE STREAMS GRID */}
      {displayCameras.length === 0 ? (
        <div className="flex flex-col items-center justify-center p-16 bg-[#0a0b10] border border-white/[0.06] rounded-2xl text-center space-y-3 font-mono">
          <Video className="w-12 h-12 text-[#444]" />
          <div className="text-sm font-bold text-[#858585]">NO MATCHING SURVEILLANCE NODES</div>
          <p className="text-xs text-[#555] max-w-sm">
            Adjust search query or status filter to reveal surveillance nodes.
          </p>
          <button
            onClick={() => { setSearchQuery(''); setFilterStatus('ALL'); setViewMode('primary'); onSelectCamera && onSelectCamera(null); }}
            className="px-4 py-2 bg-[#161822] hover:bg-[#202433] text-[#f5dfc0] rounded-xl text-xs font-bold transition"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div
          className={`grid gap-4 flex-1 ${
            displayCameras.length === 1
              ? 'grid-cols-1 max-w-5xl mx-auto w-full'
              : displayCameras.length === 2
              ? 'grid-cols-1 lg:grid-cols-2'
              : displayCameras.length <= 4
              ? 'grid-cols-1 md:grid-cols-2'
              : 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3'
          }`}
        >
          {displayCameras.map((cam) => {
            if (!cam) return null;
            const isSelected = selectedCameraId === cam.id;
            const isWebcam = cam.source_type === 'webcam' || cam.source === '0';
            const isNetwork = cam.id === 3 || cam.source_type === 'rtsp' || (cam.source && cam.source.startsWith('http'));
            const latVal = typeof cam.lat === 'number' ? cam.lat.toFixed(4) : '18.9401';
            const lonVal = typeof cam.lon === 'number' ? cam.lon.toFixed(4) : '72.8351';

            return (
              <motion.div
                key={cam.id}
                layout
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.2 }}
                className={`relative flex flex-col bg-[#0b0c12] border rounded-2xl overflow-hidden transition-all shadow-2xl group ${
                  isSelected 
                    ? 'border-[#f5dfc0] ring-1 ring-[#f5dfc0]/50' 
                    : 'border-white/[0.08] hover:border-white/[0.22]'
                }`}
              >
                {/* Camera Top HUD Header */}
                <div className="flex items-center justify-between px-3.5 py-2.5 bg-[#0f1118] border-b border-white/[0.06] select-none font-mono">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <span className="flex items-center gap-1.5 text-[10px] font-bold px-2 py-0.5 rounded bg-black/50 border border-white/[0.08]">
                      <span className={`w-2 h-2 rounded-full ${cam.is_active ? 'bg-red-500 animate-pulse shadow-[0_0_6px_#ef4444]' : 'bg-[#555]'}`} />
                      <span className={cam.is_active ? 'text-red-300 font-bold' : 'text-[#858585]'}>
                        {cam.is_active ? 'REC' : 'OFFLINE'}
                      </span>
                    </span>

                    <span className="text-xs font-bold text-[#f5dfc0] truncate" title={cam.name}>
                      NODE-0{cam.id}: {cam.name || `Camera ${cam.id}`}
                    </span>
                  </div>

                  {/* Badges & Window Controls */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {isNetwork && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#1c2e26] text-[#9ed1c1] border border-[#2a4d3e] font-bold">
                        RTSP/IP
                      </span>
                    )}
                    {isWebcam && (
                      <span className="text-[9px] px-1.5 py-0.5 rounded bg-[#f5dfc0] text-[#0A0A0A] font-black">
                        LOCAL CAM
                      </span>
                    )}

                    {/* Snapshot Button */}
                    <button
                      onClick={() => handleSnapshot(cam)}
                      title="Capture Instant High-Res Forensic Snapshot"
                      className="p-1.5 rounded-lg bg-black/40 hover:bg-[#1f2333] text-[#858585] hover:text-[#00F2FE] border border-white/[0.06] transition"
                    >
                      <Camera className="w-3.5 h-3.5" />
                    </button>

                    {/* Fullscreen / Focus Button */}
                    <button
                      onClick={() => {
                        if (selectedCameraId === cam.id) {
                          if (onSelectCamera) onSelectCamera(null);
                          setViewMode('primary');
                        } else {
                          if (onSelectCamera) onSelectCamera(cam.id);
                          setViewMode(cam.id);
                        }
                      }}
                      title={isSelected ? 'Return to Matrix View' : 'Focus Single Node Stream'}
                      className="p-1.5 rounded-lg bg-black/40 hover:bg-[#1f2333] text-[#858585] hover:text-[#f5dfc0] border border-white/[0.06] transition"
                    >
                      {isSelected ? <Minimize2 className="w-3.5 h-3.5 text-[#f5dfc0]" /> : <Maximize2 className="w-3.5 h-3.5" />}
                    </button>
                  </div>
                </div>

                {/* Camera Viewport Container */}
                <div className="relative aspect-video bg-[#050608] overflow-hidden flex items-center justify-center flex-1 min-h-[230px]">
                  {cam.is_active ? (
                    <>
                      {/* Active MJPEG Stream */}
                      <img
                        id={`cam-feed-${cam.id}`}
                        src={`/stream/${cam.id}`}
                        alt={cam.name}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          setStreamErrors(prev => ({ ...prev, [cam.id]: true }));
                        }}
                      />

                      {/* HUD Top Left Telemetry Overlay */}
                      <div className="absolute top-2.5 left-2.5 flex flex-col gap-1 pointer-events-none font-mono">
                        <div className="flex items-center gap-1.5 bg-black/80 backdrop-blur-md px-2 py-0.5 border border-white/[0.12] text-[9px] text-[#9ed1c1] rounded">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                          <span>NODE-0{cam.id} // {cam.source_type?.toUpperCase() || 'STREAM'}</span>
                        </div>
                        <div className="bg-black/80 backdrop-blur-md px-2 py-0.5 border border-white/[0.08] text-[9px] text-cyan-300 rounded font-bold">
                          AI: MULTI-THREAT DETECTOR ON
                        </div>
                      </div>

                      {/* HUD Top Right Resolution & Latency */}
                      <div className="absolute top-2.5 right-2.5 flex items-center gap-1.5 pointer-events-none font-mono">
                        <div className="bg-black/80 backdrop-blur-md px-2 py-0.5 border border-white/[0.1] text-[9px] text-[#f5dfc0] rounded font-bold">
                          1080P // 30 FPS
                        </div>
                      </div>

                      {/* HUD Bottom Cyber Scanline Effect */}
                      <div className="absolute bottom-0 inset-x-0 h-1 bg-gradient-to-r from-transparent via-[#00F2FE]/40 to-transparent pointer-events-none" />

                      {/* Real-time Timecode Watermark (Bottom Right) */}
                      <div className="absolute bottom-2 right-2.5 bg-black/85 px-2 py-0.5 rounded border border-white/[0.08] text-[9px] font-mono text-[#858585] pointer-events-none">
                        {timecode || 'LIVE'}
                      </div>
                    </>
                  ) : (
                    /* Offline Standby State with Tactical Hologram Display */
                    <div className="flex flex-col items-center justify-center p-6 text-center space-y-3 font-mono relative w-full h-full">
                      {/* Stylized background reticle grid */}
                      <div className="absolute inset-0 bg-[radial-gradient(#1f2438_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />

                      <div className="w-12 h-12 rounded-2xl bg-[#0f111a] border border-white/[0.08] flex items-center justify-center text-[#666] relative z-10 shadow-inner">
                        <Video className="w-6 h-6 text-[#858585] opacity-50" />
                      </div>

                      <div className="relative z-10">
                        <div className="text-xs font-bold text-[#e5e2e1] uppercase tracking-wider">
                          CAMERA STREAM STANDBY
                        </div>
                        <div className="text-[10px] text-[#858585] mt-0.5 truncate max-w-[260px]">
                          Source: {cam.source || 'Default Stream Pipeline'}
                        </div>
                      </div>

                      <button
                        onClick={() => onStartDetection && onStartDetection(cam.id, cam.source, cam.source_type)}
                        className="relative z-10 px-4 py-2 bg-[#142820] hover:bg-[#1d3d30] text-[#9ed1c1] border border-[#1d4f43] rounded-xl text-xs font-bold flex items-center gap-2 transition shadow-lg hover:scale-105"
                      >
                        <Play className="w-3.5 h-3.5 text-emerald-400" /> Initialize Stream Node
                      </button>
                    </div>
                  )}
                </div>

                {/* Camera Footer HUD */}
                <div className="flex items-center justify-between px-3.5 py-2.5 bg-[#0e1017] border-t border-white/[0.06] text-[10px] font-mono select-none">
                  <div className="flex items-center gap-2">
                    {cam.is_active ? (
                      <button
                        onClick={() => onStopDetection && onStopDetection(cam.id)}
                        className="px-2.5 py-1 rounded-lg bg-[#2a1416] hover:bg-[#3a1a1c] text-[#ffd9d7] border border-[#8e3335] flex items-center gap-1.5 font-bold transition shadow"
                      >
                        <Square className="w-2.5 h-2.5 text-red-400" /> Disconnect
                      </button>
                    ) : (
                      <button
                        onClick={() => onStartDetection && onStartDetection(cam.id, cam.source, cam.source_type)}
                        className="px-2.5 py-1 rounded-lg bg-[#142820] hover:bg-[#1c382c] text-[#9ed1c1] border border-[#1d4f43] flex items-center gap-1.5 font-bold transition shadow"
                      >
                        <Play className="w-2.5 h-2.5 text-emerald-400" /> Connect
                      </button>
                    )}

                    <button
                      onClick={() => openConfigDrawer(cam)}
                      className="px-2.5 py-1 rounded-lg bg-[#151722] hover:bg-[#1f2334] text-[#cfc5b9] hover:text-[#f5dfc0] border border-white/[0.08] flex items-center gap-1.5 transition"
                    >
                      <Settings className="w-2.5 h-2.5 text-[#00F2FE]" /> Source
                    </button>
                  </div>

                  <div className="flex items-center gap-3 text-[#858585]">
                    <span className="hidden sm:inline">
                      GPS: {latVal}°N, {lonVal}°E
                    </span>
                    <span className="text-[9px] px-1.5 py-0.5 rounded bg-black/40 border border-white/[0.06] text-cyan-300">
                      {cam.is_active ? 'MJPEG // 2.4Mbps' : 'STANDBY'}
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* 4. SOURCE CONFIGURATION MODAL DRAWER */}
      <AnimatePresence>
        {editingCamId !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
            onClick={() => setEditingCamId(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 15 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 15 }}
              className="w-full max-w-lg bg-[#0d0e14] border border-white/[0.12] rounded-2xl p-6 shadow-2xl text-[#e5e2e1] space-y-4 font-mono select-none"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Modal Header */}
              <div className="flex items-center justify-between border-b border-white/[0.08] pb-3.5">
                <div className="flex items-center gap-2.5">
                  <div className="p-1.5 rounded-lg bg-[#141624] border border-white/[0.08] text-[#f5dfc0]">
                    <SlidersHorizontal className="w-4 h-4 text-[#f5dfc0]" />
                  </div>
                  <div>
                    <h3 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider">
                      Configure Stream Source — NODE-0{editingCamId}
                    </h3>
                    <p className="text-[10px] text-[#858585]">
                      Select protocol preset or specify custom RTSP/video source
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setEditingCamId(null)}
                  className="p-1 rounded-lg hover:bg-white/[0.08] text-[#858585] hover:text-white transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Protocol Type Selector */}
              <div className="space-y-2">
                <label className="block text-[#858585] text-[10px] uppercase tracking-wider font-bold">
                  1. Stream Protocol Type:
                </label>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  {['video', 'webcam', 'rtsp'].map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => {
                        setEditSourceType(type);
                        if (type === 'webcam') setEditSource('0');
                      }}
                      className={`py-2 px-3 rounded-xl text-center border uppercase text-xs font-bold transition flex items-center justify-center gap-1.5 ${
                        editSourceType === type
                          ? 'bg-[#f5dfc0] text-[#0A0A0A] border-[#f5dfc0] shadow-md'
                          : 'bg-[#121420] text-[#858585] border-white/[0.08] hover:border-white/[0.2]'
                      }`}
                    >
                      {type === 'webcam' ? '🎥 Webcam' : type === 'rtsp' ? '🌐 RTSP IP' : '📁 Video File'}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quick Presets */}
              <div className="space-y-2">
                <label className="block text-[#858585] text-[10px] uppercase tracking-wider font-bold">
                  2. Ingestion Source Presets:
                </label>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 max-h-40 overflow-y-auto pr-1">
                  {SOURCE_PRESETS.map((preset) => (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => handleApplyPreset(preset)}
                      className={`p-2.5 rounded-xl border text-left text-xs transition space-y-0.5 ${
                        editSource === preset.source
                          ? 'bg-[#1a1f30] border-[#00F2FE] text-[#f5dfc0]'
                          : 'bg-[#10121b] border-white/[0.06] text-[#cfc5b9] hover:bg-[#161824]'
                      }`}
                    >
                      <div className="font-bold flex items-center justify-between">
                        <span>{preset.label}</span>
                        <span className="text-[9px] uppercase px-1.5 py-0.2 rounded bg-black/40 text-cyan-300">
                          {preset.type}
                        </span>
                      </div>
                      <div className="text-[10px] text-[#858585] truncate">{preset.desc}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Custom Source Path / URL Input */}
              <div className="space-y-1.5">
                <label className="block text-[#858585] text-[10px] uppercase tracking-wider font-bold">
                  3. Source Path or Stream URL:
                </label>
                <input
                  type="text"
                  value={editSource}
                  onChange={(e) => setEditSource(e.target.value)}
                  placeholder="e.g. http://10.49.119.32:8080/video, 0 (Webcam), or rtsp://..."
                  className="w-full px-3.5 py-2.5 bg-[#06070a] border border-white/[0.1] rounded-xl text-[#e5e2e1] text-xs font-mono focus:border-[#f5dfc0] outline-none"
                />
                <p className="text-[9px] text-[#888]">
                  💡 <strong>Phone IP Camera Tip:</strong> For Android IP Webcam, use <span className="text-cyan-300 font-bold">/video</span> (e.g. <code className="text-amber-300">http://10.49.119.32:8080/video</code>) rather than <span className="text-red-400">/videos</span>.
                </p>
              </div>

              {/* Modal Actions */}
              <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-white/[0.08]">
                <button
                  type="button"
                  onClick={() => setEditingCamId(null)}
                  className="px-4 py-2 bg-[#161822] text-[#858585] hover:text-[#e5e2e1] rounded-xl text-xs font-bold transition"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={() => handleSaveConfig(editingCamId)}
                  className="px-5 py-2 bg-[#f5dfc0] hover:bg-white text-[#0A0A0A] font-bold text-xs uppercase rounded-xl transition shadow-lg flex items-center gap-1.5"
                >
                  <Play className="w-3.5 h-3.5" /> Apply & Connect Feed
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
