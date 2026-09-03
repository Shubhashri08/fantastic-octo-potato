import React, { useState } from 'react';
import { Navigation, Compass, MapPin, Layers } from 'lucide-react';
import CameraMap from './CameraMap';
import EventReconstruction from './EventReconstruction';

export default function UnderstandConsole({
  cameras = [],
  events = [],
  selectedCameraId,
  onSelectCamera,
  onNavigateToLive,
  initialMode = 'map'
}) {
  const [activeMode, setActiveMode] = useState(initialMode); // 'map' | 'reconstruction'

  return (
    <div className="h-full w-full flex flex-col bg-[#0A0A0A] overflow-hidden select-none">
      {/* Top Understand Sub-Navigation Bar */}
      <div className="px-6 py-2.5 bg-[#111111] border-b border-[#222222] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-1.5 rounded-lg bg-[#181818] border border-[#2a2a2a] text-[#f5dfc0]">
            <Navigation className="w-4 h-4 text-[#f5dfc0]" />
          </div>
          <div>
            <h1 className="text-xs font-bold text-[#f5dfc0] font-sans tracking-wide">
              LAYER 2: UNDERSTAND & GEOSPATIAL INTELLIGENCE
            </h1>
            <p className="text-[10px] font-mono text-[#858585]">
              CCTV Surveillance Grid & Incident Movement Reconstruction
            </p>
          </div>
        </div>

        {/* Mode Switcher */}
        <div className="flex items-center bg-[#0a0a0a] p-1 rounded-xl border border-[#262626]">
          <button
            onClick={() => setActiveMode('map')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              activeMode === 'map'
                ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                : 'text-[#858585] hover:text-[#e5e2e1]'
            }`}
          >
            <MapPin className="w-3.5 h-3.5" />
            CAMERA MAP
          </button>

          <button
            onClick={() => setActiveMode('reconstruction')}
            className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              activeMode === 'reconstruction'
                ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                : 'text-[#858585] hover:text-[#e5e2e1]'
            }`}
          >
            <Compass className="w-3.5 h-3.5 text-[#00F2FE]" />
            EVENT RECONSTRUCTION
          </button>
        </div>
      </div>

      {/* Workspace Body */}
      <div className="flex-1 h-[calc(100%-49px)] overflow-hidden">
        {activeMode === 'map' ? (
          <CameraMap
            cameras={cameras}
            events={events}
            selectedCameraId={selectedCameraId}
            onSelectCamera={onSelectCamera}
            onNavigateToLive={onNavigateToLive}
          />
        ) : (
          <EventReconstruction
            events={events}
            cameras={cameras}
            onNavigateToLive={onNavigateToLive}
          />
        )}
      </div>
    </div>
  );
}
