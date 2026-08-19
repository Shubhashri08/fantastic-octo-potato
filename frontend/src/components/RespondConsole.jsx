import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldAlert, AlertTriangle, Send, CheckCircle2, PhoneCall, Radio, Truck, Siren, Eye, X } from 'lucide-react';

export default function RespondConsole({ events, cameras, onSelectEvent }) {
  const [dispatches, setDispatches] = useState({});
  const [selectedIncident, setSelectedIncident] = useState(events[0] || null);
  const [pendingDispatch, setPendingDispatch] = useState(null); // { eventId, actionType, actionTitle, units }

  const highSeverityEvents = events.filter(e => e.event_type === 'Fighting' || e.event_type === 'Fire' || e.severity === 'High');

  const openDispatchConfirmation = (eventId, actionType, actionTitle, units) => {
    setPendingDispatch({
      eventId,
      actionType,
      actionTitle,
      units,
      timestamp: new Date().toLocaleTimeString()
    });
  };

  const confirmDispatch = () => {
    if (!pendingDispatch) return;
    const key = `${pendingDispatch.eventId}_${pendingDispatch.actionType}`;
    setDispatches(prev => ({
      ...prev,
      [key]: {
        time: new Date().toLocaleTimeString(),
        status: 'DISPATCHED',
        actionTitle: pendingDispatch.actionTitle
      }
    }));
    setPendingDispatch(null);
  };

  const getCameraName = (camId) => {
    const c = cameras.find(cam => cam.id === camId);
    return c ? c.name : `CAM-0${camId}`;
  };

  const getCameraGps = (camId) => {
    const c = cameras.find(cam => cam.id === camId);
    return c ? `${c.lat.toFixed(4)}°N, ${c.lon.toFixed(4)}°E` : '28.6139°N, 77.2090°E';
  };

  return (
    <div className="flex flex-col lg:flex-row h-full overflow-hidden bg-[#0A0A0A] relative">
      {/* Left Column: Critical Incidents Queue */}
      <div className="w-full lg:w-[380px] border-r border-[#2A2A2A] bg-[#111111] p-4 flex flex-col flex-shrink-0">
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#222222]">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-[#8e3335]">bolt</span>
            <div>
              <h2 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider font-mono">
                Respond Layer — Tactical Action Stack
              </h2>
              <p className="text-[10px] text-[#988f85] font-mono">Real-Time Threat Queue (Violence & Fire)</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-1.5 py-0.5 bg-[#241113] text-[#ffd9d7] border border-[#8e3335] font-bold">
            {highSeverityEvents.length} QUEUED
          </span>
        </div>

        {/* Incident List */}
        <div className="flex-1 overflow-y-auto space-y-2 pr-1">
          {highSeverityEvents.length === 0 ? (
            <div className="py-12 text-center text-[#555555] font-mono text-xs">
              No active violence or fire emergencies in queue.
            </div>
          ) : (
            highSeverityEvents.map((ev) => {
              const isSelected = selectedIncident?.id === ev.id;
              return (
                <motion.div
                  key={ev.id}
                  whileHover={{ x: 2 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => setSelectedIncident(ev)}
                  className={`solid-card p-3 cursor-pointer border transition ${
                    isSelected ? 'border-[#f5dfc0] bg-[#181818]' : 'border-[#262626] hover:border-[#353534]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-mono font-bold text-[#ffd9d7] bg-[#8e3335] px-1.5 py-0.2">
                      CRITICAL ALERT #{ev.id}
                    </span>
                    <span className="text-[10px] font-mono text-[#988f85]">
                      {new Date(ev.timestamp).toLocaleTimeString()}
                    </span>
                  </div>

                  <div className="text-xs font-bold text-[#f5dfc0] mb-1">
                    {ev.event_type === 'Fighting' ? '⚔️ VIOLENCE / FIGHTING' : '🔥 FIRE OUTBREAK'}
                  </div>

                  <div className="text-[11px] font-mono text-[#cfc5b9] flex items-center justify-between">
                    <span>{getCameraName(ev.camera_id)}</span>
                    <span className="text-[#9ed1c1] font-bold">{(ev.confidence * 100).toFixed(0)}% CONF</span>
                  </div>
                </motion.div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Column: Threat Mitigation Panel */}
      <div className="flex-1 p-5 bg-[#0D0D0D] flex flex-col justify-between overflow-y-auto">
        {selectedIncident ? (
          <div className="space-y-5">
            {/* Header detail */}
            <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-3 border-b border-[#222222] gap-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-[#f5dfc0] font-mono uppercase">
                    Incident #{selectedIncident.id} — Threat Mitigation Command
                  </span>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-bold bg-[#8e3335] text-[#ffd9d7]">
                    CRITICAL SEVERITY
                  </span>
                </div>
                <p className="text-xs text-[#988f85] font-mono">
                  Location: {getCameraName(selectedIncident.camera_id)} • GPS: {getCameraGps(selectedIncident.camera_id)}
                </p>
              </div>

              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onSelectEvent(selectedIncident)}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-[#1C1B1B] hover:bg-[#2A2A2A] text-[#f5dfc0] border border-[#353534] text-xs font-mono font-bold"
              >
                <Eye className="w-3.5 h-3.5" /> Inspect Verified Snapshot
              </motion.button>
            </div>

            {/* Visual Snapshot & Telemetry */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="solid-card p-3 space-y-2">
                <span className="text-[10px] font-mono text-[#988f85] uppercase">Live Incident Capture Frame</span>
                <div className="relative aspect-video bg-[#0E0E0E] border border-[#222222] overflow-hidden">
                  <img
                    src={selectedIncident.snapshot_path}
                    alt="Snapshot"
                    className="w-full h-full object-contain"
                  />
                </div>
              </div>

              <div className="solid-card p-4 space-y-3 font-mono text-xs">
                <span className="text-[10px] text-[#988f85] uppercase">Incident Telemetry</span>
                <div className="space-y-2">
                  <div className="flex justify-between border-b border-[#222222] pb-1">
                    <span className="text-[#988f85]">Threat Classification</span>
                    <span className="text-[#f5dfc0] font-bold">{selectedIncident.event_type}</span>
                  </div>
                  <div className="flex justify-between border-b border-[#222222] pb-1">
                    <span className="text-[#988f85]">Neural Confidence</span>
                    <span className="text-[#9ed1c1] font-bold">{(selectedIncident.confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between border-b border-[#222222] pb-1">
                    <span className="text-[#988f85]">GPS Target Sector</span>
                    <span className="text-[#cfc5b9]">{getCameraGps(selectedIncident.camera_id)}</span>
                  </div>
                  <div className="flex justify-between border-b border-[#222222] pb-1">
                    <span className="text-[#988f85]">Temporal Confirmation</span>
                    <span className="text-[#9ed1c1]">≥3 Consecutive Positive Frames</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Tactical Response Action Triggers (Two-Step Modal Confirmation) */}
            <div className="space-y-3">
              <span className="text-xs font-bold font-mono text-[#f5dfc0] uppercase tracking-wider">
                Authorized Tactical Response Protocols (Two-Step Verification)
              </span>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Action 1: Police Intercept for Violence */}
                <div className="solid-card p-3 flex flex-col justify-between space-y-3">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-[#ffd9d7]" />
                    <div className="text-xs font-bold text-[#f5dfc0]">Police / Security Intercept</div>
                  </div>
                  <p className="text-[10px] text-[#988f85] font-mono">
                    Direct automated alert to on-ground patrol and security units.
                  </p>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => openDispatchConfirmation(selectedIncident.id, 'POLICE', 'Police & Security Intercept Unit', '2 Sector Patrol Cars + QRT Squad')}
                    className={`w-full py-1.5 text-[11px] font-bold font-mono uppercase tracking-wider transition ${
                      dispatches[`${selectedIncident.id}_POLICE`]
                        ? 'bg-[#1d4f43] text-[#9ed1c1] border border-[#9ed1c1]'
                        : 'bg-[#8e3335] hover:bg-[#a63d40] text-[#ffd9d7]'
                    }`}
                  >
                    {dispatches[`${selectedIncident.id}_POLICE`] ? '✓ Security Dispatched' : 'Deploy Security Force'}
                  </motion.button>
                </div>

                {/* Action 2: Fire Brigade */}
                <div className="solid-card p-3 flex flex-col justify-between space-y-3">
                  <div className="flex items-center gap-2">
                    <Siren className="w-5 h-5 text-[#f5dfc0]" />
                    <div className="text-xs font-bold text-[#f5dfc0]">Fire Brigade & Suppression</div>
                  </div>
                  <p className="text-[10px] text-[#988f85] font-mono">
                    Notify municipal fire station and engage sector suppression protocols.
                  </p>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => openDispatchConfirmation(selectedIncident.id, 'FIRE', 'Municipal Fire Brigade & Foam Tender', '1 Fire Engine + Sector Water Tender')}
                    className={`w-full py-1.5 text-[11px] font-bold font-mono uppercase tracking-wider transition ${
                      dispatches[`${selectedIncident.id}_FIRE`]
                        ? 'bg-[#1d4f43] text-[#9ed1c1] border border-[#9ed1c1]'
                        : 'bg-[#f5dfc0] hover:bg-[#d8c3a5] text-[#3b2e19]'
                    }`}
                  >
                    {dispatches[`${selectedIncident.id}_FIRE`] ? '✓ Fire Dept Alerted' : 'Alert Fire Brigade'}
                  </motion.button>
                </div>

                {/* Action 3: Medical Response */}
                <div className="solid-card p-3 flex flex-col justify-between space-y-3">
                  <div className="flex items-center gap-2">
                    <Truck className="w-5 h-5 text-[#9ed1c1]" />
                    <div className="text-xs font-bold text-[#f5dfc0]">Emergency Medical (EMS)</div>
                  </div>
                  <p className="text-[10px] text-[#988f85] font-mono">
                    Dispatch trauma ambulance unit to incident coordinates.
                  </p>
                  <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => openDispatchConfirmation(selectedIncident.id, 'EMS', 'Emergency Medical Trauma Unit (EMS)', '1 Advanced Life Support (ALS) Ambulance')}
                    className={`w-full py-1.5 text-[11px] font-bold font-mono uppercase tracking-wider transition ${
                      dispatches[`${selectedIncident.id}_EMS`]
                        ? 'bg-[#1d4f43] text-[#9ed1c1] border border-[#9ed1c1]'
                        : 'bg-[#1C1B1B] hover:bg-[#2A2A2A] text-[#cfc5b9] border border-[#353534]'
                    }`}
                  >
                    {dispatches[`${selectedIncident.id}_EMS`] ? '✓ Ambulance Dispatched' : 'Request Ambulance'}
                  </motion.button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-[#555555] font-mono text-sm">
            Select an incident from the threat stack to review tactical response options.
          </div>
        )}
      </div>

      {/* Two-Step Tactical Dispatch Confirmation Modal */}
      <AnimatePresence>
        {pendingDispatch && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
            onClick={() => setPendingDispatch(null)}
          >
            <motion.div
              initial={{ scale: 0.94, opacity: 0, y: 15 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.94, opacity: 0, y: 15 }}
              transition={{ type: 'spring', stiffness: 380, damping: 28 }}
              className="solid-panel w-full max-w-lg p-5 border border-[#ffd9d7]/50 bg-[#141414] shadow-2xl space-y-4"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between border-b border-[#2A2A2A] pb-3">
                <div className="flex items-center gap-2">
                  <span className="material-symbols-outlined text-[#ffd9d7]">warning</span>
                  <div>
                    <h3 className="text-sm font-bold text-[#f5dfc0] font-mono uppercase">
                      Confirm Emergency Dispatch Transmission
                    </h3>
                    <p className="text-[11px] text-[#988f85] font-mono">
                      Two-Step Protocol Authorization • Incident #EV-{String(pendingDispatch.eventId).padStart(4, '0')}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setPendingDispatch(null)}
                  className="text-[#988f85] hover:text-[#f5dfc0]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Dispatch Details Grid */}
              <div className="space-y-2 bg-[#191919] p-3.5 border border-[#2A2A2A] font-mono text-xs">
                <div className="flex justify-between border-b border-[#262626] pb-1.5">
                  <span className="text-[#988f85]">Target Incident</span>
                  <span className="text-[#f5dfc0] font-bold">
                    {selectedIncident?.event_type} (#EV-{String(pendingDispatch.eventId).padStart(4, '0')})
                  </span>
                </div>
                <div className="flex justify-between border-b border-[#262626] pb-1.5">
                  <span className="text-[#988f85]">Target Location</span>
                  <span className="text-[#cfc5b9]">{getCameraName(selectedIncident?.camera_id)}</span>
                </div>
                <div className="flex justify-between border-b border-[#262626] pb-1.5">
                  <span className="text-[#988f85]">Target Coordinates</span>
                  <span className="text-[#9ed1c1]">{getCameraGps(selectedIncident?.camera_id)}</span>
                </div>
                <div className="flex justify-between border-b border-[#262626] pb-1.5">
                  <span className="text-[#988f85]">Deployment Action</span>
                  <span className="text-[#ffd9d7] font-bold">{pendingDispatch.actionTitle}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#988f85]">Allocated Units</span>
                  <span className="text-[#f5dfc0] font-bold">{pendingDispatch.units}</span>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setPendingDispatch(null)}
                  className="px-4 py-2 bg-[#1C1B1B] hover:bg-[#2A2A2A] text-[#cfc5b9] border border-[#333333] text-xs font-mono font-bold"
                >
                  Abort
                </button>
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={confirmDispatch}
                  className="px-5 py-2 bg-[#8e3335] hover:bg-[#a63d40] text-[#ffd9d7] text-xs font-mono font-bold uppercase tracking-wider"
                >
                  Authorize & Transmit Dispatch
                </motion.button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
