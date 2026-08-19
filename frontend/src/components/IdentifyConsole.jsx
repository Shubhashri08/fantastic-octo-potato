import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, Search, User, ShieldAlert, FileText, CheckCircle2, AlertTriangle, Eye, Video, MapPin, Clock, Navigation, Send } from 'lucide-react';

export default function IdentifyConsole({ events = [], selectedCameraId, onSelectCamera, onSelectEvent, onNavigateToMap }) {
  const [activeSubTab, setActiveSubTab] = useState('person'); // 'person' | 'vehicle' | 'incidents'

  // Person Finder State
  const [uploadedImage, setUploadedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [minSimilarity, setMinSimilarity] = useState(0.30);
  const [selectedLocation, setSelectedLocation] = useState('All');
  const [selectedTimeRange, setSelectedTimeRange] = useState('last_30m');
  const [personSearchResults, setPersonSearchResults] = useState([]);
  const [isSearchingPerson, setIsSearchingPerson] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const fileInputRef = useRef(null);

  // Vehicle Finder State
  const [plateQuery, setPlateQuery] = useState('');
  const [selectedType, setSelectedType] = useState('All');
  const [selectedColor, setSelectedColor] = useState('All');
  const [vehicleSearchResults, setVehicleSearchResults] = useState([]);
  const [isSearchingVehicle, setIsSearchingVehicle] = useState(false);

  // Incident Filters State
  const [incidentSearch, setIncidentSearch] = useState('');
  const [incidentTypeFilter, setIncidentTypeFilter] = useState('All');
  const [incidentSeverityFilter, setIncidentSeverityFilter] = useState('All');
  const [reconstructingEventId, setReconstructingEventId] = useState(null);
  const [reconstructionData, setReconstructionData] = useState(null);
  const [isLoadingReconstruction, setIsLoadingReconstruction] = useState(false);

  const fetchEventReconstruction = async (eventId) => {
    setReconstructingEventId(eventId);
    setIsLoadingReconstruction(true);
    try {
      const res = await fetch(`/api/events/${eventId}/reconstruction`);
      if (res.ok) {
        const data = await res.json();
        setReconstructionData(data);
      }
    } catch (err) {
      console.error('Error fetching event reconstruction:', err);
    } finally {
      setIsLoadingReconstruction(false);
    }
  };

  // Initial fetch for vehicle search
  useEffect(() => {
    fetchVehicles();
  }, [plateQuery, selectedType, selectedColor]);

  const fetchVehicles = async () => {
    setIsSearchingVehicle(true);
    try {
      const params = new URLSearchParams();
      if (plateQuery.trim()) params.append('plate', plateQuery.trim());
      if (selectedType !== 'All') params.append('vehicle_type', selectedType);
      if (selectedColor !== 'All') params.append('color', selectedColor);

      const res = await fetch(`/api/vehicle/search?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setVehicleSearchResults(data.matches || []);
      }
    } catch (err) {
      console.error('Error searching vehicles:', err);
    } finally {
      setIsSearchingVehicle(false);
    }
  };

  const handleImageFile = (file) => {
    if (!file) return;
    setSearchError(null);
    setUploadedImage(file);
    setImagePreview(URL.createObjectURL(file));
    executePersonSearch(file, minSimilarity, selectedLocation, selectedTimeRange);
  };

  const handleImageUpload = (e) => {
    const file = e.target.files?.[0];
    if (file) handleImageFile(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file && file.type.startsWith('image/')) {
      handleImageFile(file);
    }
  };

  const handleQuickSamplePerson = async (samplePath, label) => {
    setSearchError(null);
    try {
      setIsSearchingPerson(true);
      const res = await fetch(samplePath);
      if (!res.ok) throw new Error(`Failed to load ${samplePath}`);
      const blob = await res.blob();
      const file = new File([blob], `${label}.jpg`, { type: 'image/jpeg' });
      setUploadedImage(file);
      setImagePreview(samplePath);
      executePersonSearch(file, minSimilarity, selectedLocation, selectedTimeRange);
    } catch (err) {
      console.error('Error loading sample person:', err);
      setSearchError('Could not load sample image. Please upload a photo directly.');
      setIsSearchingPerson(false);
    }
  };

  const executePersonSearch = async (file, sim, loc, timeWin) => {
    if (!file) return;
    setIsSearchingPerson(true);
    setSearchError(null);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const params = new URLSearchParams();
      params.append('min_similarity', sim);
      if (loc && loc !== 'All') params.append('location', loc);
      if (timeWin) params.append('time_window', timeWin);

      const res = await fetch(`/api/person/search?${params.toString()}`, {
        method: 'POST',
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setPersonSearchResults(data.matches || []);
      } else {
        throw new Error(`Server returned HTTP ${res.status}`);
      }
    } catch (err) {
      console.error('Error searching person:', err);
      setSearchError('Search request failed. Please check backend connection.');
    } finally {
      setIsSearchingPerson(false);
    }
  };

  // Trigger search when location or time filters change
  const handleLocationChange = (loc) => {
    setSelectedLocation(loc);
    if (uploadedImage) {
      executePersonSearch(uploadedImage, minSimilarity, loc, selectedTimeRange);
    }
  };

  const handleTimeChange = (timeWin) => {
    setSelectedTimeRange(timeWin);
    if (uploadedImage) {
      executePersonSearch(uploadedImage, minSimilarity, selectedLocation, timeWin);
    }
  };

  // Filtered Incident Log
  const filteredIncidents = (events || []).filter((ev) => {
    if (!ev) return false;
    const matchSearch =
      incidentSearch === '' ||
      (ev.event_type && ev.event_type.toLowerCase().includes(incidentSearch.toLowerCase())) ||
      String(ev.camera_id).includes(incidentSearch);
    const matchType = incidentTypeFilter === 'All' || (ev.event_type && ev.event_type.toLowerCase().includes(incidentTypeFilter.toLowerCase()));
    const matchSev = incidentSeverityFilter === 'All' || ev.severity === incidentSeverityFilter;
    return matchSearch && matchType && matchSev;
  });

  return (
    <div className="h-full w-full flex flex-col bg-[#0A0A0A] text-[#e5e2e1] overflow-hidden">
      {/* Top Layer Header & Sub-Tab Switcher */}
      <div className="px-6 py-4 border-b border-[#262626] bg-[#121212] flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#f5dfc0] animate-pulse"></span>
            <span className="text-xs font-mono tracking-widest text-[#858585] uppercase">
              LAYER 3 — IDENTIFY & RE-IDENTIFICATION CONSOLE
            </span>
          </div>
          <h1 className="text-lg font-bold text-[#f5dfc0] mt-0.5">
            Surveillance Re-ID & Location-Time Intelligence
          </h1>
        </div>

        {/* Sub-Tab Navigation Pills */}
        <div className="flex items-center bg-[#1a1a1a] p-1 rounded-lg border border-[#2e2e2e]">
          <button
            onClick={() => setActiveSubTab('person')}
            className={`px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
              activeSubTab === 'person'
                ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md font-bold'
                : 'text-[#a3a3a3] hover:text-[#e5e2e1]'
            }`}
          >
            👤 Person Finder (Location & Time)
          </button>
          <button
            onClick={() => setActiveSubTab('vehicle')}
            className={`px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
              activeSubTab === 'vehicle'
                ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md font-bold'
                : 'text-[#a3a3a3] hover:text-[#e5e2e1]'
            }`}
          >
            🚗 Vehicle Finder (Plate & Color)
          </button>
          <button
            onClick={() => setActiveSubTab('incidents')}
            className={`px-4 py-1.5 rounded-md text-xs font-mono font-medium transition-all ${
              activeSubTab === 'incidents'
                ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md font-bold'
                : 'text-[#a3a3a3] hover:text-[#e5e2e1]'
            }`}
          >
            📋 Incident Audit Log ({events.length})
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6">
        {/* ================= TAB 1: PERSON FINDER ================= */}
        {activeSubTab === 'person' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
            {/* Left Column: Upload & Search Filters */}
            <div className="bg-[#141414] border border-[#262626] rounded-xl p-5 flex flex-col gap-4">
              <div>
                <h2 className="text-sm font-mono uppercase tracking-wider text-[#f5dfc0] font-bold flex items-center gap-2">
                  <Upload className="w-4 h-4 text-[#f5dfc0]" /> Target Photo & Search Filters
                </h2>
                <p className="text-xs text-[#858585] mt-1">
                  Filter real CCTV footages by Location Node and Latest Time Window.
                </p>
              </div>

              {/* Upload Dropzone */}
              <div
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-4 flex flex-col items-center justify-center cursor-pointer transition-all bg-[#0d0d0d] relative group ${
                  isDragging ? 'border-[#00F2FE] bg-[#00F2FE]/5' : 'border-[#333333] hover:border-[#f5dfc0]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleImageUpload}
                  className="hidden"
                />
                {imagePreview ? (
                  <div className="flex flex-col items-center gap-2">
                    <img
                      src={imagePreview}
                      alt="Query Target"
                      className="h-36 w-28 object-cover rounded-lg border-2 border-[#f5dfc0] shadow-xl"
                    />
                    <span className="text-[11px] font-mono text-[#f5dfc0] group-hover:underline">
                      🔄 Replace Photo
                    </span>
                  </div>
                ) : (
                  <div className="flex flex-col items-center text-center gap-1.5">
                    <div className="h-10 w-10 rounded-full bg-[#1e1e1e] flex items-center justify-center text-lg text-[#f5dfc0]">
                      📷
                    </div>
                    <span className="text-xs font-mono font-medium text-[#e5e2e1]">
                      Click to Browse or Drag Photo Here
                    </span>
                    <span className="text-[10px] text-[#737373]">
                      Supports JPG, PNG, WEBP
                    </span>
                  </div>
                )}
              </div>

              {/* 1. Location / Node Filter Field */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono text-[#858585] uppercase tracking-wider flex items-center gap-1.5">
                  <MapPin className="w-3.5 h-3.5 text-[#00F2FE]" /> Filter by Location / Camera:
                </label>
                <select
                  value={selectedLocation}
                  onChange={(e) => handleLocationChange(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg bg-[#0d0d0d] border border-[#333333] text-xs font-mono text-[#f5dfc0] font-bold outline-none focus:border-[#00F2FE]"
                >
                  <option value="All">🌐 All Municipal Grids (Mumbai & Bengaluru)</option>
                  <option value="Mumbai">📍 Mumbai Safe City (All 10 Nodes)</option>
                  <option value="CSMT">📍 Mumbai — CSMT Concourse Station</option>
                  <option value="Sea Link">📍 Mumbai — Bandra-Worli Sea Link Toll</option>
                  <option value="Bengaluru">📍 Bengaluru Safe City (All Nodes)</option>
                  <option value="MG Road">📍 Bengaluru — MG Road Commercial Corridor</option>
                </select>
              </div>

              {/* 2. Latest Time Window Field */}
              <div className="space-y-1.5">
                <label className="text-[11px] font-mono text-[#858585] uppercase tracking-wider flex items-center gap-1.5">
                  <Clock className="w-3.5 h-3.5 text-[#f5dfc0]" /> CCTV Footage Time Horizon:
                </label>
                <div className="grid grid-cols-2 gap-1.5">
                  {[
                    { key: 'last_30m', label: '⏱️ Last 30 Mins' },
                    { key: 'last_2h', label: '🕒 Past 2 Hours' },
                    { key: 'last_24h', label: '📅 Past 24 Hours' },
                    { key: 'all', label: '🗄️ Full Archive' }
                  ].map((tw) => (
                    <button
                      key={tw.key}
                      onClick={() => handleTimeChange(tw.key)}
                      className={`px-2.5 py-1.5 rounded-lg text-xs font-mono text-center border transition-all ${
                        selectedTimeRange === tw.key
                          ? 'bg-[#f5dfc0] text-[#0A0A0A] font-bold border-[#f5dfc0]'
                          : 'bg-[#181818] text-[#858585] border-[#292929] hover:text-[#e5e2e1]'
                      }`}
                    >
                      {tw.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* One-Click Presets for Demo */}
              <div>
                <span className="text-[11px] font-mono text-[#858585] uppercase tracking-wider block mb-1.5">
                  ⚡ Quick Test Presets:
                </span>
                <div className="grid grid-cols-1 gap-1.5">
                  <button
                    onClick={() => handleQuickSamplePerson('/ref_airtlab_target_1.jpg', 'airtlab_dataset_target')}
                    className="text-left px-3 py-2.5 rounded-lg bg-[#142820] hover:bg-[#1b382d] border border-emerald-500/50 text-xs font-mono text-[#e5e2e1] flex items-center justify-between transition hover:scale-[1.01] shadow"
                  >
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
                      <span className="font-bold text-[#9ed1c1]">🎯 Target Subject from AIRTLab Dataset</span>
                    </div>
                    <span className="text-[10px] text-emerald-300 font-bold">94.5% True Positive ▶</span>
                  </button>
                  <button
                    onClick={() => handleQuickSamplePerson('/sample_target.png', 'your_portrait')}
                    className="text-left px-3 py-2 rounded-lg bg-[#1a1a1a] hover:bg-[#252525] border border-cyan-500/40 text-xs font-mono text-[#e5e2e1] flex items-center justify-between transition"
                  >
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 rounded-full bg-cyan-400"></span>
                      <span className="text-[#f5dfc0]">📸 Your Uploaded Portrait</span>
                    </div>
                    <span className="text-[10px] text-[#00F2FE] font-bold">71% Nearest Match ▶</span>
                  </button>
                </div>
              </div>

              {/* Similarity Threshold Slider */}
              <div className="pt-2 border-t border-[#262626]">
                <div className="flex justify-between text-xs font-mono mb-1.5">
                  <span className="text-[#858585]">Match Threshold:</span>
                  <span className="text-[#f5dfc0] font-bold">{(minSimilarity * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.15"
                  max="0.90"
                  step="0.05"
                  value={minSimilarity}
                  onChange={(e) => {
                    const newSim = parseFloat(e.target.value);
                    setMinSimilarity(newSim);
                    if (uploadedImage) executePersonSearch(uploadedImage, newSim, selectedLocation, selectedTimeRange);
                  }}
                  className="w-full accent-[#f5dfc0] cursor-pointer"
                />
              </div>

              {searchError && (
                <div className="p-2 rounded-lg bg-red-950/50 border border-red-800 text-xs font-mono text-red-300">
                  {searchError}
                </div>
              )}
            </div>

            {/* Right Column: Ranked CCTV Sightings with Exact Location & Live Time */}
            <div className="lg:col-span-2 flex flex-col gap-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-sm font-mono uppercase tracking-wider text-[#f5dfc0] font-bold flex items-center gap-2">
                    <Search className="w-4 h-4 text-[#00F2FE]" /> Live CCTV Sighting Matches ({personSearchResults.length})
                  </h2>
                  <p className="text-xs text-[#858585]">
                    Matched across real surveillance cameras filtered by <span className="text-[#00F2FE] font-bold">{selectedLocation}</span> within <span className="text-[#f5dfc0] font-bold">{selectedTimeRange}</span>
                  </p>
                </div>
              </div>

              {isSearchingPerson ? (
                <div className="h-64 flex flex-col items-center justify-center gap-3 border border-[#262626] rounded-xl bg-[#121212]">
                  <div className="h-8 w-8 border-3 border-[#00F2FE] border-t-transparent rounded-full animate-spin"></div>
                  <span className="text-xs font-mono text-[#a3a3a3]">
                    Scanning CCTV video frames for location "{selectedLocation}"...
                  </span>
                </div>
              ) : personSearchResults.length === 0 ? (
                <div className="h-64 flex flex-col items-center justify-center gap-2 border border-[#262626] rounded-xl bg-[#121212] text-center p-6">
                  <span className="text-4xl">📍</span>
                  <span className="text-xs font-mono text-[#858585]">
                    No person sightings found matching "{selectedLocation}". Upload a photo or select "All Grids".
                  </span>
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {personSearchResults.map((res, idx) => {
                    const sightingsList = res.sightings || [];
                    const firstSighting = sightingsList[0] || {};
                    return (
                      <motion.div
                        key={res.person_id || idx}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: idx * 0.08 }}
                        className="bg-[#141414] border border-[#262626] hover:border-[#f5dfc0]/50 rounded-xl p-5 flex flex-col gap-4 transition-all"
                      >
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div className="flex items-center gap-4">
                            {/* Evidence Snapshot Thumbnail */}
                            {firstSighting.snapshot ? (
                              <img
                                src={firstSighting.snapshot}
                                alt="CCTV Crop"
                                className="h-20 w-16 rounded-lg object-cover border-2 border-cyan-400/60 bg-black shadow-lg"
                              />
                            ) : (
                              <div className="h-16 w-16 rounded-lg bg-[#222222] border border-[#333333] flex items-center justify-center font-mono font-bold text-sm text-[#f5dfc0]">
                                #{idx + 1}
                              </div>
                            )}
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="text-sm font-bold text-[#e5e2e1]">
                                  {firstSighting.camera_name || `Camera Node ${firstSighting.camera_id}`}
                                </h3>
                                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-[#1e1e1e] text-[#00F2FE] border border-[#00F2FE]/30 font-bold">
                                  {res.person_id}
                                </span>
                              </div>

                              {/* Exact Location & Timestamp */}
                              <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs font-mono text-[#f5dfc0] font-bold flex items-center gap-1">
                                  <MapPin className="w-3.5 h-3.5 text-[#00F2FE]" />
                                  {firstSighting.city || 'Surveillance Node'}
                                </span>
                                <span className="text-[#555]">•</span>
                                <span className="text-xs font-mono text-[#9ed1c1] font-bold flex items-center gap-1">
                                  <Clock className="w-3.5 h-3.5 text-[#9ed1c1]" />
                                  {firstSighting.timestamp} ({firstSighting.time_ago || res.time_ago})
                                </span>
                              </div>

                              <p className="text-[11px] text-[#858585] mt-1 font-mono">
                                📐 GPS: {firstSighting.lat}°N, {firstSighting.lon}°E | {firstSighting.heading || 'Footage Tracked'}
                              </p>
                            </div>
                          </div>

                          {/* Similarity Meter */}
                          <div className="flex items-center gap-3 bg-[#0d0d0d] px-4 py-2 rounded-lg border border-[#242424]">
                            <div className="text-right">
                              <span className="text-[10px] font-mono text-[#858585] block">Match Score</span>
                              <span className="text-base font-mono font-black text-[#00F2FE]">{res.similarity}%</span>
                            </div>
                            <div className="w-16 h-2.5 rounded-full bg-[#262626] overflow-hidden">
                              <div
                                className="h-full bg-gradient-to-r from-amber-400 to-cyan-400"
                                style={{ width: `${Math.min(100, res.similarity)}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>

                        {/* Multi-Checkpoint Location Timeline */}
                        <div className="bg-[#0a0a0a] rounded-lg p-3.5 border border-[#1f1f1f]">
                          <span className="text-[10px] font-mono text-[#858585] uppercase tracking-wider block mb-2">
                            📍 Multi-Camera Checkpoint Route & Timestamped Sightings:
                          </span>
                          <div className="space-y-2">
                            {sightingsList.map((s, sIdx) => (
                              <div
                                key={sIdx}
                                className="flex items-center justify-between text-xs font-mono text-[#a3a3a3] border-l-2 border-[#00F2FE] pl-3 py-1"
                              >
                                <div>
                                  <span className="text-[#e5e2e1] font-bold">{s.camera_name || `Camera ${s.camera_id}`}</span>
                                  <span className="text-[10px] text-[#00F2FE] ml-2 font-mono">({s.heading || 'Tracked Checkpoint'})</span>
                                </div>
                                <div className="text-right">
                                  <span className="text-[11px] text-[#f5dfc0] font-bold block">{s.timestamp}</span>
                                  <span className="text-[9px] text-[#858585]">{s.time_ago}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        )}

        {/* ================= TAB 2: VEHICLE FINDER ================= */}
        {activeSubTab === 'vehicle' && (
          <div className="space-y-6 max-w-7xl mx-auto">
            {/* Search Filters Card */}
            <div className="bg-[#141414] border border-[#262626] rounded-xl p-5 flex flex-col gap-4">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-sm font-mono uppercase tracking-wider text-[#f5dfc0] font-bold">
                      Vehicle & Stolen Car Tracking Engine
                    </h2>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-red-950/60 text-red-400 border border-red-800">
                      🚨 BOLO Watchlist Active
                    </span>
                  </div>
                  <p className="text-xs text-[#858585] mt-0.5">
                    Search municipal fleet records by License Plate or Visual Appearance (Type + Color).
                  </p>
                </div>

                {/* Number Plate Input */}
                <div className="flex items-center gap-2">
                  <input
                    type="text"
                    placeholder="Enter Plate (e.g. KA 03 AB 1234)..."
                    value={plateQuery}
                    onChange={(e) => setPlateQuery(e.target.value)}
                    className="px-4 py-2 rounded-lg bg-[#0d0d0d] border border-[#333333] focus:border-[#f5dfc0] text-xs font-mono text-[#e5e2e1] outline-none w-64 uppercase tracking-wider"
                  />
                  {plateQuery && (
                    <button
                      onClick={() => setPlateQuery('')}
                      className="px-2.5 py-2 rounded-lg bg-[#222222] text-xs text-[#a3a3a3] hover:text-[#e5e2e1]"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>

              {/* Filter Pills */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-3 border-t border-[#222222]">
                {/* Vehicle Type Selector */}
                <div>
                  <span className="text-[11px] font-mono text-[#858585] uppercase tracking-wider block mb-2">
                    Vehicle Type:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {['All', 'Car', 'SUV', 'Motorcycle', 'Bus'].map((type) => (
                      <button
                        key={type}
                        onClick={() => setSelectedType(type)}
                        className={`px-3 py-1 rounded-md text-xs font-mono transition-all ${
                          selectedType === type
                            ? 'bg-[#f5dfc0] text-[#0A0A0A] font-bold'
                            : 'bg-[#1a1a1a] text-[#858585] hover:text-[#e5e2e1] border border-[#2b2b2b]'
                        }`}
                      >
                        {type}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Color Selector */}
                <div>
                  <span className="text-[11px] font-mono text-[#858585] uppercase tracking-wider block mb-2">
                    Primary Color:
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {['All', 'White', 'Black', 'Red', 'Blue', 'Silver', 'Yellow', 'Green'].map((color) => (
                      <button
                        key={color}
                        onClick={() => setSelectedColor(color)}
                        className={`px-3 py-1 rounded-md text-xs font-mono transition-all ${
                          selectedColor === color
                            ? 'bg-[#f5dfc0] text-[#0A0A0A] font-bold'
                            : 'bg-[#1a1a1a] text-[#858585] hover:text-[#e5e2e1] border border-[#2b2b2b]'
                        }`}
                      >
                        {color}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Vehicle Results Grid */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-mono uppercase tracking-wider text-[#858585]">
                  Matching Vehicles in Surveillance Mesh ({vehicleSearchResults.length})
                </h3>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {vehicleSearchResults.map((v, idx) => (
                  <motion.div
                    key={v.vehicle_id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: idx * 0.06 }}
                    className={`bg-[#141414] border rounded-xl p-5 flex flex-col justify-between gap-4 transition-all ${
                      v.is_stolen ? 'border-red-600/50 shadow-[0_0_20px_rgba(239,68,68,0.15)]' : 'border-[#262626] hover:border-[#f5dfc0]/50'
                    }`}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        {/* High-Contrast Plate Badge */}
                        <div className="flex items-center gap-2">
                          <div className="px-3 py-1 rounded bg-[#f5dfc0] text-[#0A0A0A] font-mono font-black text-sm tracking-wider shadow">
                            {v.plate}
                          </div>
                          {v.is_stolen && (
                            <span className="px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-700 text-[10px] font-mono font-black animate-pulse">
                              STOLEN VEHICLE
                            </span>
                          )}
                        </div>
                        <span className="text-xs font-mono text-[#858585] bg-[#0d0d0d] px-2.5 py-1 rounded border border-[#262626]">
                          {v.city}
                        </span>
                      </div>

                      {v.bolo_status && (
                        <div className="mt-2 text-[11px] font-mono text-red-300 bg-red-950/40 border border-red-800/60 p-2 rounded">
                          {v.bolo_status}
                        </div>
                      )}

                      <div className="grid grid-cols-3 gap-2 mt-3 text-xs font-mono bg-[#0d0d0d] p-3 rounded-lg border border-[#1f1f1f]">
                        <div>
                          <span className="text-[10px] text-[#737373] block">Type</span>
                          <span className="text-[#e5e2e1] font-bold">{v.type}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-[#737373] block">Color</span>
                          <span className="text-[#e5e2e1] font-bold">{v.color}</span>
                        </div>
                        <div>
                          <span className="text-[10px] text-[#737373] block">Speed</span>
                          <span className="text-[#f5dfc0] font-bold">{v.speed_kmh} km/h</span>
                        </div>
                      </div>
                    </div>

                    {/* Checkpoint Trajectory History */}
                    {v.trajectory && v.trajectory.length > 0 && (
                      <div className="bg-[#0a0a0a] rounded-lg p-3 border border-[#1f1f1f] space-y-1.5">
                        <span className="text-[10px] font-mono text-[#858585] uppercase tracking-wider block">
                          📍 Multi-Camera Checkpoint Route:
                        </span>
                        {v.trajectory.map((t, tIdx) => (
                          <div key={tIdx} className="flex items-center justify-between text-[11px] font-mono border-l-2 border-[#f5dfc0] pl-2 py-0.5 text-[#cfc5b9]">
                            <span>{t.camera || `Point ${tIdx+1}`}</span>
                            <div className="flex items-center gap-2">
                              {t.speed && <span className="text-[#9ed1c1]">{t.speed} km/h</span>}
                              <span className="text-[#f5dfc0]">{t.time}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Last Sighting Info */}
                    <div className="border-t border-[#222222] pt-2 flex items-center justify-between text-xs font-mono">
                      <div>
                        <span className="text-[10px] text-[#737373] block">Last Seen Node</span>
                        <span className="text-[#e5e2e1]">{v.camera_name}</span>
                      </div>
                      <span className="text-[11px] text-[#f5dfc0]">{v.timestamp}</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ================= TAB 3: INCIDENT AUDIT LOG ================= */}
        {activeSubTab === 'incidents' && (
          <div className="space-y-4 max-w-7xl mx-auto">
            {/* Filter Bar */}
            <div className="bg-[#141414] border border-[#262626] rounded-xl p-4 flex flex-wrap items-center justify-between gap-3">
              <input
                type="text"
                placeholder="Search by threat type or Cam ID..."
                value={incidentSearch}
                onChange={(e) => setIncidentSearch(e.target.value)}
                className="px-3 py-1.5 rounded-lg bg-[#0d0d0d] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none w-64"
              />

              <div className="flex items-center gap-2">
                <select
                  value={incidentTypeFilter}
                  onChange={(e) => setIncidentTypeFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-[#0d0d0d] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none"
                >
                  <option value="All">All Threats & Accidents</option>
                  <option value="Fighting">🥊 Fighting</option>
                  <option value="Fire">🔥 Fire Outbreak</option>
                  <option value="Accident">🚗 Accident / Collision</option>
                </select>

                <select
                  value={incidentSeverityFilter}
                  onChange={(e) => setIncidentSeverityFilter(e.target.value)}
                  className="px-3 py-1.5 rounded-lg bg-[#0d0d0d] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none"
                >
                  <option value="All">All Severities</option>
                  <option value="Critical">Critical</option>
                  <option value="High">High</option>
                  <option value="Medium">Medium</option>
                </select>
              </div>
            </div>

            {/* Table */}
            <div className="bg-[#141414] border border-[#262626] rounded-xl overflow-hidden shadow-xl">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-[#0f0f0f] border-b border-[#262626] text-[#858585] uppercase text-[11px]">
                  <tr>
                    <th className="py-3 px-4">Incident ID</th>
                    <th className="py-3 px-4">Camera</th>
                    <th className="py-3 px-4">Threat Type</th>
                    <th className="py-3 px-4">Confidence</th>
                    <th className="py-3 px-4">Timestamp</th>
                    <th className="py-3 px-4 text-right">Forensic Evidence</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#1e1e1e]">
                  {filteredIncidents.length === 0 ? (
                    <tr>
                      <td colSpan="6" className="py-8 text-center text-[#737373]">
                        No verified incidents matching filter criteria.
                      </td>
                    </tr>
                  ) : (
                    filteredIncidents.map((ev) => (
                      <tr key={ev.id} className="hover:bg-[#181818] transition-colors">
                        <td className="py-3 px-4 font-bold text-[#f5dfc0]">#INC-{ev.id}</td>
                        <td className="py-3 px-4 text-[#e5e2e1]">CAM-0{ev.camera_id}</td>
                        <td className="py-3 px-4">
                          <span
                            className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
                              ev.event_type.toLowerCase().includes('fire')
                                ? 'bg-orange-950/60 text-orange-400 border border-orange-800'
                                : ev.event_type.toLowerCase().includes('accident')
                                ? 'bg-amber-950/60 text-amber-300 border border-amber-800'
                                : 'bg-red-950/60 text-red-400 border border-red-800'
                            }`}
                          >
                            {ev.event_type}
                          </span>
                        </td>
                        <td className="py-3 px-4 text-[#e5e2e1]">{(ev.confidence * 100).toFixed(0)}%</td>
                        <td className="py-3 px-4 text-[#858585]">{ev.timestamp}</td>
                        <td className="py-3 px-4 text-right space-x-2">
                          <button
                            onClick={() => fetchEventReconstruction(ev.id)}
                            className="px-2.5 py-1 rounded bg-[#f5dfc0]/20 hover:bg-[#f5dfc0] text-[#f5dfc0] hover:text-[#0A0A0A] border border-[#f5dfc0]/50 text-[11px] font-bold transition-all shadow"
                          >
                            🔄 Reconstruct Event
                          </button>
                          <button
                            onClick={() => onSelectEvent(ev)}
                            className="px-2.5 py-1 rounded bg-[#222222] hover:bg-[#e5e2e1] hover:text-[#0A0A0A] text-[#e5e2e1] text-[11px] font-bold transition-all shadow"
                          >
                            📸 Evidence
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>

            {/* Event Reconstruction Modal */}
            <AnimatePresence>
              {reconstructingEventId && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4"
                >
                  <motion.div
                    initial={{ scale: 0.95, y: 20 }}
                    animate={{ scale: 1, y: 0 }}
                    exit={{ scale: 0.95, y: 20 }}
                    className="bg-[#111111] border border-[#333333] rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl space-y-6"
                  >
                    {/* Header */}
                    <div className="flex items-center justify-between border-b border-[#222222] pb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-[#f5dfc0]/10 border border-[#f5dfc0]/30 text-[#f5dfc0]">
                          <Clock className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-[#f5dfc0] uppercase tracking-wider font-bold">
                              FORENSIC EVENT RECONSTRUCTION
                            </span>
                            <span className="px-2 py-0.5 rounded bg-red-950 text-red-400 border border-red-800 text-[10px] font-mono font-bold">
                              INCIDENT #{reconstructingEventId}
                            </span>
                          </div>
                          <h2 className="text-lg font-bold text-[#e5e2e1]">
                            Temporal Multi-Camera Timeline Analysis
                          </h2>
                        </div>
                      </div>

                      <button
                        onClick={() => {
                          setReconstructingEventId(null);
                          setReconstructionData(null);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-[#222222] hover:bg-[#333333] text-xs font-mono text-[#858585] hover:text-white transition-all"
                      >
                        ✕ Close
                      </button>
                    </div>

                    {isLoadingReconstruction ? (
                      <div className="py-16 text-center text-[#858585] font-mono text-sm">
                        <div className="animate-spin w-8 h-8 border-2 border-[#f5dfc0] border-t-transparent rounded-full mx-auto mb-4" />
                        Synthesizing Multi-Camera Checkpoints & Proximity Radar from Neon DB...
                      </div>
                    ) : reconstructionData ? (
                      <div className="space-y-6">
                        {/* Incident Snapshot Telemetry */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 bg-[#181818] p-4 rounded-xl border border-[#262626] text-xs font-mono">
                          <div>
                            <span className="text-[10px] text-[#737373] block uppercase">Threat Classification</span>
                            <span className="text-red-400 font-bold text-sm">{reconstructionData.event_type}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-[#737373] block uppercase">Primary Sensor Node</span>
                            <span className="text-[#e5e2e1] font-bold text-sm">CAM-{reconstructionData.camera_id}</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-[#737373] block uppercase">Neural Certainty</span>
                            <span className="text-[#f5dfc0] font-bold text-sm">{(reconstructionData.confidence * 100).toFixed(0)}%</span>
                          </div>
                          <div>
                            <span className="text-[10px] text-[#737373] block uppercase">Timestamp (UTC)</span>
                            <span className="text-[#cfc5b9] font-bold">{reconstructionData.timestamp}</span>
                          </div>
                        </div>

                        {/* 3-Phase Temporal Narrative Scrubber */}
                        <div className="space-y-3">
                          <h3 className="text-xs font-mono uppercase tracking-wider text-[#858585]">
                            ⏱️ 3-Phase Chronological Incident Narrative:
                          </h3>
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                            {reconstructionData.reconstructed_timeline?.map((phase, pIdx) => (
                              <div
                                key={pIdx}
                                className="bg-[#161616] border border-[#2b2b2b] p-4 rounded-xl space-y-2 relative overflow-hidden"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="text-[10px] font-mono font-bold text-[#f5dfc0] uppercase tracking-wider">
                                    {phase.phase}
                                  </span>
                                  <span className="px-2 py-0.5 rounded bg-[#222222] text-[9px] font-mono text-[#858585]">
                                    {phase.status}
                                  </span>
                                </div>
                                <p className="text-xs text-[#cfc5b9] leading-relaxed font-mono">
                                  {phase.description}
                                </p>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Involved Entities & Proximity Radar */}
                        <div className="space-y-3">
                          <h3 className="text-xs font-mono uppercase tracking-wider text-[#858585]">
                            🎯 Nearby Entities Mapped in Proximity Radius ({reconstructionData.involved_entities?.length || 0}):
                          </h3>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                            {reconstructionData.involved_entities?.map((ent, eIdx) => (
                              <div
                                key={eIdx}
                                className="bg-[#141414] border border-[#2a2a2a] p-4 rounded-xl flex items-center justify-between"
                              >
                                <div className="space-y-1">
                                  <div className="flex items-center gap-2">
                                    <span className="px-2 py-0.5 rounded bg-[#f5dfc0] text-[#0A0A0A] text-[11px] font-mono font-bold">
                                      {ent.track_id}
                                    </span>
                                    <span className="text-xs font-mono font-bold text-[#e5e2e1]">
                                      {ent.entity_type}
                                    </span>
                                  </div>
                                  <div className="text-[11px] font-mono text-[#858585]">
                                    {Object.entries(ent.metadata || {}).map(([k, v]) => `${k}: ${v}`).join(' • ') || 'Standard profile'}
                                  </div>
                                </div>

                                <div className="text-right font-mono">
                                  <span className="text-[10px] text-[#737373] block uppercase">Proximity Distance</span>
                                  <span className="text-sm font-bold text-[#f5dfc0]">
                                    {ent.proximity_meters ? `${ent.proximity_meters.toFixed(1)}m` : '< 50m'}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Multi-Camera Sightings Checkpoint Trail */}
                        <div className="space-y-3">
                          <h3 className="text-xs font-mono uppercase tracking-wider text-[#858585]">
                            📍 Multi-Camera Checkpoint Route Trail:
                          </h3>
                          <div className="bg-[#0e0e0e] border border-[#262626] rounded-xl p-4 space-y-2">
                            {reconstructionData.chronological_sightings?.map((s, sIdx) => (
                              <div
                                key={sIdx}
                                className="flex items-center justify-between text-xs font-mono py-1.5 px-2 border-l-2 border-[#f5dfc0] hover:bg-[#161616] transition-colors rounded"
                              >
                                <div className="flex items-center gap-3">
                                  <span className="font-bold text-[#f5dfc0]">
                                    Checkpoint {sIdx + 1}:
                                  </span>
                                  <span className="text-[#e5e2e1]">
                                    {s.camera_id}
                                  </span>
                                  <span className="px-2 py-0.5 rounded bg-[#222222] text-[#858585] text-[10px]">
                                    Target: {s.track_id} ({s.entity_type})
                                  </span>
                                </div>
                                <div className="flex items-center gap-4">
                                  <span className="text-[#9ed1c1]">
                                    Certainty: {(s.confidence * 100).toFixed(0)}%
                                  </span>
                                  <span className="text-[#f5dfc0] font-bold">
                                    {s.timestamp}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>
    </div>
  );
}
