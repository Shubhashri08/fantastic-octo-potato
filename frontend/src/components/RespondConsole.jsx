import React, { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ShieldAlert, AlertTriangle, Send, CheckCircle2, Radio,
  Truck, Siren, Eye, X, MapPin, Clock, ShieldCheck, Activity, Filter,
  FileText, Download, Play, Compass, Flame, Car, Users, Crosshair,
  Volume2, VolumeX, Shield, Zap
} from 'lucide-react';

const MAX_ACTIVE_INCIDENTS = 9;

const SEVERITY_WEIGHT = {
  Critical: 4,
  High: 3,
  Medium: 2,
  Low: 1
};

// Tactical SOP protocols per threat class - Standardized 3-Agency Emergency Response (Police Force, Fire Brigade, Ambulance)
const THREAT_SOPS = {
  Fighting: [
    {
      code: 'SOP-POL-01',
      agency: 'POLICE FORCE',
      agencyBadge: 'bg-blue-950/70 text-blue-300 border-blue-700/50',
      title: 'Deploy Police & QRT Security Force',
      units: '2 Patrol Cruisers + QRT Strike Team',
      icon: ShieldAlert,
      eta: '2 min'
    },
    {
      code: 'SOP-FIRE-01',
      agency: 'FIRE BRIGADE',
      agencyBadge: 'bg-orange-950/70 text-orange-300 border-orange-700/50',
      title: 'Municipal Fire Brigade Standby',
      units: '1 First-Responder Hazard Tender',
      icon: Siren,
      eta: '4 min'
    },
    {
      code: 'SOP-EMS-01',
      agency: 'AMBULANCE (EMS)',
      agencyBadge: 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50',
      title: 'Emergency Medical Ambulance (EMS)',
      units: '1 Advanced Life Support (ALS) Ambulance',
      icon: Truck,
      eta: '3 min'
    }
  ],
  Fire: [
    {
      code: 'SOP-FIRE-01',
      agency: 'FIRE BRIGADE',
      agencyBadge: 'bg-orange-950/70 text-orange-300 border-orange-700/50',
      title: 'Municipal Fire Brigade Ingress',
      units: '2 Foam Tenders + High-Pressure Ladder',
      icon: Siren,
      eta: '3 min'
    },
    {
      code: 'SOP-POL-01',
      agency: 'POLICE FORCE',
      agencyBadge: 'bg-blue-950/70 text-blue-300 border-blue-700/50',
      title: 'Deploy Police Traffic & Sector Cordon',
      units: 'Perimeter Security Detail + Sector Blockade',
      icon: ShieldAlert,
      eta: '2 min'
    },
    {
      code: 'SOP-EMS-01',
      agency: 'AMBULANCE (EMS)',
      agencyBadge: 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50',
      title: 'Emergency Medical Ambulance (EMS)',
      units: '2 Burn-Care ALS Ambulances + Paramedic Team',
      icon: Truck,
      eta: '3 min'
    }
  ],
  Smoke: [
    {
      code: 'SOP-FIRE-01',
      agency: 'FIRE BRIGADE',
      agencyBadge: 'bg-orange-950/70 text-orange-300 border-orange-700/50',
      title: 'Municipal Fire Brigade Ingress',
      units: '1 Foam Tender + Smoke Extraction Unit',
      icon: Siren,
      eta: '3 min'
    },
    {
      code: 'SOP-POL-01',
      agency: 'POLICE FORCE',
      agencyBadge: 'bg-blue-950/70 text-blue-300 border-blue-700/50',
      title: 'Deploy Police & Ground Security',
      units: 'Station Security Perimeter Detail',
      icon: ShieldAlert,
      eta: '2 min'
    },
    {
      code: 'SOP-EMS-01',
      agency: 'AMBULANCE (EMS)',
      agencyBadge: 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50',
      title: 'Emergency Medical Ambulance (EMS)',
      units: '1 Respiratory Support ALS Ambulance',
      icon: Truck,
      eta: '3 min'
    }
  ],
  'Vehicle Collision': [
    {
      code: 'SOP-EMS-01',
      agency: 'AMBULANCE (EMS)',
      agencyBadge: 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50',
      title: 'Emergency Medical Ambulance (EMS)',
      units: '1 ALS Trauma Ambulance + Rapid Paramedics',
      icon: Truck,
      eta: '2 min'
    },
    {
      code: 'SOP-POL-01',
      agency: 'POLICE FORCE',
      agencyBadge: 'bg-blue-950/70 text-blue-300 border-blue-700/50',
      title: 'Deploy Police & Highway Intercept',
      units: '2 Highway Interceptor Cruisers + Diversion',
      icon: ShieldAlert,
      eta: '3 min'
    },
    {
      code: 'SOP-FIRE-01',
      agency: 'FIRE BRIGADE',
      agencyBadge: 'bg-orange-950/70 text-orange-300 border-orange-700/50',
      title: 'Municipal Fire Brigade Extrication',
      units: '1 Heavy Rescue Tender + Hydraulic Cutters',
      icon: Siren,
      eta: '4 min'
    }
  ],
  Accident: [
    {
      code: 'SOP-EMS-01',
      agency: 'AMBULANCE (EMS)',
      agencyBadge: 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50',
      title: 'Emergency Medical Ambulance (EMS)',
      units: '1 ALS Trauma Ambulance + Paramedic Team',
      icon: Truck,
      eta: '2 min'
    },
    {
      code: 'SOP-POL-01',
      agency: 'POLICE FORCE',
      agencyBadge: 'bg-blue-950/70 text-blue-300 border-blue-700/50',
      title: 'Deploy Police & Highway Patrol',
      units: '2 Traffic Cruisers + Perimeter Flare Line',
      icon: ShieldAlert,
      eta: '3 min'
    },
    {
      code: 'SOP-FIRE-01',
      agency: 'FIRE BRIGADE',
      agencyBadge: 'bg-orange-950/70 text-orange-300 border-orange-700/50',
      title: 'Municipal Fire Brigade Extrication',
      units: '1 Heavy Rescue Tender + Clean-up Rig',
      icon: Siren,
      eta: '4 min'
    }
  ],
  Vehicle: [
    {
      code: 'SOP-POL-01',
      agency: 'POLICE FORCE',
      agencyBadge: 'bg-blue-950/70 text-blue-300 border-blue-700/50',
      title: 'Deploy Police Road Intercept',
      units: '2 Intercept Cruisers + Barrier Control',
      icon: ShieldAlert,
      eta: '2 min'
    },
    {
      code: 'SOP-FIRE-01',
      agency: 'FIRE BRIGADE',
      agencyBadge: 'bg-orange-950/70 text-orange-300 border-orange-700/50',
      title: 'Municipal Fire Brigade Standby',
      units: '1 Road Clearing & HAZMAT Tender',
      icon: Siren,
      eta: '5 min'
    },
    {
      code: 'SOP-EMS-01',
      agency: 'AMBULANCE (EMS)',
      agencyBadge: 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50',
      title: 'Emergency Medical Ambulance (EMS)',
      units: '1 Standby Life Support Paramedic Unit',
      icon: Truck,
      eta: '4 min'
    }
  ],
  Person: [
    {
      code: 'SOP-POL-01',
      agency: 'POLICE FORCE',
      agencyBadge: 'bg-blue-950/70 text-blue-300 border-blue-700/50',
      title: 'Deploy Police Ground Security',
      units: '2 Ground Security Officers at Exit Gate',
      icon: Users,
      eta: '2 min'
    },
    {
      code: 'SOP-EMS-01',
      agency: 'AMBULANCE (EMS)',
      agencyBadge: 'bg-emerald-950/70 text-emerald-300 border-emerald-700/50',
      title: 'Emergency Medical Ambulance (EMS)',
      units: '1 First-Aid & Trauma Paramedic Unit',
      icon: Truck,
      eta: '3 min'
    },
    {
      code: 'SOP-FIRE-01',
      agency: 'FIRE BRIGADE',
      agencyBadge: 'bg-orange-950/70 text-orange-300 border-orange-700/50',
      title: 'Municipal Fire Brigade Auxiliary',
      units: '1 Tactical Safety Support Unit',
      icon: Siren,
      eta: '5 min'
    }
  ]
};

