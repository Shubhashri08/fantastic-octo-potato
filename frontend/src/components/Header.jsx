import React, { useState, useEffect } from 'react';
import { ShieldAlert, Cpu, Video, Radio, RefreshCw, Layers } from 'lucide-react';

export default function Header({ statusData, onRefresh, activeTab, eventCount }) {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <header className="flex justify-between items-center w-full px-6 h-[56px] z-50 bg-[#0E0E0E] text-[#f5dfc0] border-b border-[#2A2A2A] flex-shrink-0">
      {/* Brand & System Title */}
      <div className="flex items-center gap-3">
        <div className="p-1.5 bg-[#1C1B1B] border border-[#353534] rounded text-[#f5dfc0]">
          <span className="material-symbols-outlined text-xl">dataset</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-lg tracking-wider text-[#f5dfc0] font-sans">
            VIGRAH <span className="text-[#9ed1c1]">AI</span>
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded bg-[#1C1B1B] text-[#cfc5b9] border border-[#353534] font-mono uppercase">

          </span>
        </div>
      </div>

      {/* Center Layer Indicator */}
      <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-[#131313] border border-[#2A2A2A] rounded text-xs font-mono">
        <span className="w-2 h-2 rounded-full bg-[#9ed1c1] animate-pulse" />
        <span className="text-[#cfc5b9]">ACTIVE LAYER:</span>
        <span className="text-[#f5dfc0] font-bold uppercase">{activeTab}</span>
      </div>

      {/* Right Telemetry Controls */}
      <div className="flex items-center gap-3 text-xs">
        {/* Engine Mode */}
        <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 bg-[#131313] border border-[#2A2A2A] rounded">
          <Cpu className="w-3.5 h-3.5 text-[#9ed1c1]" />
          <span className="font-mono text-[#cfc5b9]">
            {statusData?.device === 'cuda' ? 'CUDA FP16' : 'CPU FALLBACK'}
          </span>
        </div>

        {/* Live Clock */}
        <div className="font-mono text-[#f5dfc0] bg-[#131313] px-2.5 py-1 border border-[#2A2A2A] rounded">
          {time}
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          title="Refresh All Telemetry & Streams"
          className="p-1.5 rounded bg-[#1C1B1B] hover:bg-[#2A2A2A] text-[#cfc5b9] hover:text-[#f5dfc0] border border-[#2A2A2A] transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
}
