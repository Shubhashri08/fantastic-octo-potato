import React, { useState, useEffect } from 'react';
import { Shield, Cpu, RefreshCw, Clock } from 'lucide-react';

export default function Header({ statusData, onRefresh, activeTab }) {
  const [time, setTime] = useState(new Date().toLocaleTimeString());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const layerLabels = {
    sense: 'Sense // Surveillance Matrix',
    understand: 'Understand // GIS & Trajectory',
    identify: 'Identify // Forensic Re-ID',
    respond: 'Respond // Tactical Dispatch'
  };

  return (
    <header className="flex justify-between items-center w-full px-5 h-[50px] z-50 bg-[#0A0A0A] text-[#f5dfc0] border-b border-[#222222] flex-shrink-0 select-none">
      {/* Brand & System Title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-[#141414] border border-[#2A2A2A] flex items-center justify-center text-[#9ed1c1] shadow-sm">
          <Shield className="w-4 h-4 text-[#9ed1c1]" />
        </div>
        <div className="flex items-center gap-2.5">
          <span className="font-bold text-base tracking-wider text-[#f5dfc0] font-sans">
            VIGRAH <span className="text-[#9ed1c1]">AI</span>
          </span>
        </div>
      </div>

      {/* Center Operational Context */}
      <div className="hidden md:flex items-center gap-2.5 px-3 py-1 bg-[#121212] border border-[#222222] rounded-full text-xs font-mono">
        <span className="w-2 h-2 rounded-full bg-[#9ed1c1] animate-pulse" />
        <span className="text-[#858585] uppercase">Layer:</span>
        <span className="text-[#f5dfc0] font-semibold">{layerLabels[activeTab] || activeTab}</span>
      </div>

      {/* Right Telemetry Controls */}
      <div className="flex items-center gap-2.5 text-xs">
        {/* Hardware Status */}
        <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 bg-[#121212] border border-[#222222] rounded-md">
          <Cpu className="w-3.5 h-3.5 text-[#9ed1c1]" />
          <span className="font-mono text-[11px] text-[#cfc5b9]">
            {statusData?.device === 'cuda' ? 'CUDA FP16' : 'CPU FALLBACK'}
          </span>
        </div>

        {/* Live Clock */}
        <div className="flex items-center gap-1.5 font-mono text-[11px] text-[#f5dfc0] bg-[#121212] px-2.5 py-1 border border-[#222222] rounded-md">
          <Clock className="w-3.5 h-3.5 text-[#858585]" />
          <span>{time}</span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          title="Refresh Feeds & Telemetry"
          className="p-1.5 rounded-md bg-[#141414] hover:bg-[#1E1E1E] text-[#cfc5b9] hover:text-[#f5dfc0] border border-[#262626] transition-colors"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
      </div>
    </header>
  );
}
