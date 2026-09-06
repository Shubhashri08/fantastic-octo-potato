import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Maximize2, Minimize2, Play, Square, Settings, Video, Camera, 
  Grid, LayoutGrid, Layers, CheckCircle2, Search, Sparkles, X
} from 'lucide-react';

const SOURCE_PRESETS = [
  { label: 'Corridor Physical Altercation #1', type: 'video', source: 'samples/fight_1.mp4', desc: 'Corridor altercation incident' },
  { label: 'Concourse Conflict Altercation #2', type: 'video', source: 'samples/fight_2.mp4', desc: 'Concourse physical confrontation' },
  { label: 'Corridor Defense Incident #3', type: 'video', source: 'samples/fight_3.mp4', desc: 'Active corridor fight scene' },
  { label: 'Corridor Fight Footage #4', type: 'video', source: 'samples/fight_4.mp4', desc: 'Corridor altercation incident' },
  { label: 'Daylight Intersection Broadside', type: 'video', source: 'samples/accident_cut_01_daylight_intersection.mp4', desc: 'Real intersection car crash' },
  { label: 'Night Junction T-Bone Collision', type: 'video', source: 'samples/accident_cut_02_night_junction_tbone.mp4', desc: 'Real night junction T-bone collision' },
  { label: 'Sidewalk Truck Swerve', type: 'video', source: 'samples/accident_cut_03_truck_swerve_sidewalk.mp4', desc: 'Truck swerves onto pedestrian sidewalk' },
  { label: 'Highway Night Rear-End', type: 'video', source: 'samples/accident_cut_04_highway_night_rear_end.mp4', desc: 'High-speed arterial rear-end spinout' },
  { label: 'Fire & Smoke Detection', type: 'video', source: 'samples/fire_1.mp4', desc: 'Roadway transformer fire & smoke' },
  { label: 'Pedestrian Concourse', type: 'video', source: 'samples/mall_walking.mp4', desc: 'Pedestrian concourse flow' },
  { label: 'Hardware USB Webcam', type: 'webcam', source: '0', desc: 'Hardware camera node #0' }
];

const FALLBACK_CAMERAS = [
  { id: 1, name: "CAM-01: Central Concourse // Corridor Altercation", source: "samples/fight_1.mp4", source_type: "video", lat: 18.9401, lon: 72.8351, is_active: true },
  { id: 2, name: "CAM-02: Bengaluru MG Road Commercial Corridor", source: "samples/accident_cut_01_daylight_intersection.mp4", source_type: "video", lat: 12.9756, lon: 77.6067, is_active: true },
  { id: 3, name: "CAM-03: Innovation Lab // Workspace Terminal", source: "samples/IMG_0006.mp4", source_type: "video", lat: 18.9438, lon: 72.8233, is_active: true },
  { id: 4, name: "CAM-04: Bengaluru Trinity Circle Transit Node", source: "samples/accident_cut_04_highway_night_rear_end.mp4", source_type: "video", lat: 12.9725, lon: 77.6200, is_active: true },
  { id: 5, name: "CAM-05: Bengaluru Outer Ring Road Hub", source: "samples/accident_cut_03_truck_swerve_sidewalk.mp4", source_type: "video", lat: 12.9820, lon: 77.6200, is_active: true },
  { id: 6, name: "CAM-06: Mumbai Worli Sea Face Intercept", source: "samples/accident_cut_02_night_junction_tbone.mp4", source_type: "video", lat: 18.9650, lon: 72.8180, is_active: true }
];

