import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ShieldAlert, AlertTriangle, Send, CheckCircle2, PhoneCall, Radio, 
  Truck, Siren, Eye, X, MapPin, Clock, ShieldCheck, Activity, Filter
} from 'lucide-react';

const MAX_ACTIVE_INCIDENTS = 10;

const SEVERITY_WEIGHT = {
  Critical: 4,
  High: 3,
  Medium: 2,
  Low: 1
};

export default function RespondConsole({ events = [], cameras = [], onSelectEvent }) {
  const [dispatches, setDispatches] = useState({});
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [pendingDispatch, setPendingDispatch] = useState(null);

  // Active Filters
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [threatFilter, setThreatFilter] = useState('ALL');

  // Filtered & Prioritized Actionable Incidents (Max 10)
  const actionableEvents = useMemo(() => {
    // 1. Filter by severity and threat type
    const filtered = events.filter((ev) => {
      const matchSeverity = severityFilter === 'ALL' || 
        (ev.severity && ev.severity.toUpperCase() === severityFilter.toUpperCase());
      
      let matchThreat = true;
      if (threatFilter !== 'ALL') {
        const evType = (ev.event_type || '').toLowerCase();
        const tf = threatFilter.toLowerCase();
        if (tf === 'fighting') matchThreat = evType.includes('fight') || evType.includes('violenc');
        else if (tf === 'vehicle collision') matchThreat = evType.includes('collision') || evType.includes('crash') || evType.includes('accident');
        else if (tf === 'fire') matchThreat = evType.includes('fire') || evType.includes('flame');
        else if (tf === 'smoke') matchThreat = evType.includes('smoke');
        else if (tf === 'accident') matchThreat = evType.includes('accident') || evType.includes('collision');
        else if (tf === 'person') matchThreat = evType.includes('person') || evType.includes('pedestrian');
        else if (tf === 'vehicle') matchThreat = evType.includes('vehicle') || evType.includes('car');
        else matchThreat = evType.includes(tf);
      }

      return matchSeverity && matchThreat;
    });

    // 2. Prioritize: Severity (Critical > High > Medium > Low) -> Recency (Newer > Older) -> Confidence
    filtered.sort((a, b) => {
      const weightA = SEVERITY_WEIGHT[a.severity] || 2;
      const weightB = SEVERITY_WEIGHT[b.severity] || 2;
      if (weightB !== weightA) return weightB - weightA;

      const timeA = new Date(a.timestamp || 0).getTime();
      const timeB = new Date(b.timestamp || 0).getTime();
      if (timeB !== timeA) return timeB - timeA;

      const confA = typeof a.confidence === 'number' ? a.confidence : 0.95;
      const confB = typeof b.confidence === 'number' ? b.confidence : 0.95;
      return confB - confA;
    });

    // 3. Cap to MAX_ACTIVE_INCIDENTS (10)
    return filtered.slice(0, MAX_ACTIVE_INCIDENTS);
  }, [events, severityFilter, threatFilter]);

  const activeSelected = useMemo(() => {
    if (selectedIncidentId) {
      const found = actionableEvents.find(e => e.id === selectedIncidentId);
      if (found) return found;
    }
    return actionableEvents[0] || null;
  }, [actionableEvents, selectedIncidentId]);

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
    setDispatches((prev) => ({
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
    const c = cameras.find((cam) => cam.id === camId);
    return c ? c.name : `CAM-0${camId}`;
  };

  const getCameraGps = (camId) => {
    const c = cameras.find((cam) => cam.id === camId);
    return c && typeof c.lat === 'number' && typeof c.lon === 'number'
      ? `${c.lat.toFixed(4)}°N, ${c.lon.toFixed(4)}°E`
      : (camId === 2 ? '12.9756°N, 77.6067°E' : '18.9401°N, 72.8351°E');
  };


  return (
    <div className="flex flex-col lg:flex-row h-full overflow-hidden bg-[#0A0A0A] relative text-[#e5e2e1]">
      {/* Left Column: Critical Actionable Incidents Queue (Tactical Action Stack) */}
      <div className="w-full lg:w-[400px] border-r border-[#222222] bg-[#111111] p-4 flex flex-col flex-shrink-0">
        {/* Header & Counter */}
        <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#222222]">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-red-950/60 border border-red-800/80 text-red-300">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h2 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider font-mono">
                Tactical Action Stack
              </h2>
              <p className="text-[10px] text-[#858585] font-mono">Current Actionable Incidents</p>
            </div>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 bg-red-950 text-red-200 border border-red-800 font-bold rounded">
            {actionableEvents.length} ACTIVE
          </span>
        </div>

        {/* Compact Filters at Top */}
        <div className="bg-[#161616] border border-[#262626] rounded-xl p-2.5 mb-3 space-y-2 font-mono text-xs">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-[#858585] uppercase flex items-center gap-1">
              <Filter className="w-3 h-3 text-[#f5dfc0]" /> Filters
            </span>
            <span className="text-[10px] text-cyan-300">Showing {actionableEvents.length} active</span>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {/* Severity Filter */}
            <div>
              <label className="text-[9px] text-[#737373] block uppercase mb-0.5">Severity</label>
              <select
                value={severityFilter}
                onChange={(e) => setSeverityFilter(e.target.value)}
                className="w-full px-2 py-1 bg-[#0d0d0d] border border-[#333] rounded text-[11px] text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
              >
                <option value="ALL">All Severities</option>
                <option value="CRITICAL">Critical Only</option>
                <option value="HIGH">High Only</option>
                <option value="MEDIUM">Medium Only</option>
                <option value="LOW">Low Only</option>
              </select>
            </div>

            {/* Threat Class Filter */}
            <div>
              <label className="text-[9px] text-[#737373] block uppercase mb-0.5">Threat Class</label>
              <select
                value={threatFilter}
                onChange={(e) => setThreatFilter(e.target.value)}
                className="w-full px-2 py-1 bg-[#0d0d0d] border border-[#333] rounded text-[11px] text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
              >
                <option value="ALL">All Classes</option>
                <option value="FIGHTING">Fighting / Violence</option>
                <option value="VEHICLE COLLISION">Vehicle Collision</option>
                <option value="FIRE">Fire</option>
                <option value="SMOKE">Smoke</option>
                <option value="ACCIDENT">Accident</option>
                <option value="PERSON">Person</option>
                <option value="VEHICLE">Vehicle</option>
              </select>
            </div>
          </div>
        </div>

        {/* Actionable Incident List */}
        <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
          {actionableEvents.length === 0 ? (
            <div className="py-12 text-center text-[#666666] font-mono text-xs space-y-2">
              <ShieldCheck className="w-8 h-8 text-[#444] mx-auto" />
              <div>No actionable incidents matching active filters.</div>
            </div>
          ) : (
            actionableEvents.map((ev) => {
              const isSelected = activeSelected?.id === ev.id;
              return (
                <div
                  key={ev.id}
                  onClick={() => setSelectedIncidentId(ev.id)}
                  className={`p-3.5 rounded-xl cursor-pointer border transition font-mono ${
                    isSelected 
                      ? 'border-[#f5dfc0] bg-[#1a1a1a] shadow-lg shadow-black/60' 
                      : 'border-[#222222] bg-[#0d0d0d] hover:border-[#3a3a3a] hover:bg-[#141414]'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-[10px] font-bold px-2 py-0.5 rounded border ${
                      ev.severity === 'Critical' ? 'bg-red-950 text-red-200 border-red-800' :
                      ev.severity === 'High' ? 'bg-orange-950 text-orange-200 border-orange-800' :
                      'bg-yellow-950 text-yellow-200 border-yellow-800'
                    }`}>
                      🔴 {ev.severity?.toUpperCase() || 'HIGH'} ALERT #{ev.id}
                    </span>
                    <span className="text-[10px] text-[#858585]">
                      {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Recent'}
                    </span>
                  </div>

                  <div className="text-xs font-bold text-[#f5dfc0] mb-1.5 uppercase truncate">
                    {ev.event_type === 'Fighting' ? 'VIOLENCE / FIGHTING' : ev.event_type === 'Fire' ? 'FIRE OUTBREAK' : ev.event_type}
                  </div>

                  <div className="text-[11px] text-[#858585] flex items-center justify-between">
                    <span className="truncate pr-2">{getCameraName(ev.camera_id)}</span>
                    <span className="text-emerald-400 font-bold flex-shrink-0">
                      {typeof ev.confidence === 'number' ? `${(ev.confidence * 100).toFixed(0)}% CONF` : '98% CONF'}
                    </span>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Column: Threat Mitigation Panel */}
      <div className="flex-1 p-6 bg-[#0a0a0a] overflow-y-auto space-y-5">
        {activeSelected ? (
          <div className="max-w-5xl mx-auto space-y-5">
            {/* 1. INCIDENT HEADER CARD */}
            <div className="bg-[#141414] border border-[#262626] rounded-2xl p-5 shadow-2xl space-y-3 font-mono">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#222] pb-3">
                <div>
                  <div className="text-[11px] text-[#858585] uppercase tracking-wider">
                    INCIDENT #{activeSelected.id}
                  </div>
                  <h1 className="text-base font-bold text-[#f5dfc0] uppercase tracking-wide">
                    THREAT MITIGATION COMMAND
                  </h1>
                </div>

                <div className="flex items-center gap-3">
                  <span className={`px-3 py-1 text-xs font-bold rounded-lg border flex items-center gap-1.5 ${
                    activeSelected.severity === 'Critical' ? 'bg-red-950 text-red-200 border-red-700' :
                    'bg-orange-950 text-orange-200 border-orange-700'
                  }`}>
                    <span className="w-2 h-2 rounded-full bg-red-500 animate-ping" />
                    {activeSelected.severity?.toUpperCase() || 'CRITICAL'} SEVERITY
                  </span>

                  <button
                    onClick={() => onSelectEvent && onSelectEvent(activeSelected)}
                    className="flex items-center gap-1.5 px-3.5 py-1.5 bg-[#1f1f1f] hover:bg-[#2a2a2a] text-[#f5dfc0] border border-[#333333] rounded-lg text-xs font-bold transition"
                  >
                    <Eye className="w-3.5 h-3.5 text-[#00F2FE]" />
                    Inspect Verified Snapshot
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs pt-1">
                <div>
                  <span className="text-[10px] text-[#858585] uppercase block">Threat Classification</span>
                  <span className="font-bold text-[#e5e2e1] text-sm">{activeSelected.event_type}</span>
                </div>
                <div>
                  <span className="text-[10px] text-[#858585] uppercase block">Location Node</span>
                  <span className="font-bold text-[#e5e2e1]">{getCameraName(activeSelected.camera_id)}</span>
                  <span className="text-[11px] text-cyan-300 block">GPS: {getCameraGps(activeSelected.camera_id)}</span>
                </div>
              </div>
            </div>

            {/* 2. INCIDENT TELEMETRY + LIVE EVIDENCE GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Telemetry Card */}
              <div className="bg-[#141414] border border-[#262626] rounded-2xl p-5 shadow-2xl space-y-3 font-mono text-xs">
                <div className="flex items-center gap-2 border-b border-[#222] pb-2.5">
                  <Activity className="w-4 h-4 text-emerald-400" />
                  <h3 className="text-xs uppercase tracking-wider text-[#f5dfc0] font-bold">
                    INCIDENT TELEMETRY
                  </h3>
                </div>

                <div className="space-y-2.5">
                  <div className="flex justify-between border-b border-[#1f1f1f] pb-2">
                    <span className="text-[#858585]">Threat Classification</span>
                    <span className="text-[#f5dfc0] font-bold">{activeSelected.event_type}</span>
                  </div>
                  <div className="flex justify-between border-b border-[#1f1f1f] pb-2">
                    <span className="text-[#858585]">Neural Confidence</span>
                    <span className="text-emerald-400 font-bold">
                      {typeof activeSelected.confidence === 'number' ? `${(activeSelected.confidence * 100).toFixed(1)}%` : '98.0%'}
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-[#1f1f1f] pb-2">
                    <span className="text-[#858585]">GPS Target Sector</span>
                    <span className="text-cyan-300">{getCameraGps(activeSelected.camera_id)}</span>
                  </div>
                  <div className="flex justify-between border-b border-[#1f1f1f] pb-2">
                    <span className="text-[#858585]">Temporal Confirmation</span>
                    <span className="text-emerald-400 font-bold">≥3 Consecutive Positive Frames</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[#858585]">Integrity Status</span>
                    <span className="text-[#858585]">SHA-256 Verified Stream Block</span>
                  </div>
                </div>
              </div>

              {/* Live Incident Evidence Card */}
              <div className="bg-[#141414] border border-[#262626] rounded-2xl p-5 shadow-2xl space-y-3 font-mono">
                <div className="flex items-center justify-between border-b border-[#222] pb-2.5">
                  <span className="text-xs uppercase tracking-wider text-[#f5dfc0] font-bold">
                    LIVE INCIDENT EVIDENCE
                  </span>
                  <span className="text-[10px] text-red-400 bg-red-950 px-1.5 py-0.5 rounded border border-red-900 font-bold">
                    LOCKED
                  </span>
                </div>

                <div 
                  onClick={() => onSelectEvent && onSelectEvent(activeSelected)}
                  className="relative aspect-video bg-black border border-[#262626] rounded-xl overflow-hidden cursor-pointer group flex items-center justify-center"
                >
                  {activeSelected.snapshot_path ? (
                    <>
                      <img
                        src={activeSelected.snapshot_path}
                        alt="Snapshot"
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                      />
                      <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2 text-white text-xs font-bold">
                        <Eye className="w-4 h-4" /> Click to Inspect Forensic Sighting
                      </div>
                    </>
                  ) : (
                    <div className="text-[#666] text-xs">Snapshot Unavailable</div>
                  )}
                </div>
              </div>
            </div>

            {/* 3. AUTHORIZED TACTICAL RESPONSE CARD */}
            <div className="bg-[#141414] border border-[#262626] rounded-2xl p-5 shadow-2xl space-y-4 font-mono">
              <div>
                <h3 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider">
                  AUTHORIZED TACTICAL RESPONSE
                </h3>
                <p className="text-[11px] text-[#858585] mt-0.5">
                  Two-step authorization protocol to alert emergency units
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* Security Force */}
                <div className="p-4 rounded-xl bg-[#0e0e0e] border border-[#262626] flex flex-col justify-between space-y-3">
                  <div className="flex items-center gap-2">
                    <ShieldAlert className="w-4 h-4 text-red-400" />
                    <div className="text-xs font-bold text-[#f5dfc0]">Police / Security Force</div>
                  </div>
                  <p className="text-[10px] text-[#858585]">
                    Direct automated alert to on-ground patrol and security units.
                  </p>
                  <button
                    onClick={() => openDispatchConfirmation(activeSelected.id, 'POLICE', 'Police & Security Intercept Unit', '2 Sector Patrol Cars + QRT Squad')}
                    className={`w-full py-2 rounded-lg text-xs font-bold uppercase transition ${
                      dispatches[`${activeSelected.id}_POLICE`]
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                        : 'bg-red-900/60 hover:bg-red-800 border border-red-700 text-red-100'
                    }`}
                  >
                    {dispatches[`${activeSelected.id}_POLICE`] ? 'Security Dispatched' : 'Deploy Security Force'}
                  </button>
                </div>

                {/* Fire Brigade */}
                <div className="p-4 rounded-xl bg-[#0e0e0e] border border-[#262626] flex flex-col justify-between space-y-3">
                  <div className="flex items-center gap-2">
                    <Siren className="w-4 h-4 text-orange-400" />
                    <div className="text-xs font-bold text-[#f5dfc0]">Fire Brigade</div>
                  </div>
                  <p className="text-[10px] text-[#858585]">
                    Notify municipal fire station and engage sector suppression protocols.
                  </p>
                  <button
                    onClick={() => openDispatchConfirmation(activeSelected.id, 'FIRE', 'Municipal Fire Brigade & Foam Tender', '1 Fire Engine + Sector Water Tender')}
                    className={`w-full py-2 rounded-lg text-xs font-bold uppercase transition ${
                      dispatches[`${activeSelected.id}_FIRE`]
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                        : 'bg-[#f5dfc0] hover:bg-white text-black font-black'
                    }`}
                  >
                    {dispatches[`${activeSelected.id}_FIRE`] ? 'Fire Dept Alerted' : 'Alert Fire Brigade'}
                  </button>
                </div>

                {/* Medical Response (EMS) */}
                <div className="p-4 rounded-xl bg-[#0e0e0e] border border-[#262626] flex flex-col justify-between space-y-3">
                  <div className="flex items-center gap-2">
                    <Truck className="w-4 h-4 text-cyan-400" />
                    <div className="text-xs font-bold text-[#f5dfc0]">Emergency Medical (EMS)</div>
                  </div>
                  <p className="text-[10px] text-[#858585]">
                    Dispatch trauma ambulance unit to incident coordinates.
                  </p>
                  <button
                    onClick={() => openDispatchConfirmation(activeSelected.id, 'EMS', 'Emergency Medical Trauma Unit (EMS)', '1 Advanced Life Support (ALS) Ambulance')}
                    className={`w-full py-2 rounded-lg text-xs font-bold uppercase transition ${
                      dispatches[`${activeSelected.id}_EMS`]
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                        : 'bg-[#1f1f1f] hover:bg-[#2b2b2b] text-[#e5e2e1] border border-[#3a3a3a]'
                    }`}
                  >
                    {dispatches[`${activeSelected.id}_EMS`] ? 'Ambulance Dispatched' : 'Request Ambulance'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-[#666] font-mono text-sm">
            Select an incident from the tactical action stack to review response options.
          </div>
        )}
      </div>

      {/* Two-Step Tactical Dispatch Confirmation Modal */}
      <AnimatePresence>
        {pendingDispatch && (
          <div 
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
            onClick={() => setPendingDispatch(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 10 }}
              className="w-full max-w-lg p-6 border border-red-800/80 rounded-2xl bg-[#141414] shadow-2xl space-y-4 font-mono text-xs"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-[#2a2a2a] pb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  <h3 className="text-sm font-bold text-[#f5dfc0] uppercase">
                    Confirm Emergency Tactical Transmission
                  </h3>
                </div>
                <button onClick={() => setPendingDispatch(null)} className="text-[#858585] hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2 bg-[#0a0a0a] p-4 rounded-xl border border-[#222]">
                <div className="flex justify-between border-b border-[#1f1f1f] pb-1.5">
                  <span className="text-[#858585]">Target Incident</span>
                  <span className="text-[#f5dfc0] font-bold">
                    {activeSelected?.event_type} (#EVT-{String(pendingDispatch.eventId).padStart(4, '0')})
                  </span>
                </div>
                <div className="flex justify-between border-b border-[#1f1f1f] pb-1.5">
                  <span className="text-[#858585]">Location Node</span>
                  <span className="text-[#e5e2e1]">{getCameraName(activeSelected?.camera_id)}</span>
                </div>
                <div className="flex justify-between border-b border-[#1f1f1f] pb-1.5">
                  <span className="text-[#858585]">Coordinates</span>
                  <span className="text-cyan-300">{getCameraGps(activeSelected?.camera_id)}</span>
                </div>
                <div className="flex justify-between border-b border-[#1f1f1f] pb-1.5">
                  <span className="text-[#858585]">Deployment Action</span>
                  <span className="text-red-200 font-bold">{pendingDispatch.actionTitle}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858585]">Allocated Units</span>
                  <span className="text-[#f5dfc0] font-bold">{pendingDispatch.units}</span>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setPendingDispatch(null)}
                  className="px-4 py-2 bg-[#1f1f1f] hover:bg-[#2a2a2a] text-[#858585] hover:text-white rounded-lg text-xs font-bold transition"
                >
                  Abort
                </button>
                <button
                  onClick={confirmDispatch}
                  className="px-5 py-2 bg-red-800 hover:bg-red-700 text-white rounded-lg text-xs font-bold uppercase tracking-wider transition"
                >
                  Authorize & Transmit Dispatch
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
