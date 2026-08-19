import React from 'react';
import { motion } from 'framer-motion';

const OPERATIONAL_LAYERS = [
  {
    id: 'sense',
    name: 'Sense',
    subtitle: 'Surveillance Matrix',
    icon: 'radar',
    badge: 'LIVE FEEDS'
  },
  {
    id: 'understand',
    name: 'Understand',
    subtitle: 'Geospatial Intelligence',
    icon: 'map',
    badge: 'GIS'
  },
  {
    id: 'identify',
    name: 'Identify',
    subtitle: 'Threat / Re-ID',
    icon: 'fingerprint',
    badge: null
  },
  {
    id: 'respond',
    name: 'Respond',
    subtitle: 'Tactical Dispatch',
    icon: 'bolt',
    badge: 'TACTICAL'
  }
];

export default function Sidebar({ activeTab, onSelectTab, incidentCount }) {
  return (
    <aside className="flex flex-col py-4 bg-[#111111] border-r border-[#2A2A2A] w-[235px] flex-shrink-0 h-full select-none">
      {/* Sidebar Header */}
      <div className="px-4 mb-4">
        <h2 className="text-[10px] font-mono text-[#cfc5b9] uppercase tracking-widest mb-1 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#f5dfc0] animate-ping" />
          VIGRAH COMMAND
        </h2>
        <h1 className="text-xs font-bold text-[#f5dfc0] tracking-wider font-sans">
          OPERATIONAL LAYERS
        </h1>
      </div>

      {/* Navigation Layer Buttons */}
      <nav className="flex flex-col gap-1 w-full flex-1 relative">
        {OPERATIONAL_LAYERS.map((layer) => {
          const isActive = activeTab === layer.id;
          return (
            <motion.button
              key={layer.id}
              onClick={() => onSelectTab(layer.id)}
              whileHover={{ x: 3 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className={`relative flex items-center justify-between px-4 py-2.5 w-full text-left transition-colors ${
                isActive
                  ? 'text-[#f5dfc0]'
                  : 'text-[#cfc5b9] hover:text-[#e5e2e1] hover:bg-[#161616]'
              }`}
            >
              {/* Shared Layout Active Indicator Pill */}
              {isActive && (
                <motion.div
                  layoutId="activeLayerIndicator"
                  className="absolute inset-0 bg-[#1E1E1E] border-l-4 border-[#f5dfc0]"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}

              <div className="flex items-center gap-3 relative z-10">
                <span
                  className={`material-symbols-outlined text-lg transition-colors ${
                    isActive ? 'text-[#f5dfc0] material-symbols-filled' : 'text-[#988f85]'
                  }`}
                >
                  {layer.icon}
                </span>
                <div>
                  <div className="text-xs font-semibold tracking-wide font-sans">{layer.name}</div>
                  <div className="text-[10px] text-[#988f85] font-mono">{layer.subtitle}</div>
                </div>
              </div>

              {layer.id === 'respond' && incidentCount > 0 && (
                <motion.span
                  initial={{ scale: 0.8 }}
                  animate={{ scale: 1 }}
                  className="relative z-10 text-[10px] font-mono px-1.5 py-0.2 rounded bg-[#8e3335] text-[#ffd9d7] font-bold"
                >
                  {Math.min(incidentCount, 10)} ACTIVE
                </motion.span>
              )}

              {layer.badge && layer.id !== 'respond' && (
                <span className="relative z-10 text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#161616] text-[#9ed1c1] border border-[#2A2A2A]">
                  {layer.badge}
                </span>
              )}
            </motion.button>
          );
        })}
      </nav>

      {/* Bottom Health Pill */}
      <motion.div
        whileHover={{ scale: 1.02 }}
        className="p-3 mx-3 bg-[#161616] border border-[#262626] rounded text-[11px] font-mono shadow-inner"
      >
        <div className="flex items-center justify-between mb-1">
          <span className="text-[#cfc5b9]">NODE STATUS</span>
          <span className="flex items-center gap-1 text-[#9ed1c1] font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-[#9ed1c1] animate-pulse" /> ONLINE
          </span>
        </div>
        <div className="text-[10px] text-[#988f85]">
          Violence & Fire Neural Engine
        </div>
      </motion.div>
    </aside>
  );
}