function LiveTimecode() {
  const [timecode, setTimecode] = useState('');
  useEffect(() => {
    const timer = setInterval(() => {
      const now = new Date();
      const h = String(now.getHours()).padStart(2, '0');
      const m = String(now.getMinutes()).padStart(2, '0');
      const s = String(now.getSeconds()).padStart(2, '0');
      const ms = String(Math.floor(now.getMilliseconds() / 10)).padStart(2, '0');
      setTimecode(`${h}:${m}:${s}.${ms}`);
    }, 60);
    return () => clearInterval(timer);
  }, []);
  return <span>{timecode || 'LIVE'}</span>;
}

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

  const [viewMode, setViewMode] = useState('primary');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('ALL');

  const [snapshotToast, setSnapshotToast] = useState(null);
  const [, setStreamErrors] = useState({});

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

        setSnapshotToast(`Forensic snapshot captured: NODE-0${cam.id}`);
        setTimeout(() => setSnapshotToast(null), 3000);
      } else {
        setSnapshotToast(`Snapshot locked for NODE-0${cam.id}`);
        setTimeout(() => setSnapshotToast(null), 3000);
      }
    } catch {
      setSnapshotToast(`Snapshot locked for NODE-0${cam.id}`);
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

  let displayCameras = [];
  if (selectedCameraId) {
    const focused = filteredCameras.find((c) => c.id === selectedCameraId) || activeCameraList.find(c => c.id === selectedCameraId);
    displayCameras = focused ? [focused] : filteredCameras.slice(0, 4);
  } else if (viewMode === 'all') {
    displayCameras = filteredCameras;
  } else if (viewMode === 'dual') {
    displayCameras = filteredCameras.slice(0, 2);
  } else if (viewMode === 'primary') {
    displayCameras = filteredCameras.length >= 4 ? filteredCameras.slice(0, 4) : filteredCameras;
  } else if (typeof viewMode === 'number') {
    const single = filteredCameras.find(c => c.id === viewMode) || activeCameraList.find(c => c.id === viewMode);
    displayCameras = single ? [single] : filteredCameras.slice(0, 4);
  } else {
    displayCameras = filteredCameras.slice(0, 4);
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-3.5 md:p-4 bg-[#0A0A0A] text-[#e5e2e1] gap-3 select-none">
      {/* Toast Notification */}
      <AnimatePresence>
        {snapshotToast && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="fixed top-14 right-6 z-50 px-3.5 py-2 bg-[#121212] border border-[#2A2A2A] text-[#9ed1c1] rounded-lg text-xs font-mono font-bold shadow-2xl flex items-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4 text-[#9ed1c1]" />
            {snapshotToast}
          </motion.div>
        )}
      </AnimatePresence>

      {/* 1. SLIM TACTICAL COMMAND & CONTROL BAR */}
      <div className="flex flex-wrap items-center justify-between gap-2.5 px-3 py-2 bg-[#111111] border border-[#222222] rounded-xl text-xs font-mono">
        {/* Left Status & Sector Pills */}
        <div className="flex items-center gap-2 overflow-x-auto max-w-full">
          <div className="flex items-center gap-1.5 px-2.5 py-1 bg-[#161616] rounded-md border border-[#262626]">
            <span className="w-2 h-2 rounded-full bg-[#9ed1c1] animate-pulse" />
            <span className="text-[11px] font-bold text-[#9ed1c1]">{activeCamerasCount}/{activeCameraList.length} LIVE</span>
          </div>

          <div className="h-4 w-px bg-white/10 mx-1 hidden sm:block" />

          {/* Quick Node Selector Pills */}
          <div className="flex items-center gap-1.5">
            {activeCameraList.map((cam) => {
              const isCurrent = (selectedCameraId === cam.id) || (displayCameras.length === 1 && displayCameras[0]?.id === cam.id);
              return (
                <button
                  key={cam.id}
                  onClick={() => {
                    setViewMode(cam.id);
                    if (onSelectCamera) onSelectCamera(cam.id);
                  }}
                  className={`px-2.5 py-1 rounded-md text-[10px] font-bold transition flex items-center gap-1.5 border ${
                    isCurrent
                      ? 'bg-[#222222] text-[#f5dfc0] border-[#f5dfc0]/70 shadow-sm'
                      : cam.is_active
                      ? 'bg-[#161616] text-[#cfc5b9] border-[#262626] hover:border-[#383838]'
                      : 'bg-[#121212] text-[#666666] border-[#1C1C1C]'
                  }`}
                >
                  <span className={`w-1.5 h-1.5 rounded-full ${cam.is_active ? 'bg-[#9ed1c1]' : 'bg-[#444]'}`} />
                  CAM-0{cam.id}
                </button>
              );
            })}
          </div>
        </div>

        {/* Center/Right Controls */}
        <div className="flex items-center gap-2 ml-auto">
          {/* Quick Node Search */}
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2 top-1/2 -translate-y-1/2 text-[#666666]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search..."
              className="pl-7 pr-2.5 py-1 bg-[#141414] border border-[#262626] rounded-md text-[11px] text-[#e5e2e1] placeholder-[#555555] outline-none focus:border-[#9ed1c1] w-28 sm:w-36 transition-colors"
            />
          </div>

            {/* Layout Mode Selector */}
            <div className="flex items-center bg-[#141414] p-0.5 rounded-md border border-[#242424]">
              <button
                onClick={() => { setViewMode('primary'); onSelectCamera && onSelectCamera(null); }}
                title="4-Grid Matrix"
                className={`px-2 py-1 rounded text-[11px] font-bold transition flex items-center gap-1 ${
                  viewMode === 'primary' && !selectedCameraId
                    ? 'bg-[#242424] text-[#f5dfc0]'
                    : 'text-[#858585] hover:text-[#e5e2e1]'
                }`}
              >
                <LayoutGrid className="w-3 h-3" /> 4-Grid
              </button>
              <button
                onClick={() => { setViewMode('all'); onSelectCamera && onSelectCamera(null); }}
                title="All Feeds"
                className={`px-2 py-1 rounded text-[11px] font-bold transition flex items-center gap-1 ${
                  viewMode === 'all' && !selectedCameraId
                    ? 'bg-[#242424] text-[#f5dfc0]'
                    : 'text-[#858585] hover:text-[#e5e2e1]'
                }`}
              >
                <Grid className="w-3 h-3" /> All ({activeCameraList.length})
              </button>
              <button
                onClick={() => { setViewMode('dual'); onSelectCamera && onSelectCamera(null); }}
                title="Dual Split"
                className={`px-2 py-1 rounded text-[11px] font-bold transition flex items-center gap-1 ${
                  viewMode === 'dual' && !selectedCameraId
                    ? 'bg-[#242424] text-[#f5dfc0]'
                    : 'text-[#858585] hover:text-[#e5e2e1]'
                }`}
              >
                <Layers className="w-3 h-3" /> Dual
              </button>
            </div>

            {/* Start/Stop All Buttons */}
            <div className="flex items-center bg-[#141414] p-0.5 rounded-md border border-[#242424]">
              <button
                onClick={handleStartAll}
                title="Start all camera feeds"
                className="px-2 py-1 rounded text-[#9ed1c1] hover:bg-[#1E1E1E] transition flex items-center gap-1 font-bold text-[10px]"
              >
                <Play className="w-2.5 h-2.5 text-[#9ed1c1]" /> Start
              </button>
              <button
                onClick={handleStopAll}
                title="Stop all camera feeds"
                className="px-2 py-1 rounded text-[#ffd9d7] hover:bg-[#2A1416] transition flex items-center gap-1 font-bold text-[10px]"
              >
                <Square className="w-2.5 h-2.5 text-red-400" /> Stop
              </button>
            </div>

            {selectedCameraId && (
              <button
                onClick={() => { onSelectCamera && onSelectCamera(null); setViewMode('primary'); }}
                className="flex items-center gap-1 px-2 py-1 rounded bg-[#161616] hover:bg-[#222222] text-[#9ed1c1] border border-[#262626] text-[10px] font-bold transition"
              >
                <Minimize2 className="w-3 h-3" /> Reset
              </button>
            )}
          </div>
        </div>

        {/* 2. SURVEILLANCE STREAMS GRID */}
        {displayCameras.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-12 bg-[#111111] border border-[#222222] rounded-xl text-center space-y-3 font-mono">
            <Video className="w-10 h-10 text-[#444]" />
            <div className="text-xs font-bold text-[#858585]">NO MATCHING SURVEILLANCE NODES</div>
            <button
              onClick={() => { setSearchQuery(''); setFilterStatus('ALL'); setViewMode('primary'); onSelectCamera && onSelectCamera(null); }}
              className="px-3 py-1.5 bg-[#161616] hover:bg-[#222222] text-[#f5dfc0] rounded-lg text-xs font-bold transition"
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div
            className={`grid gap-3 flex-1 ${
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
              const isNetwork = cam.source_type === 'rtsp' || (cam.source && cam.source.startsWith('http'));
            const latVal = typeof cam.lat === 'number' ? cam.lat.toFixed(4) : '18.9401';
            const lonVal = typeof cam.lon === 'number' ? cam.lon.toFixed(4) : '72.8351';

            return (
              <motion.div
                key={cam.id}
                layout
                initial={{ opacity: 0, scale: 0.99 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.15 }}
                className={`relative flex flex-col bg-[#111111] border rounded-xl overflow-hidden shadow-xl group ${
                  isSelected 
                    ? 'border-[#9ed1c1] ring-1 ring-[#9ed1c1]/40' 
                    : 'border-[#222222] hover:border-[#333333]'
                }`}
              >
                {/* Camera Top HUD Bar */}
                <div className="flex items-center justify-between px-3 py-2 bg-[#141414] border-b border-[#202020] select-none font-mono">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${cam.is_active ? 'bg-red-500 animate-pulse' : 'bg-[#555]'}`} />
                    <span className="text-xs font-bold text-[#f5dfc0] truncate">
                      NODE-0{cam.id}: {cam.name?.split(':')[1]?.trim() || cam.name}
                    </span>
                  </div>

                  {/* Badges & Quick Icons */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {isNetwork && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#161616] text-[#9ed1c1] border border-[#2A2A2A] font-bold">
                        RTSP
                      </span>
                    )}
                    {isWebcam && (
                      <span className="text-[9px] px-1.5 py-0.2 rounded bg-[#161616] text-[#f5dfc0] border border-[#2A2A2A] font-bold">
                        LOCAL
                      </span>
                    )}

                    {/* Snapshot Button */}
                    <button
                      onClick={() => handleSnapshot(cam)}
                      title="Forensic Snapshot"
                      className="p-1 rounded bg-[#181818] hover:bg-[#222222] text-[#858585] hover:text-[#9ed1c1] border border-[#262626] transition"
                    >
                      <Camera className="w-3 h-3" />
                    </button>

                    {/* Source Config Button */}
                    <button
                      onClick={() => openConfigDrawer(cam)}
                      title="Configure Source"
                      className="p-1 rounded bg-[#181818] hover:bg-[#222222] text-[#858585] hover:text-[#f5dfc0] border border-[#262626] transition"
                    >
                      <Settings className="w-3 h-3" />
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
                      title={isSelected ? 'Return to Matrix' : 'Focus Stream'}
                      className="p-1 rounded bg-[#181818] hover:bg-[#222222] text-[#858585] hover:text-[#f5dfc0] border border-[#262626] transition"
                    >
                      {isSelected ? <Minimize2 className="w-3 h-3 text-[#9ed1c1]" /> : <Maximize2 className="w-3 h-3" />}
                    </button>
                  </div>
                </div>

                {/* Camera Viewport Container */}
                <div className="relative aspect-video bg-[#050505] overflow-hidden flex items-center justify-center flex-1 min-h-[220px]">
                  {cam.is_active ? (
                    <>
                      {/* Active MJPEG Stream */}
                      <img
                        id={`cam-feed-${cam.id}`}
                        src={`/stream/${cam.id}`}
                        alt={cam.name}
                        className="w-full h-full object-cover smooth-video-feed"
                        onError={() => {
                          setStreamErrors(prev => ({ ...prev, [cam.id]: true }));
                        }}
                      />

                      {/* On-Hover Action Overlay */}
                      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/30 opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none flex flex-col justify-between p-2.5">
                        <div className="flex justify-end items-start pointer-events-auto">
                          <div className="bg-black/80 backdrop-blur-md px-2 py-0.5 rounded border border-white/10 text-[9px] font-mono text-[#f5dfc0]">
                            1080P // 30 FPS
                          </div>
                        </div>

                        <div className="flex justify-between items-end pointer-events-auto">
                          <button
                            onClick={() => onStopDetection && onStopDetection(cam.id)}
                            className="px-2 py-1 rounded bg-[#2A1417]/90 hover:bg-[#3D1A1F] text-[#ffd9d7] border border-[#8e3335] text-[10px] font-mono font-bold flex items-center gap-1 shadow-lg transition backdrop-blur-sm"
                          >
                            <Square className="w-2.5 h-2.5 text-red-400" /> Disconnect
                          </button>
                          <span className="text-[9px] font-mono text-[#858585] bg-black/80 px-2 py-0.5 rounded border border-white/10">
                            <LiveTimecode />
                          </span>
                        </div>
                      </div>
                    </>
                  ) : (
                    /* Tactical Standby Reticle */
                    <div className="flex flex-col items-center justify-center p-6 text-center space-y-2.5 font-mono relative w-full h-full">
                      <div className="w-10 h-10 rounded-xl bg-[#141414] border border-[#222222] flex items-center justify-center text-[#555]">
                        <Video className="w-5 h-5 text-[#777777]" />
                      </div>
                      <div>
                        <div className="text-[11px] font-bold text-[#cfc5b9] tracking-wider uppercase">
                          FEED STANDBY
                        </div>
                        <div className="text-[9px] text-[#777777] truncate max-w-[220px]">
                          {cam.source || 'Pipeline node'}
                        </div>
                      </div>
                      <button
                        onClick={() => onStartDetection && onStartDetection(cam.id, cam.source, cam.source_type)}
                        className="px-3 py-1.5 bg-[#161616] hover:bg-[#222222] text-[#9ed1c1] border border-[#2A2A2A] rounded-lg text-[10px] font-bold flex items-center gap-1.5 transition shadow"
                      >
                        <Play className="w-3 h-3 text-[#9ed1c1]" /> Connect Feed
                      </button>
                    </div>
                  )}
                </div>

                {/* Stream Footer Bar */}
                <div className="flex items-center justify-between px-3 py-1.5 bg-[#0E0E0E] border-t border-[#1C1C1C] text-[10px] font-mono select-none text-[#777777]">
                  <span>GPS: {latVal}°N, {lonVal}°E</span>
                  <span className={`text-[9px] px-2 py-0.5 rounded border flex items-center gap-1.5 ${
                    cam.is_active ? 'bg-[#141414] border-[#2A2A2A] text-[#9ed1c1]' : 'bg-[#121212] border-[#1C1C1C] text-[#666666]'
                  }`}>
                    {cam.is_active && <span className="w-1.5 h-1.5 rounded-full bg-[#9ed1c1] animate-pulse" />}
                    {cam.is_active ? 'ONLINE' : 'OFFLINE'}
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Camera Configuration Modal */}
      <AnimatePresence>
        {editingCamId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="w-full max-w-md bg-[#141414] border border-[#2A2A2A] rounded-2xl p-5 shadow-2xl space-y-4 font-mono text-xs text-[#e5e2e1]"
            >
              <div className="flex justify-between items-center pb-2 border-b border-[#222222]">
                <div className="flex items-center gap-2">
                  <Settings className="w-4 h-4 text-[#9ed1c1]" />
                  <span className="font-bold text-[#f5dfc0]">Configure Node-0{editingCamId}</span>
                </div>
                <button
                  onClick={() => setEditingCamId(null)}
                  className="p-1 rounded-md text-[#777777] hover:text-[#e5e2e1] transition"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Presets */}
              <div>
                <label className="text-[10px] text-[#858585] uppercase tracking-wider mb-1.5 block">Quick Source Presets</label>
                <div className="grid grid-cols-1 gap-1 max-h-36 overflow-y-auto pr-1">
                  {SOURCE_PRESETS.map((p, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleApplyPreset(p)}
                      className={`px-2.5 py-1.5 rounded-lg text-left transition border text-[11px] flex justify-between items-center ${
                        selectedPreset === p.label
                          ? 'bg-[#222222] border-[#9ed1c1] text-[#f5dfc0]'
                          : 'bg-[#181818] border-[#262626] text-[#cfc5b9] hover:bg-[#1E1E1E]'
                      }`}
                    >
                      <span className="font-bold truncate">{p.label}</span>
                      <span className="text-[9px] text-[#777777] uppercase ml-2">{p.type}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Source Input */}
              <div className="space-y-2">
                <div>
                  <label className="text-[10px] text-[#858585] uppercase tracking-wider mb-1 block">Custom Source Path / URL</label>
                  <input
                    type="text"
                    value={editSource}
                    onChange={(e) => setEditSource(e.target.value)}
                    placeholder="e.g. samples/fire_1.mp4 or rtsp://..."
                    className="w-full px-3 py-1.5 bg-[#181818] border border-[#262626] rounded-lg text-[11px] text-[#e5e2e1] outline-none focus:border-[#9ed1c1]"
                  />
                </div>
                <div className="flex gap-2">
                  {['video', 'rtsp', 'webcam'].map((st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setEditSourceType(st)}
                      className={`flex-1 py-1 rounded-lg text-[10px] font-bold uppercase transition border ${
                        editSourceType === st
                          ? 'bg-[#222222] text-[#9ed1c1] border-[#9ed1c1]'
                          : 'bg-[#181818] text-[#777777] border-[#262626]'
                      }`}
                    >
                      {st}
                    </button>
                  ))}
                </div>
              </div>

              <div className="flex gap-2 pt-2 border-t border-[#222222]">
                <button
                  onClick={() => setEditingCamId(null)}
                  className="flex-1 py-1.5 rounded-lg bg-[#181818] text-[#858585] hover:text-[#e5e2e1] border border-[#262626] transition font-bold"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleSaveConfig(editingCamId)}
                  className="flex-1 py-1.5 rounded-lg bg-[#141414] hover:bg-[#1E1E1E] text-[#9ed1c1] border border-[#9ed1c1]/50 transition font-bold shadow"
                >
                  Apply & Stream
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