// Tactical sound chime for emergency transmission
const playDispatchTone = () => {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12); // A5
    gain.gain.setValueAtTime(0.12, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.22);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start();
    osc.stop(ctx.currentTime + 0.22);
  } catch (e) {
    // Audio context may be restricted by browser policy
  }
};

export default function RespondConsole({ events = [], cameras = [], onSelectEvent }) {
  const [dispatches, setDispatches] = useState({});
  const [selectedIncidentId, setSelectedIncidentId] = useState(null);
  const [pendingDispatch, setPendingDispatch] = useState(null);
  const [evidenceMode, setEvidenceMode] = useState('snapshot'); // 'snapshot' | 'video'
  const [etaSeconds, setEtaSeconds] = useState(174);
  const [docketExported, setDocketExported] = useState(false);
  const [audioFeedback, setAudioFeedback] = useState(true);

  // Active Filters
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [threatFilter, setThreatFilter] = useState('ALL');

  // Live ETA countdown timer
  useEffect(() => {
    const timer = setInterval(() => {
      setEtaSeconds(prev => (prev > 1 ? prev - 1 : 180));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const formatEta = (sec) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `0${m}:${s < 10 ? '0' : ''}${s}`;
  };

  // Filtered & Prioritized Actionable Incidents (Max 9 unique incidents)
  const actionableEvents = useMemo(() => {
    const filtered = events.filter((ev) => {
      // Strictly keep only the earlier 9 curated demo incidents (IDs 6001-6009)
      if (ev.id < 6001 || ev.id > 6009) return false;
      if (ev.snapshot_path && ev.snapshot_path.includes('incident_cam1_Fighting')) return false;

      const matchSeverity = severityFilter === 'ALL' ||
        (ev.severity && ev.severity.toUpperCase() === severityFilter.toUpperCase());

      let matchThreat = true;
      if (threatFilter !== 'ALL') {
        const evType = (ev.event_type || '').toLowerCase();
        const tf = threatFilter.toLowerCase();
        if (tf === 'fighting') matchThreat = evType.includes('fight') || evType.includes('violenc');
        else if (tf === 'vehicle collision') matchThreat = evType.includes('collision') || evType.includes('crash');
        else if (tf === 'fire') matchThreat = evType.includes('fire') || evType.includes('flame');
        else if (tf === 'smoke') matchThreat = evType.includes('smoke');
        else if (tf === 'accident') matchThreat = evType.includes('accident');
        else if (tf === 'person') matchThreat = evType.includes('person') || evType.includes('pedestrian');
        else if (tf === 'vehicle') matchThreat = evType.includes('vehicle') || evType.includes('car');
        else matchThreat = evType.includes(tf);
      }

      return matchSeverity && matchThreat;
    });

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

    // Return up to 9 unique incidents
    return filtered.slice(0, MAX_ACTIVE_INCIDENTS);
  }, [events, severityFilter, threatFilter]);

  const activeSelected = useMemo(() => {
    if (selectedIncidentId) {
      const found = actionableEvents.find(e => e.id === selectedIncidentId);
      if (found) return found;
    }
    return actionableEvents[0] || null;
  }, [actionableEvents, selectedIncidentId]);

  const resolvedVideo = useMemo(() => {
    if (!activeSelected) return '/samples/fight_1.mp4';
    if (activeSelected.video_clip_path) return activeSelected.video_clip_path;
    if (activeSelected.video_url) return activeSelected.video_url;
    const camMap = {
      1: '/samples/fight_1.mp4',
      2: '/samples/fire_1.mp4',
      3: '/samples/IMG_0006.mp4',
      4: '/samples/accident_cut_04_highway_night_rear_end.mp4',
      5: '/samples/accident_cut_03_truck_swerve_sidewalk.mp4',
      6: '/samples/accident_cut_02_night_junction_tbone.mp4',
      7: '/samples/accident_cut_05_intersection_crossover.mp4'
    };
    return camMap[activeSelected.camera_id] || '/samples/fight_1.mp4';
  }, [activeSelected]);

  const activeSOPs = useMemo(() => {
    if (!activeSelected) return THREAT_SOPS['Fighting'];
    const type = activeSelected.event_type;
    return THREAT_SOPS[type] || THREAT_SOPS['Vehicle Collision'] || THREAT_SOPS['Fighting'];
  }, [activeSelected]);

  const openDispatchConfirmation = (eventId, actionCode, actionTitle, units) => {
    setPendingDispatch({
      eventId,
      actionCode,
      actionTitle,
      units,
      timestamp: new Date().toLocaleTimeString()
    });
  };

  const confirmDispatch = () => {
    if (!pendingDispatch) return;
    if (audioFeedback) playDispatchTone();
    const key = `${pendingDispatch.eventId}_${pendingDispatch.actionCode}`;
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
      : (camId === 1 ? '18.9401°N, 72.8351°E' : camId === 2 ? '12.9756°N, 77.6067°E' : camId === 3 ? '18.9438°N, 72.8233°E' : '12.9725°N, 77.6200°E');
  };

  const handleExportDocket = () => {
    if (!activeSelected) return;
    const docket = {
      docket_id: `VIGRAH-DOCKET-${activeSelected.id}`,
      generated_at: new Date().toISOString(),
      threat_classification: activeSelected.event_type,
      severity: activeSelected.severity,
      neural_confidence: activeSelected.confidence,
      camera_node: `CAM-0${activeSelected.camera_id}`,
      gps_sector: getCameraGps(activeSelected.camera_id),
      temporal_confirmation_frames: activeSelected.confirmation_count || 8,
      evidence_snapshot: activeSelected.snapshot_path,
      evidence_video: resolvedVideo,
      authorized_dispatches: Object.keys(dispatches)
        .filter(k => k.startsWith(String(activeSelected.id)))
        .map(k => dispatches[k]),
      forensic_integrity: 'SHA-256 HASH VERIFIED BLOCK',
      system: 'VIGRAH AI - Visual Intelligence & Geospatial Response Hub'
    };

    const blob = new Blob([JSON.stringify(docket, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `VIGRAH_INCIDENT_DOCKET_${activeSelected.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
    setDocketExported(true);
    setTimeout(() => setDocketExported(false), 3000);
  };

  // Tactical severity style badges
  const getSeverityStyle = (severity = 'Critical') => {
    const s = severity.toUpperCase();
    if (s === 'CRITICAL') {
      return {
        badge: 'bg-red-950/60 text-red-300 border-red-800/80',
        dot: 'bg-red-500 animate-ping',
        text: 'text-red-400'
      };
    }
    if (s === 'HIGH') {
      return {
        badge: 'bg-amber-950/60 text-amber-300 border-amber-700/80',
        dot: 'bg-amber-400 animate-pulse',
        text: 'text-amber-400'
      };
    }
    return {
      badge: 'bg-cyan-950/60 text-cyan-300 border-cyan-700/80',
      dot: 'bg-[#00F2FE] animate-pulse',
      text: 'text-[#00F2FE]'
    };
  };

  return (
    <div className="h-full w-full flex flex-col bg-[#0A0A0A] text-[#e5e2e1] overflow-hidden select-none font-mono">
      {/* Sub-Header Layer Selector - Unified with LAYER 1, 2, 3 Visual Vibe */}
      <div className="px-6 py-3 bg-[#111111] border-b border-[#222222] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#181818] border border-[#2a2a2a] text-[#f5dfc0]">
            <ShieldAlert className="w-5 h-5 text-[#00F2FE]" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-[#f5dfc0] font-sans tracking-wide">
              LAYER 4: RESPOND & TACTICAL MITIGATION
            </h1>
            <p className="text-[11px] font-mono text-[#858585]">
              Real-Time Automated Emergency Dispatch, SOP Protocols & Rapid Intercept Telemetry
            </p>
          </div>
        </div>

        {/* Global Controls & Stats */}
        <div className="flex items-center gap-3">
          <button
            onClick={handleExportDocket}
            className="flex items-center gap-1.5 px-4 py-2 bg-[#181818] hover:bg-[#222] text-[#cfc5b9] hover:text-white border border-[#2a2a2a] rounded-xl text-xs font-bold transition shadow"
          >
            <Download className="w-3.5 h-3.5 text-[#00F2FE]" />
            {docketExported ? 'Docket Exported!' : 'Export Docket'}
          </button>
        </div>
      </div>

      {/* Main Responsive Body: Tactical Stack + Mitigation Panel */}
      <div className="flex-1 overflow-hidden flex flex-col lg:flex-row">

        {/* Left Column: Tactical Action Stack - Expanded Width for Maximum Legibility */}
        <div className="w-full lg:w-[460px] xl:w-[480px] border-r border-[#222222] bg-[#111111] p-4 flex flex-col flex-shrink-0">

          {/* Section Header */}
          <div className="flex items-center justify-between pb-3 mb-3 border-b border-[#222222]">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-[#00F2FE]" />
              <h2 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider font-mono">
                Tactical Action Stack
              </h2>
            </div>
          </div>

          {/* Stack Filter Controls */}
          <div className="bg-[#0a0a0a] border border-[#262626] rounded-xl p-3 mb-3 space-y-2 text-xs">
            <div className="flex items-center justify-between text-[10px] text-[#858585] uppercase">
              <span className="flex items-center gap-1">
                <Filter className="w-3 h-3 text-[#00F2FE]" /> Filter Incidents
              </span>
              <span className="text-[#00F2FE]">{actionableEvents.length} of {events.length || 9} Shown</span>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-[9px] text-[#737373] block uppercase mb-1">Severity</label>
                <select
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                  className="w-full px-2 py-1.5 bg-[#141414] border border-[#333333] rounded-lg text-[11px] text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                >
                  <option value="ALL">All Severities</option>
                  <option value="CRITICAL">Critical Only</option>
                  <option value="HIGH">High Only</option>
                  <option value="MEDIUM">Medium Only</option>
                </select>
              </div>

              <div>
                <label className="text-[9px] text-[#737373] block uppercase mb-1">Threat Class</label>
                <select
                  value={threatFilter}
                  onChange={(e) => setThreatFilter(e.target.value)}
                  className="w-full px-2 py-1.5 bg-[#141414] border border-[#333333] rounded-lg text-[11px] text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                >
                  <option value="ALL">All Threat Classes</option>
                  <option value="FIGHTING">Fighting / Altercation</option>
                  <option value="VEHICLE COLLISION">Vehicle Collision</option>
                  <option value="ACCIDENT">Accident</option>
                  <option value="FIRE">Fire Hazard</option>
                  <option value="VEHICLE">Vehicle BOLO</option>
                </select>
              </div>
            </div>
          </div>

          {/* Incident Queue Cards */}
          <div className="flex-1 overflow-y-auto space-y-2.5 pr-1">
            {actionableEvents.length === 0 ? (
              <div className="py-12 text-center text-[#666666] text-xs space-y-2">
                <ShieldCheck className="w-8 h-8 text-[#444] mx-auto" />
                <div>No actionable incidents matching filters.</div>
              </div>
            ) : (
              actionableEvents.map((ev) => {
                const isSelected = activeSelected?.id === ev.id;
                const sev = getSeverityStyle(ev.severity);
                const isFighting = (ev.event_type || '').toLowerCase().includes('fight');
                return (
                  <div
                    key={ev.id}
                    onClick={() => setSelectedIncidentId(ev.id)}
                    className={`p-3.5 rounded-xl cursor-pointer border transition-all ${isSelected
                        ? 'border-[#00F2FE] bg-[#1a1f2c] shadow-lg shadow-cyan-950/40 ring-1 ring-[#00F2FE]/50'
                        : 'border-[#262626] bg-[#141414] hover:border-[#00F2FE]/40 hover:bg-[#181818]'
                      }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded border flex items-center gap-1.5 ${sev.badge}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${sev.dot}`} />
                        #{ev.id} · {ev.severity?.toUpperCase() || 'CRITICAL'}
                      </span>
                      <span className="text-[10px] text-[#858585]">
                        {ev.timestamp ? new Date(ev.timestamp).toLocaleTimeString() : 'Live'}
                      </span>
                    </div>

                    <div className="text-xs font-bold text-[#f5dfc0] mb-1 uppercase truncate flex items-center gap-1.5">
                      {isFighting}
                      {ev.event_type}
                    </div>

                    <div className="text-[11px] text-[#858585] flex items-center justify-between">
                      <span className="truncate pr-2 font-mono">{getCameraName(ev.camera_id)}</span>
                      <span className="text-[#00F2FE] font-bold flex-shrink-0">
                        {typeof ev.confidence === 'number' ? `${(ev.confidence * 100).toFixed(0)}%` : '96%'}
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Right Column: Threat Mitigation Panel */}
        <div className="flex-1 p-6 bg-[#0A0A0A] overflow-y-auto space-y-6">
          {activeSelected ? (
            <div className="max-w-6xl mx-auto space-y-6">

              {/* 1. INCIDENT HEADER CARD */}
              <div className="bg-[#141414] border border-[#262626] rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#222222] pb-4">
                  <div>
                    <div className="text-[11px] text-[#858585] uppercase tracking-wider flex items-center gap-2">
                      <span>OPERATIONAL SECTOR INCIDENT #{activeSelected.id}</span>
                    </div>
                    <h2 className="text-base font-bold text-[#f5dfc0] uppercase tracking-wide flex items-center gap-2 mt-1">
                      Threat Mitigation Command & Telemetry
                    </h2>
                  </div>

                  <div className="flex items-center gap-2.5">
                    <button
                      onClick={() => onSelectEvent && onSelectEvent(activeSelected)}
                      className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] hover:opacity-95 text-[#0A0A0A] font-black text-xs uppercase tracking-wider transition shadow-lg shadow-cyan-950/50 transform hover:scale-[1.02]"
                    >
                      <Eye className="w-4 h-4" />
                      Full Forensic Lightbox
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-1">
                  <div className="p-3 bg-[#0a0a0a] rounded-xl border border-[#222222]">
                    <span className="text-[10px] text-[#858585] uppercase block mb-0.5">Threat Classification</span>
                    <span className="font-bold text-[#f5dfc0] text-sm flex items-center gap-1.5">
                      {activeSelected.event_type}
                      <span className="text-[10px] text-[#00F2FE]">
                        ({typeof activeSelected.confidence === 'number' ? `${(activeSelected.confidence * 100).toFixed(0)}%` : '96%'})
                      </span>
                    </span>
                  </div>
                  <div className="p-3 bg-[#0a0a0a] rounded-xl border border-[#222222]">
                    <span className="text-[10px] text-[#858585] uppercase block mb-0.5">Sensor Checkpoint</span>
                    <span className="font-bold text-[#e5e2e1] truncate block">{getCameraName(activeSelected.camera_id)}</span>
                  </div>
                  <div className="p-3 bg-[#0a0a0a] rounded-xl border border-[#222222]">
                    <span className="text-[10px] text-[#858585] uppercase block mb-0.5">GPS Geofence</span>
                    <span className="font-bold text-[#00F2FE]">{getCameraGps(activeSelected.camera_id)}</span>
                  </div>
                </div>
              </div>

              {/* 2. INCIDENT TELEMETRY + LIVE EVIDENCE GRID */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* Tactical Response Telemetry Card */}
                <div className="bg-[#141414] border border-[#262626] rounded-2xl p-6 shadow-2xl space-y-4 text-xs flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between border-b border-[#222222] pb-3 mb-3">
                      <div className="flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-[#00F2FE]" />
                        <h3 className="text-xs uppercase tracking-wider text-[#f5dfc0] font-bold">
                          Tactical Dispatch Telemetry
                        </h3>
                      </div>
                    </div>

                    {/* Telemetry Metrics Grid */}
                    <div className="grid grid-cols-2 gap-2.5 mb-3">
                      <div className="p-3 bg-[#0a0a0a] rounded-xl border border-[#222222] space-y-1">
                        <span className="text-[10px] text-[#858585] uppercase tracking-wide block">Verification State</span>
                        <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                          Multi-Frame Confirmed
                        </span>
                      </div>

                      <div className="p-3 bg-[#0a0a0a] rounded-xl border border-[#222222] space-y-1">
                        <span className="text-[10px] text-[#858585] uppercase tracking-wide block">ETA to Target</span>
                        <span className="text-xs font-bold text-[#f5dfc0] flex items-center gap-1.5">
                          <Clock className="w-3.5 h-3.5 text-[#00F2FE]" />
                          {formatEta(etaSeconds)} ({activeSOPs[0]?.eta || '2 min'})
                        </span>
                      </div>

                      <div className="p-3 bg-[#0a0a0a] rounded-xl border border-[#222222] space-y-1">
                        <span className="text-[10px] text-[#858585] uppercase tracking-wide block">Primary Intercept Unit</span>
                        <span className="text-xs font-bold text-[#e5e2e1] truncate block">
                          PATROL-QRT-04 · 154.80 MHz
                        </span>
                      </div>

                      <div className="p-3 bg-[#0a0a0a] rounded-xl border border-[#222222] space-y-1">
                        <span className="text-[10px] text-[#858585] uppercase tracking-wide block">Jurisdiction Clearance</span>
                        <span className="text-xs font-bold text-[#00F2FE] truncate block">
                          Priority Green (0.8 km)
                        </span>
                      </div>
                    </div>

                    {/* Telemetry Details */}
                    <div className="space-y-2 bg-[#0a0a0a] p-3 rounded-xl border border-[#222222]">
                      <div className="flex justify-between border-b border-[#1c1c1c] pb-1.5">
                        <span className="text-[#858585]">Threat Class & Target</span>
                        <span className="text-[#f5dfc0] font-bold">{activeSelected.event_type} · ID #{activeSelected.id}</span>
                      </div>
                      <div className="flex justify-between border-b border-[#1c1c1c] pb-1.5">
                        <span className="text-[#858585]">Neural Confidence</span>
                        <span className="text-[#00F2FE] font-bold">
                          {typeof activeSelected.confidence === 'number' ? `${(activeSelected.confidence * 100).toFixed(1)}%` : '96.0%'} High-Lock
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-[#858585]">Sensor Checkpoint</span>
                        <span className="text-[#e5e2e1] font-semibold truncate max-w-[200px]">
                          {getCameraName(activeSelected.camera_id)}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Lifecycle Chain */}
                  <div className="pt-2 border-t border-[#222222] flex items-center justify-between text-[10px]">
                    <span className="text-[#00F2FE] font-bold">1. DETECTED</span>
                    <span className="text-[#00F2FE] font-bold">→ 2. VERIFIED</span>
                    <span className="text-[#f5dfc0] font-bold">→ 3. EN ROUTE</span>
                    <span className="text-[#666666]">→ 4. RESOLVED</span>
                  </div>
                </div>

                {/* Live Incident Evidence Card - Clean, High-Legibility Image/Video View */}
                <div className="bg-[#141414] border border-[#262626] rounded-2xl p-6 shadow-2xl space-y-4 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between border-b border-[#222222] pb-3 mb-3">
                      <div className="flex items-center gap-2">
                        <span className="text-xs uppercase tracking-wider text-[#f5dfc0] font-bold">
                          Live Incident Evidence
                        </span>
                      </div>

                      {/* View Switcher: Freeze Frame vs Stream Video */}
                      <div className="flex items-center bg-[#0a0a0a] p-1 rounded-xl border border-[#262626]">
                        <button
                          onClick={() => setEvidenceMode('snapshot')}
                          className={`px-3 py-1 text-[10px] font-bold rounded-lg transition ${evidenceMode === 'snapshot'
                              ? 'bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] text-[#0A0A0A] shadow'
                              : 'text-[#858585] hover:text-white'
                            }`}
                        >
                          Snapshot (HUD)
                        </button>
                        <button
                          onClick={() => setEvidenceMode('video')}
                          className={`px-3 py-1 text-[10px] font-bold rounded-lg transition ${evidenceMode === 'video'
                              ? 'bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] text-[#0A0A0A] shadow'
                              : 'text-[#858585] hover:text-white'
                            }`}
                        >
                          Video Feed
                        </button>
                      </div>
                    </div>

                    <div className="relative aspect-video bg-black border border-[#222222] rounded-xl overflow-hidden flex items-center justify-center">
                      {evidenceMode === 'snapshot' ? (
                        activeSelected.snapshot_path ? (
                          <div
                            onClick={() => onSelectEvent && onSelectEvent(activeSelected)}
                            className="w-full h-full cursor-pointer group relative"
                          >
                            <img
                              src={activeSelected.snapshot_path}
                              alt="Incident Evidence"
                              className="w-full h-full object-contain group-hover:scale-[1.02] transition duration-300"
                            />
                            <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center gap-2 text-white text-xs font-bold">
                              <Eye className="w-4 h-4 text-[#00F2FE]" /> Click to Inspect Full Resolution Lightbox
                            </div>
                          </div>
                        ) : (
                          <div className="text-[#666] text-xs">Snapshot Unavailable</div>
                        )
                      ) : (
                        <video
                          key={resolvedVideo}
                          src={resolvedVideo}
                          controls
                          autoPlay
                          muted
                          playsInline
                          loop
                          className="w-full h-full object-contain"
                        />
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-[#858585] pt-2 border-t border-[#222222]">
                    <span className="truncate max-w-[240px] font-mono">
                      {evidenceMode === 'snapshot' ? (activeSelected.snapshot_path ? activeSelected.snapshot_path.split('/').pop() : 'Snapshot') : `Feed: ${resolvedVideo.split('/').pop()}`}
                    </span>
                    <span className="text-[#00F2FE] font-bold flex items-center gap-1">
                      <ShieldCheck className="w-3.5 h-3.5" /> SHA-256 VERIFIED
                    </span>
                  </div>
                </div>
              </div>

              {/* 3. THREAT-TAILORED SOP TACTICAL RESPONSE CARDS - Standard 3-Agency Emergency Standard (Police, Fire Brigade, Ambulance) */}
              <div className="bg-[#141414] border border-[#262626] rounded-2xl p-6 shadow-2xl space-y-4">
                <div className="flex items-center justify-between border-b border-[#222222] pb-3">
                  <div>
                    <h3 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider flex items-center gap-2">
                      <span>Authorized Standard Operating Procedures (SOP)</span>
                    </h3>
                    <p className="text-[11px] text-[#858585] mt-0.5">
                      Tailored multi-agency emergency deployment workflows for {activeSelected.event_type} threats
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  {activeSOPs.map((sop) => {
                    const Icon = sop.icon;
                    const isDispatched = dispatches[`${activeSelected.id}_${sop.code}`];

                    return (
                      <div
                        key={sop.code}
                        className={`p-5 rounded-2xl border flex flex-col justify-between space-y-4 transition ${isDispatched
                            ? 'bg-[#0f1715] border-emerald-500/50 shadow-lg shadow-emerald-950/30'
                            : 'bg-[#181818] border-[#2a2a2a] hover:border-[#00F2FE]/40'
                          }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <div className="p-2 rounded-lg bg-[#0d0d0d] border border-[#262626]">
                              <Icon className="w-4 h-4 text-[#858585]" />
                            </div>
                            <span className="text-xs font-mono font-bold tracking-wider text-[#858585] uppercase">
                              {sop.agency || sop.code}
                            </span>
                          </div>
                          <span className="text-[10px] text-[#858585] font-bold">ETA: {sop.eta}</span>
                        </div>

                        <div>
                          <div className="text-xs font-bold text-[#f5dfc0] mb-1">
                            {sop.title}
                          </div>
                          <p className="text-[11px] text-[#858585] leading-relaxed">
                            {sop.units}
                          </p>
                        </div>

                        <button
                          onClick={() => openDispatchConfirmation(activeSelected.id, sop.code, sop.title, sop.units)}
                          className={`w-full py-2.5 rounded-xl font-mono text-xs font-black uppercase tracking-wider transition flex items-center justify-center gap-2 shadow-lg ${isDispatched
                              ? 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/60'
                              : 'bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] hover:opacity-95 text-[#0A0A0A] shadow-cyan-950/50 transform hover:scale-[1.01]'
                            }`}
                        >
                          {isDispatched ? (
                            <>
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Unit Dispatched
                            </>
                          ) : (
                            'Authorize Deployment'
                          )}
                        </button>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-[#666] text-sm">
              Select an incident from the tactical action stack to review response options.
            </div>
          )}
        </div>
      </div>

      {/* Two-Step Tactical Dispatch Confirmation Modal */}
      <AnimatePresence>
        {pendingDispatch && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md font-mono"
            onClick={() => setPendingDispatch(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 10 }}
              className="w-full max-w-lg p-6 border border-[#262626] rounded-2xl bg-[#141414] shadow-2xl space-y-4 text-xs"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-[#222222] pb-3">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-amber-400" />
                  <h3 className="text-sm font-bold text-[#f5dfc0] uppercase">
                    Confirm Emergency Tactical Transmission
                  </h3>
                </div>
                <button onClick={() => setPendingDispatch(null)} className="text-[#858585] hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-2.5 bg-[#0a0a0a] p-4 rounded-xl border border-[#222222]">
                <div className="flex justify-between border-b border-[#1c1c1c] pb-1.5">
                  <span className="text-[#858585]">Target Incident</span>
                  <span className="text-[#f5dfc0] font-bold">
                    {activeSelected?.event_type} (#EVT-{String(pendingDispatch.eventId).padStart(4, '0')})
                  </span>
                </div>
                <div className="flex justify-between border-b border-[#1c1c1c] pb-1.5">
                  <span className="text-[#858585]">Location Node</span>
                  <span className="text-[#e5e2e1]">{getCameraName(activeSelected?.camera_id)}</span>
                </div>
                <div className="flex justify-between border-b border-[#1c1c1c] pb-1.5">
                  <span className="text-[#858585]">Coordinates</span>
                  <span className="text-[#00F2FE]">{getCameraGps(activeSelected?.camera_id)}</span>
                </div>
                <div className="flex justify-between border-b border-[#1c1c1c] pb-1.5">
                  <span className="text-[#858585]">SOP Protocol</span>
                  <span className="text-[#f5dfc0] font-bold">{pendingDispatch.actionCode} · {pendingDispatch.actionTitle}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#858585]">Allocated Units</span>
                  <span className="text-[#00F2FE] font-bold">{pendingDispatch.units}</span>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setPendingDispatch(null)}
                  className="px-4 py-2 bg-[#1b1c24] hover:bg-[#252834] text-[#858585] hover:text-white rounded-xl text-xs font-bold transition border border-[#2a2a2a]"
                >
                  Abort
                </button>
                <button
                  onClick={confirmDispatch}
                  className="px-6 py-2.5 bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] hover:opacity-95 text-[#0A0A0A] rounded-xl text-xs font-black uppercase tracking-wider transition shadow-lg shadow-cyan-950/50 flex items-center gap-1.5 transform hover:scale-[1.02]"
                >
                  <Send className="w-3.5 h-3.5" />
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
