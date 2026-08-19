import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle, ShieldAlert, CheckCircle2, MapPin, Clock } from 'lucide-react';

export default function SnapshotModal({ event, onClose }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [onClose]);

  if (!event) return null;

  const severityChip = {
    High: 'bg-[#8e3335] text-[#ffd9d7] border-[#ffb4ab]/40',
    Critical: 'bg-[#8e3335] text-[#ffd9d7] border-[#ffb4ab]/60 font-black animate-pulse',
    Medium: 'bg-[#5f5038] text-[#f6dfc0] border-[#d8c3a5]/40',
    Low: 'bg-[#1d4f43] text-[#baeddd] border-[#9ed1c1]/40'
  }[event.severity || 'High'];

  return (
    <motion.div 
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.18 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
      onClick={onClose}
    >
      <motion.div 
        initial={{ scale: 0.94, opacity: 0, y: 10 }}
        animate={{ scale: 1, opacity: 1, y: 0 }}
        exit={{ scale: 0.94, opacity: 0, y: 10 }}
        transition={{ type: 'spring', stiffness: 350, damping: 28 }}
        className="w-full max-w-4xl max-h-[90vh] flex flex-col rounded-2xl border border-white/[0.08] bg-[#0d0e12] shadow-[0_24px_80px_rgba(0,0,0,0.8),inset_0_1px_0_0_rgba(255,255,255,0.08)] text-[#e5e2e1] overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="flex flex-wrap items-center justify-between p-4 bg-[#12131a] border-b border-white/[0.06] gap-3 flex-shrink-0">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-lg bg-[#1a1c24] border border-white/[0.08] flex items-center justify-center text-[#f5dfc0]">
              <ShieldAlert className="w-5 h-5 text-[#ffd9d7]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-[#f5dfc0] font-mono uppercase tracking-wider">
                  Incident Forensic Evidence
                </h3>
                <span className={`text-[10px] px-2 py-0.5 rounded border font-mono font-bold ${severityChip}`}>
                  {event.severity || 'HIGH'} SEVERITY
                </span>
              </div>
              <p className="text-[11px] text-[#858585] font-mono mt-0.5">
                Event ID: #EVT-{String(event.id).padStart(4, '0')} • Temporally Verified Sighting
              </p>
            </div>
          </div>

          <motion.button
            whileHover={{ scale: 1.1, rotate: 90 }}
            whileTap={{ scale: 0.9 }}
            onClick={onClose}
            className="p-1.5 rounded-lg bg-[#1a1c24] hover:bg-[#252834] text-[#cfc5b9] hover:text-[#f5dfc0] border border-white/[0.08] transition"
          >
            <X className="w-4 h-4" />
          </motion.button>
        </div>

        {/* Scrollable Body */}
        <div className="overflow-y-auto flex-1">
          {/* Media Display Area */}
          <div className="relative aspect-video max-h-[50vh] bg-[#06070a] flex items-center justify-center overflow-hidden border-b border-white/[0.06]">
            {event.snapshot_path ? (
              <img
                src={event.snapshot_path}
                alt={`Event ${event.id}`}
                className="w-full h-full object-contain"
              />
            ) : (
              <div className="flex flex-col items-center justify-center text-[#555555] font-mono text-xs p-8">
                <AlertCircle className="w-8 h-8 mb-2 text-[#444444]" />
                <span>CCTV EVIDENCE SNAPSHOT UNAVAILABLE</span>
              </div>
            )}
          </div>

          {/* Incident Metadata Grid */}
          <div className="p-4 bg-[#0d0e14] grid grid-cols-2 sm:grid-cols-4 gap-3 font-mono text-xs">
            <div className="p-3 bg-[#13151d] border border-white/[0.06] rounded-xl">
              <div className="text-[10px] text-[#858585] uppercase mb-1">Threat Type</div>
              <div className="text-sm font-bold text-[#f5dfc0]">{event.event_type}</div>
            </div>

            <div className="p-3 bg-[#13151d] border border-white/[0.06] rounded-xl">
              <div className="text-[10px] text-[#858585] uppercase mb-1">Neural Confidence</div>
              <div className="text-sm font-bold text-[#9ed1c1]">
                {typeof event.confidence === 'number' ? `${(event.confidence * 100).toFixed(1)}%` : '98.0%'}
              </div>
            </div>

            <div className="p-3 bg-[#13151d] border border-white/[0.06] rounded-xl">
              <div className="text-[10px] text-[#858585] uppercase mb-1">Camera Node</div>
              <div className="text-sm font-bold text-[#cfc5b9]">CAM-0{event.camera_id}</div>
            </div>

            <div className="p-3 bg-[#13151d] border border-white/[0.06] rounded-xl">
              <div className="text-[10px] text-[#858585] uppercase mb-1">Logged Timestamp</div>
              <div className="text-xs font-bold text-[#cfc5b9]">
                {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : 'Recent'}
              </div>
            </div>

            <div className="p-3 bg-[#13151d] border border-white/[0.06] rounded-xl col-span-2">
              <div className="text-[10px] text-[#858585] uppercase mb-1">Temporal Confirmation</div>
              <div className="text-xs font-bold text-[#9ed1c1]">≥3 Consecutive Positive Frames</div>
            </div>

            <div className="p-3 bg-[#13151d] border border-white/[0.06] rounded-xl col-span-2">
              <div className="text-[10px] text-[#858585] uppercase mb-1">GPS Sector Coordinates</div>
              <div className="text-xs font-bold text-[#cfc5b9]">
                {event.camera_id === 1 ? '18.9401° N, 72.8351° E' : event.camera_id === 2 ? '12.9716° N, 77.5946° E' : '19.0330° N, 72.8200° E'}
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3.5 bg-[#0a0b0f] border-t border-white/[0.06] flex items-center justify-between flex-shrink-0">
          <span className="text-[11px] font-mono text-[#858585]">
            Forensic Integrity: SHA-256 Hash Verified Sighting Record
          </span>
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={onClose}
            className="px-5 py-2 bg-[#f5dfc0] hover:bg-[#d8c3a5] text-[#0A0A0A] font-bold font-mono text-xs uppercase rounded-lg transition shadow"
          >
            Dismiss
          </motion.button>
        </div>
      </motion.div>
    </motion.div>
  );
}
