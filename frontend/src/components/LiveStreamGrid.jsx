import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Maximize2, Minimize2, Play, Square, Settings, Radio, Video, Camera, ShieldAlert } from 'lucide-react';

export default function LiveStreamGrid({
  cameras,
  selectedCameraId,
  onSelectCamera,
  onStartDetection,
  onStopDetection
}) {
  const [editingCamId, setEditingCamId] = useState(null);
  const [editSource, setEditSource] = useState('');
  const [editSourceType, setEditSourceType] = useState('video');

  const [viewMode, setViewMode] = useState('primary'); // 'primary' (1-3), 'all' (1-6), or specific camId

  const openConfigDrawer = (cam) => {
    setEditingCamId(cam.id);
    setEditSource(cam.source || '');
    setEditSourceType(cam.source_type || 'video');
  };

  const handleSaveConfig = (camId) => {
    onStartDetection(camId, editSource, editSourceType);
    setEditingCamId(null);
  };

  const activeCamerasCount = cameras.filter(c => c.is_active).length;
  
  let displayCameras = [];
  if (selectedCameraId) {
    const focused = cameras.find((c) => c.id === selectedCameraId);
    displayCameras = focused ? [focused] : cameras.slice(0, 3);
  } else if (viewMode === 'all') {
    displayCameras = cameras;
  } else if (viewMode === 'primary') {
    // Show CAM-01, CAM-02, CAM-03 by default
    displayCameras = cameras.length >= 3 ? cameras.slice(0, 3) : cameras;
  } else if (typeof viewMode === 'number') {
    const single = cameras.find(c => c.id === viewMode);
    displayCameras = single ? [single] : cameras.slice(0, 3);
  } else {
    displayCameras = cameras.slice(0, 3);
  }

  return (
    <div className="flex flex-col h-full overflow-y-auto p-5 bg-[#060709] text-[#e5e2e1] gap-4">
      {/* Header Bar */}
      <div className="flex flex-wrap items-center justify-between pb-3 border-b border-white/[0.06] gap-3">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-[#12131a] border border-white/[0.08] flex items-center justify-center text-[#f5dfc0]">
            <Radio className="w-5 h-5 animate-pulse text-[#f5dfc0]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-[#f5dfc0] uppercase tracking-wider font-mono">
                Sense Layer — Live Surveillance Matrix
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1c2e26] text-[#9ed1c1] border border-[#2a4d3e] font-bold">
                {activeCamerasCount} OF {cameras.length} ACTIVE
              </span>
            </div>
            <p className="text-[11px] text-[#858585] font-mono mt-0.5">
              Real-Time AI Multi-Threat Analytics (Violence, Fire Outbreak & Road Accident Detection)
            </p>
          </div>
        </div>

        {/* View Switcher Controls */}
        <div className="flex items-center gap-1.5 bg-[#0e0f16] p-1 rounded-xl border border-white/[0.08]">
          <button
            onClick={() => { setViewMode('primary'); onSelectCamera(null); }}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition ${
              viewMode === 'primary' && !selectedCameraId
                ? 'bg-[#f5dfc0] text-[#0A0A0A]'
                : 'text-[#858585] hover:text-[#e5e2e1]'
            }`}
          >
            Main Matrix (CAM 1-3)
          </button>
          <button
            onClick={() => { setViewMode('all'); onSelectCamera(null); }}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-bold transition ${
              viewMode === 'all' && !selectedCameraId
                ? 'bg-[#f5dfc0] text-[#0A0A0A]'
                : 'text-[#858585] hover:text-[#e5e2e1]'
            }`}
          >
            All Nodes ({cameras.length})
          </button>
          <button
            onClick={() => { setViewMode(3); onSelectCamera(3); }}
            className={`px-3 py-1 rounded-lg text-xs font-mono font-bold flex items-center gap-1 transition ${
              selectedCameraId === 3 || viewMode === 3
                ? 'bg-[#1c2e26] text-[#9ed1c1] border border-[#2a4d3e]'
                : 'text-[#cfc5b9] hover:text-[#f5dfc0]'
            }`}
          >
            <span className="w-1.5 h-1.5 rounded-full bg-[#00f2fe] animate-pulse" />
            CAM-03 (Network IP)
          </button>

          {selectedCameraId && (
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => { onSelectCamera(null); setViewMode('primary'); }}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-[#161822] hover:bg-[#202433] text-[#f5dfc0] border border-white/[0.08] text-xs font-mono font-bold transition ml-1"
            >
              <Minimize2 className="w-3 h-3" /> Reset View
            </motion.button>
          )}
        </div>
      </div>

      {/* Quick Channel Bar */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1">
        <span className="text-[10px] font-mono text-[#858585] uppercase tracking-wider whitespace-nowrap">Channels:</span>
        {cameras.map((cam) => {
          const isCurrent = (selectedCameraId === cam.id) || (displayCameras.length === 1 && displayCameras[0]?.id === cam.id);
          return (
            <button
              key={cam.id}
              onClick={() => {
                setViewMode(cam.id);
                onSelectCamera(cam.id);
              }}
              className={`px-2.5 py-1 rounded-lg text-[11px] font-mono whitespace-nowrap transition flex items-center gap-1.5 border ${
                isCurrent
                  ? 'bg-[#202433] text-[#f5dfc0] border-[#f5dfc0]'
                  : cam.is_active
                  ? 'bg-[#10131a] text-[#cfc5b9] border-white/[0.08] hover:border-white/[0.2]'
                  : 'bg-[#0d0e14] text-[#858585] border-white/[0.04] hover:text-[#cfc5b9]'
              }`}
            >
              <span className={`w-1.5 h-1.5 rounded-full ${cam.is_active ? 'bg-[#00f2fe]' : 'bg-[#555]'}`} />
              CAM-0{cam.id} {cam.id === 3 ? '(Network Feed)' : ''}
            </button>
          );
        })}
      </div>

      {/* Grid Layout (Clean 3-Feed Bento Grid) */}
      <div
        className={`grid gap-4 flex-1 ${
          displayCameras.length === 1
            ? 'grid-cols-1 max-w-4xl mx-auto w-full'
            : displayCameras.length === 2
            ? 'grid-cols-1 md:grid-cols-2'
            : 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3'
        }`}
      >
        {displayCameras.map((cam, idx) => {
          const isSelected = selectedCameraId === cam.id;
          const isWebcam = cam.source_type === 'webcam' || cam.source === '0';
          const isNetwork = cam.id === 3 || cam.source_type === 'rtsp' || cam.source?.startsWith('http');

          return (
            <motion.div
              key={cam.id}
              layout
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2 }}
              className={`relative flex flex-col bg-[#0d0e14] border rounded-2xl overflow-hidden transition-all shadow-xl ${
                isSelected ? 'border-[#f5dfc0]' : 'border-white/[0.08] hover:border-white/[0.2]'
              }`}
            >
              {/* Camera Header HUD */}
              <div className="flex items-center justify-between px-3.5 py-2.5 bg-[#11121a] border-b border-white/[0.06] select-none">
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1.5 text-[10px] font-mono font-bold text-[#ffd9d7]">
                    <span className={`w-2 h-2 rounded-full ${cam.is_active ? 'bg-[#8e3335] animate-pulse' : 'bg-[#555]'}`} />
                    {cam.is_active ? 'REC' : 'OFFLINE'} CAM-0{cam.id}
                  </span>
                  <span className="text-[11px] font-bold text-[#e5e2e1] truncate max-w-[170px]" title={cam.name}>
                    {cam.name}
                  </span>
                </div>

                <div className="flex items-center gap-1.5">
                  {isNetwork && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#1c2e26] text-[#9ed1c1] border border-[#2a4d3e] font-bold">
                      IP / NETWORK
                    </span>
                  )}
                  {isWebcam && (
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#f5dfc0] text-[#0A0A0A] font-black">
                      LIVE CAM
                    </span>
                  )}
                  <button
                    onClick={() => {
                      if (selectedCameraId === cam.id) {
                        onSelectCamera(null);
                        setViewMode('primary');
                      } else {
                        onSelectCamera(cam.id);
                        setViewMode(cam.id);
                      }
                    }}
                    className="p-1 text-[#858585] hover:text-[#f5dfc0] transition"
                  >
                    {isSelected ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Video Stream Container */}
              <div className="relative aspect-video bg-black overflow-hidden flex items-center justify-center flex-1 min-h-[220px]">
                {cam.is_active ? (
                  <img
                    src={`/stream/${cam.id}`}
                    alt={cam.name}
                    className="w-full h-full object-contain"
                    onError={(e) => {
                      // Fallback image handling
                    }}
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center p-6 text-center space-y-3">
                    <Video className="w-10 h-10 text-[#858585] opacity-40" />
                    <div>
                      <div className="text-xs font-mono font-bold text-[#e5e2e1]">CAMERA STANDBY</div>
                      <div className="text-[10px] font-mono text-[#858585] mt-0.5 truncate max-w-[240px]">
                        Source: {cam.source || 'Not configured'}
                      </div>
                    </div>
                    <button
                      onClick={() => onStartDetection(cam.id, cam.source, cam.source_type)}
                      className="px-3.5 py-1.5 bg-[#142820] hover:bg-[#1c382c] text-[#9ed1c1] border border-[#1d4f43] rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition shadow"
                    >
                      <Play className="w-3 h-3" /> Connect & Start Feed
                    </button>
                  </div>
                )}
                
                <div className="absolute top-2 left-2 bg-black/75 px-2 py-0.5 border border-white/[0.08] text-[9px] font-mono text-[#9ed1c1] rounded">
                  NODE-0{cam.id} // {cam.source_type.toUpperCase()}
                </div>
              </div>

              {/* Camera Footer HUD */}
              <div className="flex items-center justify-between px-3.5 py-2 bg-[#0e0f16] border-t border-white/[0.06] text-[10px] font-mono">
                <div className="flex items-center gap-2">
                  {cam.is_active ? (
                    <button
                      onClick={() => onStopDetection(cam.id)}
                      className="px-2.5 py-1 rounded bg-[#2a1416] hover:bg-[#3a1a1c] text-[#ffd9d7] border border-[#8e3335] flex items-center gap-1 font-bold transition"
                    >
                      <Square className="w-2.5 h-2.5" /> Stop
                    </button>
                  ) : (
                    <button
                      onClick={() => onStartDetection(cam.id, cam.source, cam.source_type)}
                      className="px-2.5 py-1 rounded bg-[#142820] hover:bg-[#1c382c] text-[#9ed1c1] border border-[#1d4f43] flex items-center gap-1 font-bold transition"
                    >
                      <Play className="w-2.5 h-2.5" /> Start
                    </button>
                  )}

                  <button
                    onClick={() => openConfigDrawer(cam)}
                    className="px-2.5 py-1 rounded bg-[#161822] hover:bg-[#202433] text-[#cfc5b9] border border-white/[0.08] flex items-center gap-1 transition"
                  >
                    <Settings className="w-2.5 h-2.5" /> Source
                  </button>
                </div>

                <span className="text-[#858585] text-[10px]">
                  GPS: {cam.lat.toFixed(4)}, {cam.lon.toFixed(4)}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Source Configuration Overlay Drawer */}
      <AnimatePresence>
        {editingCamId !== null && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md"
            onClick={() => setEditingCamId(null)}
          >
            <motion.div
              initial={{ scale: 0.95, y: 10 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.95, y: 10 }}
              className="w-full max-w-md bg-[#0d0e14] border border-white/[0.1] rounded-2xl p-5 shadow-2xl text-[#e5e2e1] space-y-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-white/[0.06] pb-3">
                <h3 className="text-sm font-bold text-[#f5dfc0] font-mono uppercase">
                  Configure CAM-0{editingCamId} Stream Source
                </h3>
                <button onClick={() => setEditingCamId(null)} className="text-xs text-[#858585]">✕</button>
              </div>

              <div className="space-y-3 font-mono text-xs">
                <label className="block text-[#858585] text-[10px] uppercase">Protocol Type</label>
                <div className="grid grid-cols-3 gap-2">
                  {['video', 'webcam', 'rtsp'].map((type) => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => {
                        setEditSourceType(type);
                        if (type === 'webcam') setEditSource('0');
                      }}
                      className={`py-1.5 rounded-lg text-center border uppercase text-[11px] font-bold ${
                        editSourceType === type
                          ? 'bg-[#f5dfc0] text-[#0A0A0A] border-[#f5dfc0]'
                          : 'bg-[#141620] text-[#858585] border-white/[0.06]'
                      }`}
                    >
                      {type}
                    </button>
                  ))}
                </div>

                <label className="block text-[#858585] text-[10px] uppercase mt-2">Source Path / URL</label>
                <input
                  type="text"
                  value={editSource}
                  onChange={(e) => setEditSource(e.target.value)}
                  placeholder="0 (Webcam), or samples/cctv.mp4, or rtsp://..."
                  className="w-full px-3 py-2 bg-[#06070a] border border-white/[0.08] rounded-lg text-[#e5e2e1] text-xs font-mono focus:border-[#f5dfc0] outline-none"
                />
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-white/[0.06]">
                <button
                  onClick={() => setEditingCamId(null)}
                  className="px-4 py-2 bg-[#161822] text-[#858585] hover:text-[#e5e2e1] rounded-lg text-xs font-mono"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleSaveConfig(editingCamId)}
                  className="px-5 py-2 bg-[#f5dfc0] text-[#0A0A0A] font-bold text-xs font-mono uppercase rounded-lg shadow"
                >
                  Apply Source
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
