import React from 'react';
import { motion } from 'framer-motion';
import { Video, Map, Fingerprint, Zap } from 'lucide-react';

const OPERATIONAL_LAYERS = [
  {
    id: 'sense',
    name: 'Sense',
    subtitle: 'Surveillance Matrix',
    icon: Video,
    badge: null
  },
  {
    id: 'understand',
    name: 'Understand',
    subtitle: 'Geospatial Intelligence',
    icon: Map,
    badge: null
  },
  {
    id: 'identify',
    name: 'Identify',
    subtitle: 'Threat / Re-ID',
    icon: Fingerprint,
    badge: null
  },
  {
    id: 'respond',
    name: 'Respond',
    subtitle: 'Tactical Dispatch',
    icon: Zap,
    badge: 'TACTICAL'
  }
];

export default function Sidebar({ activeTab, onSelectTab, incidentCount }) {
  return (
    <aside className="flex flex-col py-4 bg-[#0C0C0C] border-r border-[#222222] w-[230px] flex-shrink-0 h-full select-none">
      {/* Sidebar Header */}
      <div className="px-4 mb-3.5">
        <h2 className="text-[10px] font-mono text-[#858585] uppercase tracking-widest mb-1 flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-[#9ed1c1] animate-ping" />
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
          const IconComponent = layer.icon;

          return (
            <motion.button
              key={layer.id}
              onClick={() => onSelectTab(layer.id)}
              whileHover={{ x: 2 }}
              whileTap={{ scale: 0.98 }}
              transition={{ type: 'spring', stiffness: 400, damping: 25 }}
              className={`relative flex items-center justify-between px-4 py-2.5 w-full text-left transition-colors ${
                isActive
                  ? 'text-[#f5dfc0]'
                  : 'text-[#cfc5b9] hover:text-[#e5e2e1] hover:bg-[#141414]'
              }`}
            >
              {/* Shared Layout Active Indicator Pill */}
              {isActive && (
                <motion.div
                  layoutId="activeLayerIndicator"
                  className="absolute inset-0 bg-[#1A1A1A] border-l-4 border-[#9ed1c1]"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}

              <div className="flex items-center gap-3 relative z-10">
                <div className={`p-1.5 rounded-md transition-colors ${
                  isActive ? 'bg-[#242424] text-[#9ed1c1]' : 'text-[#858585]'
                }`}>
                  <IconComponent className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-semibold tracking-wide font-sans">{layer.name}</div>
                  <div className="text-[10px] text-[#858585] font-mono">{layer.subtitle}</div>
                </div>
              </div>



              {layer.badge && layer.id !== 'respond' && (
                <span className="relative z-10 text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#141414] text-[#9ed1c1] border border-[#262626]">
                  {layer.badge}
                </span>
              )}
            </motion.button>
          );
        })}
      </nav>
    </aside>
  );
}
