import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Upload, Search, User, ShieldAlert, FileText, CheckCircle2, AlertTriangle, 
  Eye, Video, MapPin, Clock, Navigation, Send, Flag, Car, ShieldCheck, 
  RefreshCw, Gauge, Compass, AlertOctagon, Check, Filter, Sparkles, 
  Camera as CameraIcon, ExternalLink, ChevronRight, X, AlertCircle, Shield, Layers
} from 'lucide-react';

import { 
  searchVehicle, 
  getVehicles, 
  getVehicleSightings, 
  flagVehicle 
} from '../api/vehicles';
import { 
  getVideoEvidenceSources, 
  uploadVideoEvidence, 
  deleteVideoEvidence, 
  searchPersonEvidence 
} from '../api/persons';
import { getCameras } from '../api/cameras';

export default function IdentifyConsole({ 
  events = [], 
  selectedCameraId, 
  onSelectCamera, 
  onSelectEvent, 
  onNavigateToMap,
  activeSubTab: parentSubTab = 'vehicle',
  onChangeSubTab
}) {
  const [internalSubTab, setInternalSubTab] = useState(parentSubTab === 'person' ? 'person' : 'vehicle');
  const activeSubTab = (parentSubTab === 'person' || parentSubTab === 'vehicle') ? parentSubTab : internalSubTab;

  const handleSubTabChange = (tabKey) => {
    setInternalSubTab(tabKey);
    if (onChangeSubTab) onChangeSubTab(tabKey);
  };

  // Dynamic Camera Registry
  const [availableCameras, setAvailableCameras] = useState([]);

  useEffect(() => {
    async function loadRegisteredCameras() {
      try {
        const cams = await getCameras();
        if (Array.isArray(cams)) {
          setAvailableCameras(cams);
        }
      } catch (err) {
        console.warn('Could not load camera registry:', err);
      }
    }
    loadRegisteredCameras();
  }, []);

  // ==========================================
  // 1. VEHICLE FINDER STATE
  // ==========================================
  const [vehicleSearchMode, setVehicleSearchMode] = useState('plate'); // 'plate' | 'description'
  const [plateInput, setPlateInput] = useState('');
  const [plateLocation, setPlateLocation] = useState('All');
  const [plateTimeRange, setPlateTimeRange] = useState('all');
  
  const [descType, setDescType] = useState('All');
  const [descModel, setDescModel] = useState('');
  const [descColor, setDescColor] = useState('All');
  const [descLocation, setDescLocation] = useState('All');
  const [descTimeRange, setDescTimeRange] = useState('all');

  // Investigation Results State
  const [investigationStatus, setInvestigationStatus] = useState('idle'); // 'idle' | 'searching' | 'found' | 'no_match' | 'error'
  const [investigationError, setInvestigationError] = useState(null);
  const [vehicleMatches, setVehicleMatches] = useState([]);
  const [isSearchingVehicle, setIsSearchingVehicle] = useState(false);
  const [selectedVehicleForModal, setSelectedVehicleForModal] = useState(null);

  // Movement History Modal State
  const [movementHistory, setMovementHistory] = useState(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [historyError, setHistoryError] = useState(null);

  // Database Browser View (Browse All Logged Vehicles)
  const [isBrowsingDatabase, setIsBrowsingDatabase] = useState(false);
  const [dbVehicles, setDbVehicles] = useState([]);
  const [dbTotalCount, setDbTotalCount] = useState(0);
  const [dbPage, setDbPage] = useState(1);
  const [isDbLoading, setIsDbLoading] = useState(false);
  const [dbError, setDbError] = useState(null);

  // Flagging State
  const [flagModalVehicle, setFlagModalVehicle] = useState(null);
  const [flagReason, setFlagReason] = useState('Stolen Vehicle');
  const [flagNote, setFlagNote] = useState('');
  const [isFlaggingLoading, setIsFlaggingLoading] = useState(false);
  const [flagToast, setFlagToast] = useState(null);

  // Clear Stale Vehicle Results
  const clearVehicleResults = () => {
    setVehicleMatches([]);
    setMovementHistory(null);
    setInvestigationError(null);
    setInvestigationStatus('idle');
  };

  const handleVehicleModeChange = (mode) => {
    setVehicleSearchMode(mode);
    clearVehicleResults();
  };

  // Primary Vehicle Search Handler
  const executeVehicleInvestigation = async (modeOverride = null) => {
    const activeMode = modeOverride || vehicleSearchMode;
    
    setVehicleMatches([]);
    setMovementHistory(null);
    setInvestigationError(null);
    setFlagToast(null);
    setIsSearchingVehicle(true);
    setInvestigationStatus('searching');

    try {
      if (activeMode === 'plate') {
        const p = plateInput.trim();
        if (!p) {
          setInvestigationError('Please enter a license plate number.');
          setInvestigationStatus('error');
          setIsSearchingVehicle(false);
          return;
        }

        const data = await searchVehicle({ 
          plate_number: p,
          location: plateLocation !== 'All' ? plateLocation : undefined,
          time_range: plateTimeRange !== 'all' ? plateTimeRange : undefined
        });

        if (data.matches && data.matches.length > 0) {
          setVehicleMatches(data.matches);
          setInvestigationStatus('found');
        } else {
          setInvestigationStatus('no_match');
        }

      } else if (activeMode === 'description') {
        const data = await searchVehicle({
          vehicle_type: descType !== 'All' ? descType : undefined,
          color: descColor !== 'All' ? descColor : undefined,
          location: descLocation !== 'All' ? descLocation : undefined,
          vehicle_model: descModel ? descModel.trim() : undefined,
          time_range: descTimeRange !== 'all' ? descTimeRange : undefined
        });

        if (data.matches && data.matches.length > 0) {
          setVehicleMatches(data.matches);
          setInvestigationStatus('found');
        } else {
          setInvestigationStatus('no_match');
        }
      }
    } catch (err) {
      console.error('Error executing vehicle search:', err);
      setInvestigationError(err.message || 'Vehicle search could not complete. Please retry.');
      setInvestigationStatus('error');
    } finally {
      setIsSearchingVehicle(false);
    }
  };

  // Load Historical Sightings on Demand
  const handleLoadMovementHistory = async (vehicleId) => {
    if (!vehicleId) return;
    setIsLoadingHistory(true);
    setHistoryError(null);
    try {
      const data = await getVehicleSightings(vehicleId);
      const items = Array.isArray(data) ? data : (data.sightings || []);
      setMovementHistory(items);
    } catch (err) {
      console.error('Error loading sightings history:', err);
      setHistoryError('Unable to load movement trajectory history.');
    } finally {
      setIsLoadingHistory(false);
    }
  };

  // Browse Database Drawer
  const handleBrowseDatabase = async (page = 1) => {
    setIsBrowsingDatabase(true);
    setIsDbLoading(true);
    setDbError(null);
    try {
      const data = await getVehicles(page, 25);
      setDbVehicles(data.items || []);
      setDbTotalCount(data.total || 0);
      setDbPage(page);
    } catch (err) {
      console.error('Error browsing vehicle database:', err);
      setDbError(err.message || 'Failed to load vehicle database.');
    } finally {
      setIsDbLoading(false);
    }
  };

  const handleSelectFromDatabase = (vehicle) => {
    setVehicleMatches([vehicle]);
    setInvestigationStatus('found');
    setMovementHistory(null);
    setIsBrowsingDatabase(false);
  };

  // Flagging Handlers
  const handleFlagSubmit = async () => {
    if (!flagModalVehicle) return;
    setIsFlaggingLoading(true);
    try {
      await flagVehicle(flagModalVehicle.vehicle_id, true, flagReason, flagNote);
      const updated = {
        ...flagModalVehicle,
        is_stolen: true,
        bolo_status: `CRITICAL BOLO: ${flagReason.toUpperCase()}`,
        flag_status: {
          is_flagged: true,
          reason: flagReason,
          note: flagNote,
          flagged_at: new Date().toISOString()
        }
      };
      
      setVehicleMatches(prev => prev.map(v => v.vehicle_id === updated.vehicle_id ? updated : v));
      if (selectedVehicleForModal?.vehicle_id === updated.vehicle_id) {
        setSelectedVehicleForModal(updated);
      }
      setFlagToast({ type: 'success', message: `Vehicle ${flagModalVehicle.plate} flagged successfully.` });
      setFlagModalVehicle(null);
    } catch (err) {
      console.error('Error flagging vehicle:', err);
      setFlagToast({ type: 'error', message: err.message || 'Could not flag vehicle.' });
    } finally {
      setIsFlaggingLoading(false);
    }
  };

  const handleUnflagSubmit = async (vehicle) => {
    if (!vehicle) return;
    setIsFlaggingLoading(true);
    try {
      await flagVehicle(vehicle.vehicle_id, false, null, null);
      const updated = {
        ...vehicle,
        is_stolen: false,
        bolo_status: 'NORMAL: Verified Vehicle Registry',
        flag_status: {
          is_flagged: false,
          reason: null,
          note: null,
          flagged_at: null
        }
      };
      setVehicleMatches(prev => prev.map(v => v.vehicle_id === updated.vehicle_id ? updated : v));
      if (selectedVehicleForModal?.vehicle_id === updated.vehicle_id) {
        setSelectedVehicleForModal(updated);
      }
      setFlagToast({ type: 'success', message: `Flag removed for ${vehicle.plate}.` });
    } catch (err) {
      console.error('Error removing flag:', err);
      setFlagToast({ type: 'error', message: err.message || 'Could not clear vehicle flag.' });
    } finally {
      setIsFlaggingLoading(false);
    }
  };

  // ==========================================
  // 2. VIDEO EVIDENCE & PERSON FINDER STATE
  // ==========================================
  const [videoSources, setVideoSources] = useState([]);
  const [isVideoSourcesLoading, setIsVideoSourcesLoading] = useState(false);
  const [isSourceDrawerOpen, setIsSourceDrawerOpen] = useState(false);
  const [isUploadVideoModalOpen, setIsUploadVideoModalOpen] = useState(false);
  const [uploadVideoFile, setUploadVideoFile] = useState(null);
  const [uploadSourceName, setUploadSourceName] = useState('');
  const [uploadLocation, setUploadLocation] = useState('');
  const [isUploadingVideo, setIsUploadingVideo] = useState(false);
  const [uploadProgressText, setUploadProgressText] = useState('');
  const [videoUploadError, setVideoUploadError] = useState(null);

  const [uploadedImage, setUploadedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [minSimilarity, setMinSimilarity] = useState(0.35);
  const [selectedSourceFilter, setSelectedSourceFilter] = useState('ALL');
  const [selectedTimeRange, setSelectedTimeRange] = useState('all');
  const [personSearchResults, setPersonSearchResults] = useState([]);
  const [personSearchStatus, setPersonSearchStatus] = useState('idle'); // 'idle' | 'searching' | 'found' | 'no_match' | 'error'
  const [isSearchingPerson, setIsSearchingPerson] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [personSearchError, setPersonSearchError] = useState(null);
  const [selectedPersonForModal, setSelectedPersonForModal] = useState(null);
  const fileInputRef = useRef(null);
  const videoFileInputRef = useRef(null);

  // Load Video Evidence Sources
  const loadVideoSources = async () => {
    setIsVideoSourcesLoading(true);
    try {
      const list = await getVideoEvidenceSources();
      setVideoSources(list || []);
    } catch (err) {
      console.error('Error loading video sources:', err);
    } finally {
      setIsVideoSourcesLoading(false);
    }
  };

  useEffect(() => {
    loadVideoSources();
  }, []);

  const handlePersonDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      setUploadedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setPersonSearchError(null);
      setPersonSearchResults([]);
      setPersonSearchStatus('idle');
    }
  };

  const handlePersonFileSelect = (e) => {
    const file = e.target.files[0];
    if (file && file.type.startsWith('image/')) {
      setUploadedImage(file);
      setImagePreview(URL.createObjectURL(file));
      setPersonSearchError(null);
      setPersonSearchResults([]);
      setPersonSearchStatus('idle');
    }
  };

  const [personSearchTotalEvaluated, setPersonSearchTotalEvaluated] = useState(0);

  const handlePersonSearch = async () => {
    if (!uploadedImage) return;
    setIsSearchingPerson(true);
    setPersonSearchStatus('searching');
    setPersonSearchError(null);
    setPersonSearchResults([]);
    setPersonSearchTotalEvaluated(0);
    
    try {
      const data = await searchPersonEvidence(
        uploadedImage,
        minSimilarity,
        selectedSourceFilter,
        selectedTimeRange,
        10
      );

      const matches = data.matches || [];
      const totalCandidates = data.total_candidates || matches.length;
      setPersonSearchTotalEvaluated(totalCandidates);

      const normalizedMatches = matches
        .map((m, idx) => {
          let rawSim = typeof m.similarity === 'number' ? m.similarity : 0;
          let simPercent = rawSim <= 1.0 ? Math.round(rawSim * 100) : Math.round(rawSim);
          simPercent = Math.min(100, Math.max(0, simPercent));
          return {
            ...m,
            rank: idx + 1,
            is_best_match: idx === 0,
            normalized_similarity: simPercent / 100.0,
            similarity_percent: simPercent
          };
        })
        .filter(m => m.normalized_similarity >= minSimilarity)
        .sort((a, b) => b.similarity_percent - a.similarity_percent);

      setPersonSearchResults(normalizedMatches);
      setPersonSearchStatus(normalizedMatches.length > 0 ? 'found' : 'no_match');
    } catch (err) {
      console.error('Error during person search:', err);
      setPersonSearchError(err.message || 'Failed to search video person gallery. Please try another reference photo.');
      setPersonSearchStatus('error');
    } finally {
      setIsSearchingPerson(false);
    }
  };

  const handleUploadVideoEvidence = async (e) => {
    e.preventDefault();
    if (!uploadVideoFile) return;

    setIsUploadingVideo(true);
    setVideoUploadError(null);
    setUploadProgressText('Uploading video evidence file...');

    try {
      const uploadRes = await uploadVideoEvidence(
        uploadVideoFile, 
        uploadSourceName, 
        'CAM-01', 
        uploadLocation
      );
      
      const sourceId = uploadRes.video?.source_id;
      setUploadProgressText(`Indexing video [${sourceId}] (YOLO11 Detection + ByteTrack + TransReID)...`);

      // Poll until ready or failed
      let isReady = false;
      let attempts = 0;
      while (!isReady && attempts < 60) {
        await new Promise(r => setTimeout(r, 2000));
        attempts++;
        const currentSources = await getVideoEvidenceSources();
        setVideoSources(currentSources || []);
        const target = currentSources.find(s => s.source_id === sourceId);
        if (target) {
          if (target.status === 'ready') {
            isReady = true;
            break;
          } else if (target.status === 'failed') {
            throw new Error(target.error_message || 'Video processing failed.');
          }
        }
      }

      await loadVideoSources();
      setIsUploadVideoModalOpen(false);
      setUploadVideoFile(null);
      setUploadSourceName('');
      setUploadLocation('');
      setFlagToast({ type: 'success', message: `Video evidence [${sourceId}] indexed into Person Finder gallery.` });
    } catch (err) {
      console.error('Error uploading video evidence:', err);
      setVideoUploadError(err.message || 'Failed to process video evidence.');
    } finally {
      setIsUploadingVideo(false);
      setUploadProgressText('');
    }
  };

  const handleDeleteVideo = async (sourceId) => {
    if (!confirm(`Remove video evidence source ${sourceId} from index?`)) return;
    try {
      await deleteVideoEvidence(sourceId);
      await loadVideoSources();
      if (selectedSourceFilter === sourceId) setSelectedSourceFilter('ALL');
      setFlagToast({ type: 'success', message: `Removed ${sourceId} from video index.` });
    } catch (err) {
      console.error('Error removing video source:', err);
      setFlagToast({ type: 'error', message: 'Failed to remove video evidence.' });
    }
  };

  // Lock scroll when any modal is open
  useEffect(() => {
    const isAnyModalOpen = selectedVehicleForModal || selectedPersonForModal || flagModalVehicle;
    if (isAnyModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [selectedVehicleForModal, selectedPersonForModal, flagModalVehicle]);

  // Handle global Escape key for modals
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setSelectedVehicleForModal(null);
        setSelectedPersonForModal(null);
        setFlagModalVehicle(null);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  return (
    <div className="h-full w-full flex flex-col bg-[#0A0A0A] text-[#e5e2e1] overflow-hidden select-none">
      {/* Sub-Header Layer Selector (ONLY Vehicle Finder and Person Finder) */}
      <div className="px-6 py-3 bg-[#111111] border-b border-[#222222] flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-[#181818] border border-[#2a2a2a] text-[#f5dfc0]">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-[#f5dfc0] font-sans tracking-wide">
              LAYER 3: IDENTIFY & RE-IDENTIFICATION
            </h1>
            <p className="text-[11px] font-mono text-[#858585]">
              Real-Time Entity Re-Identification & Biometric Trajectory Matching
            </p>
          </div>
        </div>

        {/* Sub-tab Navigation (strictly Vehicle Finder & Person Finder) */}
        <div className="flex items-center bg-[#0a0a0a] p-1 rounded-xl border border-[#262626]">
          <button
            onClick={() => handleSubTabChange('vehicle')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              activeSubTab === 'vehicle'
                ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                : 'text-[#858585] hover:text-[#e5e2e1]'
            }`}
          >
            <Car className="w-3.5 h-3.5" />
            VEHICLE FINDER
          </button>

          <button
            onClick={() => handleSubTabChange('person')}
            className={`flex items-center gap-2 px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all ${
              activeSubTab === 'person'
                ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                : 'text-[#858585] hover:text-[#e5e2e1]'
            }`}
          >
            <User className="w-3.5 h-3.5" />
            PERSON FINDER
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        
        {/* ========================================================================= */}
        {/* TAB 1: VEHICLE FINDER (PLATE NUMBER & VEHICLE DESCRIPTION)                */}
        {/* ========================================================================= */}
        {activeSubTab === 'vehicle' && (
          <div className="max-w-7xl mx-auto space-y-6">
            {/* Search Input Controller */}
            <div className="bg-[#141414] border border-[#262626] rounded-2xl p-6 shadow-2xl space-y-5">
              <div className="flex flex-wrap items-center justify-between border-b border-[#222] pb-4 gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <Car className="w-5 h-5 text-[#f5dfc0]" />
                    <h2 className="text-base font-mono uppercase tracking-wider text-[#f5dfc0] font-black">
                      VEHICLE RE-IDENTIFICATION & SIGHTING INVESTIGATION
                    </h2>
                  </div>
                  <p className="text-xs text-[#858585] mt-1 font-mono">
                    Search CCTV recordings by vehicle registration number or visual vehicle attributes.
                  </p>
                </div>

                {/* Search Mode Switcher (Plate Number vs Description) */}
                <div className="flex items-center bg-[#0a0a0a] p-1 rounded-xl border border-[#262626]">
                  <button
                    onClick={() => handleVehicleModeChange('plate')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
                      vehicleSearchMode === 'plate'
                        ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                        : 'text-[#858585] hover:text-[#e5e2e1]'
                    }`}
                  >
                    <FileText className="w-3.5 h-3.5" />
                    PLATE NUMBER
                  </button>

                  <button
                    onClick={() => handleVehicleModeChange('description')}
                    className={`px-4 py-1.5 rounded-lg text-xs font-mono font-bold transition-all flex items-center gap-1.5 ${
                      vehicleSearchMode === 'description'
                        ? 'bg-[#f5dfc0] text-[#0A0A0A] shadow-md'
                        : 'text-[#858585] hover:text-[#e5e2e1]'
                    }`}
                  >
                    <Filter className="w-3.5 h-3.5" />
                    VEHICLE DESCRIPTION
                  </button>
                </div>
              </div>

              {/* Mode-Specific Input Panel */}
              <div>
                {/* MODE 1: PLATE NUMBER INPUT */}
                {vehicleSearchMode === 'plate' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-12 gap-3">
                      <div className="md:col-span-6">
                        <label className="text-[11px] font-mono text-[#858585] uppercase tracking-wider block mb-1.5">
                          Enter License Plate Number:
                        </label>
                        <div className="relative">
                          <input
                            type="text"
                            placeholder="e.g. MH 46 CB 0005, MH 43 CG 3824"
                            value={plateInput}
                            onChange={(e) => {
                              setPlateInput(e.target.value);
                              clearVehicleResults();
                            }}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') executeVehicleInvestigation('plate');
                            }}
                            className="w-full px-4 py-3 rounded-xl bg-[#0a0a0a] border border-[#333333] focus:border-[#00F2FE] text-sm font-mono text-[#f5dfc0] font-black uppercase tracking-wider outline-none shadow-inner"
                          />
                          {plateInput && (
                            <button
                              onClick={() => {
                                setPlateInput('');
                                clearVehicleResults();
                              }}
                              className="absolute right-3 top-3 text-xs text-[#737373] hover:text-white"
                            >
                              Clear
                            </button>
                          )}
                        </div>
                      </div>

                      <div className="md:col-span-3">
                        <label className="text-[11px] font-mono text-[#858585] uppercase tracking-wider block mb-1.5">
                          Camera / Location (Optional):
                        </label>
                        <select
                          value={plateLocation}
                          onChange={(e) => {
                            setPlateLocation(e.target.value);
                            clearVehicleResults();
                          }}
                          className="w-full px-3 py-3 rounded-xl bg-[#0a0a0a] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                        >
                          <option value="All">All Cameras</option>
                          {availableCameras.map((cam) => (
                            <option key={cam.id} value={`CAM-0${cam.id}`}>
                              CAM-0{cam.id}: {cam.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="md:col-span-3">
                        <label className="text-[11px] font-mono text-[#858585] uppercase tracking-wider block mb-1.5">
                          Time Horizon:
                        </label>
                        <select
                          value={plateTimeRange}
                          onChange={(e) => {
                            setPlateTimeRange(e.target.value);
                            clearVehicleResults();
                          }}
                          className="w-full px-3 py-3 rounded-xl bg-[#0a0a0a] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                        >
                          <option value="all">Full Archive</option>
                          <option value="30m">Last 30 Min</option>
                          <option value="2h">Past 2 Hours</option>
                          <option value="24h">Past 24 Hours</option>
                        </select>
                      </div>
                    </div>
                  </div>
                )}

                {/* MODE 2: VEHICLE DESCRIPTION INPUT */}
                {vehicleSearchMode === 'description' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                      {/* Vehicle Type */}
                      <div>
                        <label className="text-[10px] font-mono text-[#858585] uppercase block mb-1">
                          Vehicle Type
                        </label>
                        <select
                          value={descType}
                          onChange={(e) => {
                            setDescType(e.target.value);
                            clearVehicleResults();
                          }}
                          className="w-full px-3 py-2.5 rounded-lg bg-[#0a0a0a] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                        >
                          <option value="All">All Vehicle Types</option>
                          <option value="Car">Sedan / Car</option>
                          <option value="SUV">SUV / Cruiser</option>
                          <option value="Motorcycle">Motorcycle</option>
                          <option value="Bus">Public Transit Bus</option>
                          <option value="Truck">Heavy Transport Truck</option>
                        </select>
                      </div>

                      {/* Make / Model */}
                      <div>
                        <label className="text-[10px] font-mono text-[#858585] uppercase block mb-1">
                          Make / Model (Optional)
                        </label>
                        <input
                          type="text"
                          placeholder="e.g. Toyota, Pulsar, Mahindra"
                          value={descModel}
                          onChange={(e) => {
                            setDescModel(e.target.value);
                            clearVehicleResults();
                          }}
                          className="w-full px-3 py-2.5 rounded-lg bg-[#0a0a0a] border border-[#333333] text-xs font-mono text-[#f5dfc0] outline-none focus:border-[#00F2FE]"
                        />
                      </div>

                      {/* Color */}
                      <div>
                        <label className="text-[10px] font-mono text-[#858585] uppercase block mb-1">
                          Color
                        </label>
                        <select
                          value={descColor}
                          onChange={(e) => {
                            setDescColor(e.target.value);
                            clearVehicleResults();
                          }}
                          className="w-full px-3 py-2.5 rounded-lg bg-[#0a0a0a] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                        >
                          <option value="All">All Colors</option>
                          <option value="Red">Red</option>
                          <option value="Blue">Blue</option>
                          <option value="Silver">Silver / Grey</option>
                          <option value="White">White</option>
                          <option value="Black">Black</option>
                          <option value="Yellow">Yellow</option>
                          <option value="Green">Green</option>
                        </select>
                      </div>

                      {/* Camera / Checkpoint Location */}
                      <div>
                        <label className="text-[10px] font-mono text-[#858585] uppercase block mb-1">
                          Camera / Checkpoint
                        </label>
                        <select
                          value={descLocation}
                          onChange={(e) => {
                            setDescLocation(e.target.value);
                            clearVehicleResults();
                          }}
                          className="w-full px-3 py-2.5 rounded-lg bg-[#0a0a0a] border border-[#333333] text-xs font-mono text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                        >
                          <option value="All">All Checkpoints</option>
                          {availableCameras.map((cam) => (
                            <option key={cam.id} value={`CAM-0${cam.id}`}>
                              CAM-0{cam.id}: {cam.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Time Horizon Buttons */}
                    <div className="flex flex-wrap items-center gap-2 pt-1">
                      <span className="text-[10px] font-mono text-[#858585] uppercase">
                        Time Horizon:
                      </span>
                      {[
                        { key: '30m', label: 'Last 30 Min' },
                        { key: '2h', label: 'Past 2 Hours' },
                        { key: '24h', label: 'Past 24 Hours' },
                        { key: 'all', label: 'Full Archive' }
                      ].map((tw) => (
                        <button
                          key={tw.key}
                          onClick={() => {
                            setDescTimeRange(tw.key);
                            clearVehicleResults();
                          }}
                          className={`px-3 py-1 rounded-md text-xs font-mono border transition ${
                            descTimeRange === tw.key
                              ? 'bg-[#f5dfc0] text-black font-bold border-[#f5dfc0]'
                              : 'bg-[#121212] text-[#858585] border-[#292929] hover:text-[#e5e2e1]'
                          }`}
                        >
                          {tw.label}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Action Button Bar */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#222222]">
                <div className="text-xs font-mono text-[#737373]">
                  {vehicleSearchMode === 'plate' && 'Exact & fuzzy license plate query across all recorded CCTV feeds.'}
                  {vehicleSearchMode === 'description' && 'Multi-attribute database query with time window.'}
                </div>

                <div className="flex items-center gap-3">
                  {investigationStatus !== 'idle' && (
                    <button
                      onClick={clearVehicleResults}
                      className="px-4 py-2 rounded-xl bg-[#1e1e1e] hover:bg-[#282828] text-xs font-mono text-[#a3a3a3] hover:text-white border border-[#333333] transition"
                    >
                      Reset
                    </button>
                  )}

                  <button
                    onClick={() => executeVehicleInvestigation()}
                    disabled={isSearchingVehicle}
                    className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] hover:opacity-95 text-[#0A0A0A] font-mono text-xs font-black shadow-lg shadow-cyan-950/50 transition transform hover:scale-[1.02] flex items-center gap-2"
                  >
                    {isSearchingVehicle ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        SEARCHING CCTV CORRIDORS...
                      </>
                    ) : (
                      <>
                        <Search className="w-4 h-4" />
                        FIND VEHICLE
                      </>
                    )}
                  </button>
                </div>
              </div>
            </div>

            {/* Dedicated Database Browser Drawer */}
            {isBrowsingDatabase && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-6 shadow-2xl space-y-4"
              >
                <div className="flex items-center justify-between border-b border-[#222] pb-4">
                  <div className="flex items-center gap-3">
                    <Car className="w-5 h-5 text-[#f5dfc0]" />
                    <div>
                      <h3 className="text-sm font-mono font-bold text-[#f5dfc0] uppercase">
                        LOGGED VEHICLE DATABASE ({dbTotalCount} REGISTERED FLEET RECORDS)
                      </h3>
                      <p className="text-[11px] font-mono text-[#858585]">
                        Page {dbPage} • Real-time database records with latest telemetry checkpoints
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setIsBrowsingDatabase(false)}
                    className="px-3 py-1.5 rounded-lg bg-[#222] hover:bg-[#333] text-xs font-mono text-[#e5e2e1] transition flex items-center gap-1.5"
                  >
                    <X className="w-4 h-4" /> Close Database View
                  </button>
                </div>

                {isDbLoading ? (
                  <div className="py-12 text-center text-xs font-mono text-[#858585] space-y-3">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-[#00F2FE]" />
                    <div>Loading logged vehicle records from database...</div>
                  </div>
                ) : dbError ? (
                  <div className="py-8 text-center bg-red-950/30 border border-red-900 rounded-xl p-6 space-y-3">
                    <AlertCircle className="w-8 h-8 text-red-400 mx-auto" />
                    <div className="text-xs font-mono text-red-200 font-bold">UNABLE TO LOAD VEHICLES</div>
                    <div className="text-[11px] font-mono text-red-300">{dbError}</div>
                    <button
                      onClick={() => handleBrowseDatabase(dbPage)}
                      className="px-4 py-1.5 rounded-lg bg-red-800 hover:bg-red-700 text-xs font-mono text-white font-bold transition"
                    >
                      Retry
                    </button>
                  </div>
                ) : dbVehicles.length === 0 ? (
                  <div className="py-12 text-center text-xs font-mono text-[#858585]">
                    No vehicles have been logged yet.
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[520px] overflow-y-auto pr-1">
                    {dbVehicles.map((v) => (
                      <div
                        key={v.vehicle_id}
                        onClick={() => handleSelectFromDatabase(v)}
                        className="p-3.5 bg-[#0d0d0d] hover:bg-[#181818] border border-[#262626] hover:border-[#00F2FE] rounded-xl transition cursor-pointer flex gap-3 items-center group"
                      >
                        <img
                          src={v.snapshot || '/snapshots/crop_vehicle_cam2_1.jpg'}
                          alt={v.plate}
                          className="w-20 h-16 object-cover rounded-lg border border-[#333] group-hover:border-cyan-400"
                        />
                        <div className="space-y-1 flex-1 min-w-0 font-mono">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-black text-[#f5dfc0] truncate">
                              {v.plate}
                            </span>
                            {v.is_stolen && (
                              <span className="px-1.5 py-0.2 text-[9px] font-bold bg-red-950 text-red-300 border border-red-800 rounded">
                                BOLO
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-[#858585] truncate">
                            {v.color} {v.type}
                          </div>
                          <div className="text-[10px] text-cyan-300 truncate">
                            {v.latest_sighting?.location || 'Corridor Checkpoint'}
                          </div>
                        </div>
                        <ChevronRight className="w-4 h-4 text-[#555] group-hover:text-white" />
                      </div>
                    ))}
                  </div>
                )}
              </motion.div>
            )}

            {/* VEHICLE MATCH CARDS (COMPACT & CLICKABLE) */}
            {investigationStatus === 'found' && vehicleMatches.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-mono uppercase text-[#f5dfc0] font-bold">
                    MATCHED VEHICLES ({vehicleMatches.length} Found)
                  </h3>
                  <span className="text-[11px] font-mono text-[#858585]">
                    Click any card to open detailed Forensic Profile
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {vehicleMatches.map((v) => (
                    <motion.div
                      key={v.vehicle_id}
                      whileHover={{ y: -2 }}
                      onClick={() => {
                        setSelectedVehicleForModal(v);
                        setMovementHistory(null);
                      }}
                      className="bg-[#141414] hover:bg-[#181818] border border-[#262626] hover:border-cyan-500/60 rounded-2xl p-5 cursor-pointer shadow-xl transition space-y-4 font-mono group"
                    >
                      {/* Top Row: Plate Badge & Match Confidence */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Car className="w-4 h-4 text-[#00F2FE]" />
                          <span className="text-xs font-bold text-[#f5dfc0] uppercase">
                            VEHICLE MATCH
                          </span>
                        </div>
                        <span className="px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-700 text-xs font-bold">
                          {Math.round((v.match_confidence || 0.95) * 100)}% MATCH
                        </span>
                      </div>

                      {/* License Plate Banner */}
                      <div className="flex items-center justify-between">
                        <div className="bg-yellow-400 text-black px-3 py-1.5 rounded border-2 border-black font-black text-sm tracking-wider inline-flex items-center gap-1.5">
                          <span className="text-[8px] bg-blue-800 text-white px-1 py-0.2 rounded">IND</span>
                          <span>{v.plate}</span>
                        </div>
                        {v.is_stolen && (
                          <span className="px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 text-[10px] font-bold">
                            FLAGGED BOLO
                          </span>
                        )}
                      </div>

                      {/* Description */}
                      <div className="text-xs text-[#e5e2e1] font-bold">
                        {v.model || 'Toyota Corolla'} · {v.color} · {v.type}
                      </div>

                      {/* Latest Sighting Summary */}
                      <div className="p-2.5 rounded-xl bg-[#0a0a0a] border border-[#222] text-xs space-y-1">
                        <div className="text-[10px] text-[#858585] uppercase">Last Known Sighting</div>
                        <div className="text-[#f5dfc0] font-bold truncate">
                          {v.latest_sighting?.camera_name || v.latest_sighting?.camera_id || 'CAM-01'} · {v.latest_sighting?.location || 'MG Road'}
                        </div>
                        <div className="text-[10px] text-cyan-300 flex justify-between">
                          <span>{v.latest_sighting?.timestamp || 'Recent'}</span>
                          <span>{v.latest_sighting?.speed_kmh || 55} km/h</span>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center justify-between pt-1 border-t border-[#222]">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (v.is_stolen) {
                              handleUnflagSubmit(v);
                            } else {
                              setFlagModalVehicle(v);
                            }
                          }}
                          className={`text-xs font-bold transition ${
                            v.is_stolen ? 'text-red-400 hover:text-red-300' : 'text-[#858585] hover:text-red-400'
                          }`}
                        >
                          {v.is_stolen ? '[ CLEAR FLAG ]' : '[ FLAG VEHICLE ]'}
                        </button>

                        <span className="text-xs font-bold text-[#00F2FE] group-hover:underline flex items-center gap-1">
                          [ VIEW DETAILS ]
                        </span>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* No Match State */}
            {investigationStatus === 'no_match' && (
              <div className="bg-[#141414] border border-[#262626] rounded-2xl p-10 text-center space-y-3">
                <AlertCircle className="w-8 h-8 text-yellow-400 mx-auto" />
                <h3 className="text-sm font-mono uppercase text-[#f5dfc0] font-bold">
                  NO MATCHING VEHICLE
                </h3>
                <p className="text-xs font-mono text-[#858585] max-w-md mx-auto">
                  No vehicle in recorded CCTV corridors matches the search criteria.
                </p>
              </div>
            )}

            {/* Error State */}
            {investigationStatus === 'error' && (
              <div className="bg-[#141414] border border-red-900/50 rounded-2xl p-10 text-center space-y-4 shadow-2xl">
                <AlertOctagon className="w-10 h-10 text-red-400 mx-auto" />
                <h3 className="text-base font-mono uppercase text-red-200 font-black tracking-wide">
                  SEARCH ERROR
                </h3>
                <p className="text-xs font-mono text-red-300 max-w-md mx-auto">
                  {investigationError || 'The vehicle search service could not complete the request.'}
                </p>
                <button
                  onClick={() => executeVehicleInvestigation()}
                  className="px-5 py-2 rounded-xl bg-red-800 hover:bg-red-700 text-xs font-mono text-white font-bold transition"
                >
                  RETRY
                </button>
              </div>
            )}

            {/* Idle State */}
            {investigationStatus === 'idle' && (
              <div className="border border-dashed border-[#262626] rounded-2xl p-12 text-center space-y-3 bg-[#0d0d0d]">
                <ShieldCheck className="w-10 h-10 text-[#555] mx-auto" />
                <h3 className="text-sm font-mono uppercase text-[#858585] font-bold">
                  VEHICLE IDENTIFICATION READY
                </h3>
                <p className="text-xs font-mono text-[#555] max-w-md mx-auto">
                  Enter a license plate or configure visual attributes above and click "FIND VEHICLE".
                </p>
              </div>
            )}

            {/* Discrete Database Access */}
            <div className="text-center pt-2 pb-4">
              <button
                onClick={() => handleBrowseDatabase(1)}
                className="text-[11px] font-mono text-[#666] hover:text-[#00F2FE] underline transition cursor-pointer"
              >
                Browse detection database ({dbTotalCount || 25} logged vehicles in registry)
              </button>
            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: PERSON FINDER (MISSING PERSON & VIDEO EVIDENCE INVESTIGATION)       */}
        {/* ========================================================================= */}
        {activeSubTab === 'person' && (
          <div className="max-w-7xl mx-auto space-y-6">
            
            {/* Top Toolbar: Video Evidence Sources Drawer / Manager */}
            <div className="bg-[#111111] border border-[#262626] rounded-2xl p-5 shadow-xl space-y-4 font-mono">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#222] pb-3">
                <div className="flex items-center gap-2.5">
                  <Video className="w-5 h-5 text-[#00F2FE]" />
                  <div>
                    <h3 className="text-xs font-bold text-[#f5dfc0] uppercase tracking-wider">
                      CCTV & Video Evidence Sources ({videoSources.length} Active Feeds)
                    </h3>
                    <p className="text-[10px] text-[#858585]">
                      Videos processed into track clusters & 128-D appearance embeddings
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-2.5">
                  <button
                    onClick={() => setIsSourceDrawerOpen(!isSourceDrawerOpen)}
                    className="px-3 py-1.5 rounded-xl bg-[#1a1a1a] hover:bg-[#252525] text-xs text-[#cfc5b9] border border-[#333] transition flex items-center gap-1.5"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    {isSourceDrawerOpen ? 'Hide Sources' : 'Manage Sources'}
                  </button>

                  <button
                    onClick={() => setIsUploadVideoModalOpen(true)}
                    className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] text-[#0A0A0A] font-black text-xs uppercase tracking-wider transition hover:opacity-95 shadow flex items-center gap-1.5"
                  >
                    <Upload className="w-3.5 h-3.5" />
                    + Add Video Evidence
                  </button>
                </div>
              </div>

              {/* Collapsible Source List */}
              {isSourceDrawerOpen && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  className="space-y-3 pt-1"
                >
                  {videoSources.length === 0 ? (
                    <div className="p-4 bg-[#0a0a0a] rounded-xl border border-[#222] text-center text-xs text-[#666]">
                      No video evidence processed yet. Click "+ Add Video Evidence" to upload CCTV footage files.
                    </div>
                  ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {videoSources.map((v) => (
                        <div
                          key={v.source_id}
                          className="p-3.5 bg-[#0d0d0d] border border-[#222] rounded-xl space-y-2 text-xs flex flex-col justify-between"
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-[#f5dfc0] flex items-center gap-1.5">
                              <span className="w-2 h-2 rounded-full bg-emerald-400" />
                              {v.source_id}
                            </span>
                            <span className="px-2 py-0.5 rounded bg-[#1c1c1c] text-cyan-300 text-[10px] font-bold border border-[#333]">
                              {v.track_count} Tracks ({v.sighting_count} Sightings)
                            </span>
                          </div>

                          <div className="text-[11px] text-[#ccc] font-medium truncate">
                            {v.source_name}
                          </div>

                          <div className="flex items-center justify-between text-[10px] text-[#777] pt-1 border-t border-[#1a1a1a]">
                            <span>{v.location}</span>
                            <span>{Math.round(v.duration_sec)}s @ {v.fps} FPS</span>
                            <button
                              onClick={() => handleDeleteVideo(v.source_id)}
                              className="text-red-400 hover:text-red-300 underline"
                            >
                              Remove
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </motion.div>
              )}
            </div>

            {/* MISSING PERSON SEARCH QUERY CARD */}
            <div className="bg-[#141414] border border-[#262626] rounded-2xl p-6 shadow-2xl space-y-5 font-mono">
              <div className="border-b border-[#222] pb-4">
                <div className="flex items-center gap-2">
                  <User className="w-5 h-5 text-[#f5dfc0]" />
                  <h2 className="text-base uppercase tracking-wider text-[#f5dfc0] font-black">
                    MISSING PERSON RE-IDENTIFICATION & VIDEO EVIDENCE SEARCH
                  </h2>
                </div>
                <p className="text-xs text-[#858585] mt-1">
                  Search uploaded CCTV/video evidence for visually similar person sightings across camera corridors.
                </p>
              </div>

              {/* Upload Dropzone */}
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handlePersonDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition ${
                  isDragging ? 'border-[#00F2FE] bg-cyan-950/20' : 'border-[#333] hover:border-[#f5dfc0] bg-[#0a0a0a]'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handlePersonFileSelect}
                  className="hidden"
                />
                {imagePreview ? (
                  <div className="flex items-center justify-center gap-4">
                    <img src={imagePreview} alt="Reference Person" className="w-20 h-24 object-cover rounded-lg border border-cyan-400" />
                    <div className="text-left">
                      <div className="text-xs font-bold text-[#f5dfc0]">MISSING PERSON REFERENCE PHOTO LOADED</div>
                      <div className="text-[11px] text-[#858585]">Click to select a different reference photograph</div>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="w-8 h-8 text-[#858585] mx-auto" />
                    <div className="text-xs font-bold text-[#e5e2e1]">Click to Browse or Drag Reference Photo Here</div>
                    <div className="text-[10px] text-[#737373]">Extracts 512-D Deep OSNet Appearance Embedding & searches indexed CCTV footage</div>
                  </div>
                )}
              </div>

              {/* Search Controls Toolbar */}
              <div className="flex flex-wrap items-center justify-between gap-4 pt-2">
                <div className="flex flex-wrap items-center gap-4 text-xs">
                  {/* Dynamic Video Evidence Source Filter */}
                  <div>
                    <label className="text-[10px] text-[#858585] block mb-1 uppercase">Search Source Filter</label>
                    <select
                      value={selectedSourceFilter}
                      onChange={(e) => {
                        setSelectedSourceFilter(e.target.value);
                        setPersonSearchResults([]);
                        setPersonSearchStatus('idle');
                      }}
                      className="px-3 py-1.5 rounded-lg bg-[#0a0a0a] border border-[#333] text-[#e5e2e1] outline-none focus:border-[#00F2FE]"
                    >
                      <option value="ALL">All Video Evidence Sources</option>
                      {videoSources.map((vs) => (
                        <option key={vs.source_id} value={vs.source_id}>
                          {vs.source_id}: {vs.source_name} ({vs.track_count} Tracks)
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Minimum Similarity Slider */}
                  <div>
                    <label className="text-[10px] text-[#858585] block mb-1 uppercase">
                      Min Match Score: {Math.round(minSimilarity * 100)}%
                    </label>
                    <input
                      type="range"
                      min="0.10"
                      max="0.95"
                      step="0.05"
                      value={minSimilarity}
                      onChange={(e) => {
                        setMinSimilarity(parseFloat(e.target.value));
                        setPersonSearchResults([]);
                        setPersonSearchStatus('idle');
                      }}
                      className="w-32 accent-[#00F2FE] cursor-pointer"
                    />
                  </div>
                </div>

                <button
                  onClick={handlePersonSearch}
                  disabled={!uploadedImage || isSearchingPerson}
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] hover:opacity-95 text-black font-black text-xs uppercase tracking-wider transition flex items-center gap-2 disabled:opacity-50 shadow-lg"
                >
                  {isSearchingPerson ? (
                    <>
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      SEARCHING VIDEO EVIDENCE...
                    </>
                  ) : (
                    <>
                      <Search className="w-4 h-4" />
                      SEARCH VIDEO EVIDENCE
                    </>
                  )}
                </button>
              </div>

              {personSearchError && (
                <div className="p-3 rounded-lg bg-red-950/50 border border-red-800 text-xs text-red-200">
                  {personSearchError}
                </div>
              )}
            </div>

            {/* PERSON MATCH CARDS (ACTUAL REAL VIDEO PERSON CROPS) */}
            {personSearchStatus === 'found' && personSearchResults.length > 0 && (
              <div className="space-y-4 font-mono">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-[#222] pb-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <h3 className="text-xs uppercase text-[#f5dfc0] font-bold tracking-wider">
                      MATCHED CANDIDATES ({personSearchResults.length} BEST {personSearchResults.length === 1 ? 'MATCH' : 'MATCHES'})
                    </h3>
                  </div>
                  <span className="text-[11px] text-[#858585]">
                    {personSearchTotalEvaluated > personSearchResults.length 
                      ? `${personSearchTotalEvaluated} candidates evaluated · Top ${personSearchResults.length} shown` 
                      : 'Ranked by TransReID visual similarity'}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pb-8">
                  {personSearchResults.map((p, pIdx) => {
                    const cropUrl = p.representative_crop_url || p.evidence_image_url || p.representative_crop || `/api/person/evidence/${p.source_id}/${p.track_id}`;
                    return (
                      <motion.div
                        key={`${p.source_id}-${p.track_id}-${pIdx}`}
                        whileHover={{ y: -2 }}
                        onClick={() => setSelectedPersonForModal(p)}
                        className={`bg-[#141414] hover:bg-[#181818] border rounded-2xl p-5 cursor-pointer shadow-xl transition space-y-3 group ${
                          p.is_best_match || pIdx === 0 
                            ? 'border-emerald-500/70 shadow-emerald-950/20' 
                            : 'border-[#262626] hover:border-cyan-500/60'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-[#00F2FE]" />
                            <span className="text-xs font-bold text-[#f5dfc0]">
                              PERSON TRACK: {p.track_id}
                            </span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {(p.is_best_match || pIdx === 0) && (
                              <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 text-[9px] font-bold">
                                ★ BEST MATCH
                              </span>
                            )}
                            <span className="px-2.5 py-0.5 rounded-full bg-cyan-950 text-cyan-300 border border-cyan-700 text-xs font-bold">
                              {p.similarity_percent}% MATCH
                            </span>
                          </div>
                        </div>

                        <div className="flex gap-3 items-center">
                          <div className="w-20 h-28 rounded-lg overflow-hidden border border-[#333] flex-shrink-0 bg-[#0a0a0a] relative flex items-center justify-center">
                            <img
                              src={cropUrl}
                              alt={`Track ${p.track_id}`}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.target.style.display = 'none';
                                const fallback = e.target.parentElement.querySelector('.fallback-icon');
                                if (fallback) fallback.style.display = 'flex';
                              }}
                            />
                            <div className="fallback-icon hidden flex-col items-center justify-center p-2 text-center text-[#666]">
                              <User className="w-6 h-6 mb-1 text-[#444]" />
                              <span className="text-[9px] leading-tight">EVIDENCE CROP</span>
                            </div>
                          </div>

                          <div className="space-y-1 min-w-0 flex-1 text-xs">
                            <div className="font-bold text-[#e5e2e1] truncate">{p.camera_name || p.source_name || p.source_id}</div>
                            <div className="text-[10px] text-[#858585] truncate">Location: {p.location || 'Surveillance Sector'}</div>
                            <div className="text-[10px] text-cyan-300 truncate">
                              {p.sighting_count || p.detection_count || 1} confirmed sighting(s)
                            </div>
                            <div className="text-[10px] text-yellow-400">
                              Timeline: {p.first_seen || '00:00'} → {p.last_seen || p.first_seen || '00:00'}
                            </div>
                          </div>
                        </div>

                        {/* Latest Confirmed Sighting Card */}
                        {p.sightings && p.sightings.length > 0 && (
                          <div className="p-2.5 rounded-xl bg-[#0a0a0a] border border-[#222] text-xs space-y-1">
                            <div className="text-[10px] text-[#858585] uppercase">Evidence Telemetry</div>
                            <div className="text-[#f5dfc0] font-bold truncate text-[11px]">
                              {p.camera_id || p.source_id}: {p.camera_name || p.source_name}
                            </div>
                            <div className="text-[10px] text-[#858585] truncate">
                              Occurrences: {p.sightings.map(s => s.formatted_time || `${Math.round(s.timestamp_sec || 0)}s`).join(', ')}
                            </div>
                          </div>
                        )}

                        <div className="pt-2 border-t border-[#222] text-right">
                          <span className="text-xs font-bold text-[#00F2FE] group-hover:underline">
                            [ VIEW FORENSIC DETAILS ]
                          </span>
                        </div>
                      </motion.div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* No Match State */}
            {personSearchStatus === 'no_match' && (
              <div className="bg-[#141414] border border-[#262626] rounded-2xl p-10 text-center space-y-3 font-mono">
                <AlertCircle className="w-8 h-8 text-yellow-400 mx-auto" />
                <h3 className="text-sm uppercase text-[#f5dfc0] font-bold">
                  NO MATCH FOUND
                </h3>
                <p className="text-xs text-[#858585] max-w-md mx-auto">
                  No candidate person sighting in the selected video evidence exceeded the similarity threshold (&ge; {Math.round(minSimilarity * 100)}%). Try lowering the threshold or uploading additional video footage.
                </p>
              </div>
            )}

            {/* Empty Initial State */}
            {personSearchStatus === 'idle' && (
              <div className="bg-[#141414] border border-[#262626] rounded-2xl p-10 text-center space-y-3 font-mono">
                <User className="w-10 h-10 text-[#444] mx-auto" />
                <h3 className="text-sm uppercase text-[#858585] font-bold">
                  PERSON IDENTIFICATION READY
                </h3>
                <p className="text-xs text-[#555] max-w-md mx-auto">
                  Upload a missing-person reference photo and click "SEARCH VIDEO EVIDENCE" to identify matching individuals across CCTV footage.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ========================================================================= */}
      {/* 3. VEHICLE FORENSIC PROFILE MODAL                                         */}
      {/* ========================================================================= */}
      <AnimatePresence>
        {selectedVehicleForModal && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md"
            onClick={() => setSelectedVehicleForModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 10 }}
              className="w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl border border-white/[0.08] bg-[#0d0e12] shadow-2xl text-[#e5e2e1] overflow-hidden font-mono"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 bg-[#12131a] border-b border-white/[0.06] flex-shrink-0">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[#1a1c24] border border-white/[0.08] text-[#f5dfc0]">
                    <Car className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#f5dfc0] uppercase">
                      VEHICLE FORENSIC PROFILE
                    </h3>
                    <p className="text-[11px] text-[#858585]">
                      {selectedVehicleForModal.plate} · Investigation Record #{selectedVehicleForModal.vehicle_id}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedVehicleForModal(null)}
                  className="p-1.5 rounded-lg bg-[#1a1c24] hover:bg-[#252834] text-[#cfc5b9] hover:text-[#f5dfc0]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Body */}
              <div className="overflow-y-auto flex-1 p-5 space-y-5">
                {/* CCTV Image */}
                <div className="relative aspect-video max-h-[45vh] bg-[#06070a] rounded-xl overflow-hidden border border-white/[0.06] flex items-center justify-center">
                  {selectedVehicleForModal.latest_sighting?.evidence_image || selectedVehicleForModal.snapshot ? (
                    <img
                      src={selectedVehicleForModal.latest_sighting?.evidence_image || selectedVehicleForModal.snapshot}
                      alt="Vehicle Evidence"
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <div className="text-center p-6 text-xs text-[#666]">
                      CCTV EVIDENCE UNAVAILABLE
                    </div>
                  )}
                </div>

                {/* Compact Metadata Table */}
                <div className="bg-[#12131a] border border-white/[0.06] rounded-xl overflow-hidden text-xs">
                  <div className="grid grid-cols-2 divide-x divide-y divide-white/[0.06]">
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">PLATE</span>
                      <span className="font-bold text-yellow-400">{selectedVehicleForModal.plate}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">VEHICLE TYPE</span>
                      <span className="font-bold text-[#e5e2e1]">{selectedVehicleForModal.type}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">MAKE / MODEL</span>
                      <span className="font-bold text-[#e5e2e1]">{selectedVehicleForModal.model}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">COLOR</span>
                      <span className="font-bold text-[#e5e2e1]">{selectedVehicleForModal.color}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">MATCH CONFIDENCE</span>
                      <span className="font-bold text-emerald-400">{Math.round((selectedVehicleForModal.match_confidence || 0.95) * 100)}%</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">CAMERA</span>
                      <span className="font-bold text-cyan-300">{selectedVehicleForModal.latest_sighting?.camera_id || 'CAM-01'}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">LOCATION</span>
                      <span className="font-bold text-[#e5e2e1] truncate">{selectedVehicleForModal.latest_sighting?.location || 'MG Road Corridor'}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">TIMESTAMP</span>
                      <span className="font-bold text-[#f5dfc0]">{selectedVehicleForModal.latest_sighting?.timestamp || 'Recent'}</span>
                    </div>
                  </div>
                </div>

                {/* Movement History on Demand */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-[#f5dfc0] uppercase">MOVEMENT HISTORY</span>
                    {!movementHistory && (
                      <button
                        onClick={() => handleLoadMovementHistory(selectedVehicleForModal.vehicle_id)}
                        disabled={isLoadingHistory}
                        className="px-3 py-1 rounded bg-[#1e202b] hover:bg-[#282b3a] text-cyan-300 text-xs font-bold border border-cyan-800/40"
                      >
                        {isLoadingHistory ? 'Fetching...' : '[ VIEW MOVEMENT HISTORY ]'}
                      </button>
                    )}
                  </div>

                  {movementHistory && (
                    <div className="space-y-2">
                      {movementHistory.map((s, sIdx) => (
                        <div key={sIdx} className="p-2.5 rounded-lg bg-[#0e0f14] border border-white/[0.06] flex items-center justify-between text-xs">
                          <div>
                            <div className="font-bold text-[#e5e2e1]">{s.location}</div>
                            <div className="text-[10px] text-[#858585]">
                              {s.camera_id} • Velocity: {s.speed_kmh || 0} km/h • GPS: {typeof s.latitude === 'number' ? s.latitude.toFixed(4) : (s.latitude || '0.0000')}, {typeof s.longitude === 'number' ? s.longitude.toFixed(4) : (s.longitude || '0.0000')}
                            </div>

                          </div>
                          <div className="text-right text-[#f5dfc0] font-bold">{s.timestamp}</div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>

              {/* Footer Actions */}
              <div className="p-4 bg-[#12131a] border-t border-white/[0.06] flex items-center justify-between flex-shrink-0">
                <button
                  onClick={() => {
                    const v = selectedVehicleForModal;
                    if (v.is_stolen) {
                      handleUnflagSubmit(v);
                    } else {
                      setFlagModalVehicle(v);
                    }
                  }}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition ${
                    selectedVehicleForModal.is_stolen
                      ? 'bg-emerald-950 text-emerald-200 border border-emerald-700'
                      : 'bg-red-900/60 hover:bg-red-800 text-red-100 border border-red-700'
                  }`}
                >
                  {selectedVehicleForModal.is_stolen ? 'CLEAR FLAG' : 'FLAG VEHICLE'}
                </button>

                <button
                  onClick={() => setSelectedVehicleForModal(null)}
                  className="px-4 py-2 rounded-xl bg-[#222] hover:bg-[#333] text-xs text-[#e5e2e1]"
                >
                  Close
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ========================================================================= */}
      {/* 4. PERSON FORENSIC PROFILE MODAL                                          */}
      {/* ========================================================================= */}
      <AnimatePresence>
        {selectedPersonForModal && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md font-mono"
            onClick={() => setSelectedPersonForModal(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0, y: 10 }}
              animate={{ scale: 1, opacity: 1, y: 0 }}
              exit={{ scale: 0.95, opacity: 0, y: 10 }}
              className="w-full max-w-3xl max-h-[90vh] flex flex-col rounded-2xl border border-white/[0.08] bg-[#0d0e12] shadow-2xl text-[#e5e2e1] overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header */}
              <div className="flex items-center justify-between p-4 bg-[#12131a] border-b border-white/[0.06] flex-shrink-0">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-[#1a1c24] border border-white/[0.08] text-[#00F2FE]">
                    <User className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#f5dfc0] uppercase">
                      MISSING PERSON RE-IDENTIFICATION PROFILE
                    </h3>
                    <p className="text-[11px] text-[#858585]">
                      PERSON TRACK: {selectedPersonForModal.track_id} · Video Evidence Investigation
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedPersonForModal(null)}
                  className="p-1.5 rounded-lg bg-[#1a1c24] hover:bg-[#252834] text-[#cfc5b9] hover:text-[#f5dfc0]"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="overflow-y-auto flex-1 p-5 space-y-5">
                {/* Side-by-Side Visual Comparison: Reference vs Matched Video Crop */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Reference Image */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase text-[#858585] block">
                      QUERY REFERENCE PHOTOGRAPH
                    </span>
                    <div className="relative aspect-[3/4] max-h-[36vh] bg-[#06070a] rounded-xl overflow-hidden border border-cyan-500/40 flex items-center justify-center">
                      {imagePreview ? (
                        <img
                          src={imagePreview}
                          alt="Query Reference"
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <div className="text-xs text-[#555]">REFERENCE NOT LOADED</div>
                      )}
                      <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/80 text-[10px] text-cyan-300 font-bold border border-cyan-800">
                        INPUT QUERY
                      </div>
                    </div>
                  </div>

                  {/* Matched Video Evidence Crop */}
                  <div className="space-y-1.5">
                    <span className="text-[10px] uppercase text-[#858585] block">
                      BEST MATCHED CCTV VIDEO CROP
                    </span>
                    <div className="relative aspect-[3/4] max-h-[36vh] bg-[#06070a] rounded-xl overflow-hidden border border-emerald-500/40 flex items-center justify-center">
                      <img
                        src={selectedPersonForModal.representative_crop_url || selectedPersonForModal.evidence_image_url || selectedPersonForModal.representative_crop || `/api/person/evidence/${selectedPersonForModal.source_id}/${selectedPersonForModal.track_id}`}
                        alt="Matched Evidence"
                        className="w-full h-full object-contain"
                        onError={(e) => {
                          e.target.style.display = 'none';
                          const fb = e.target.parentElement.querySelector('.modal-fallback');
                          if (fb) fb.style.display = 'flex';
                        }}
                      />
                      <div className="modal-fallback hidden flex-col items-center justify-center p-4 text-center text-[#777]">
                        <User className="w-8 h-8 mb-2 text-[#444]" />
                        <span className="text-xs">EVIDENCE IMAGE UNAVAILABLE</span>
                      </div>
                      <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-emerald-950/90 text-[10px] text-emerald-300 font-bold border border-emerald-700">
                        {selectedPersonForModal.similarity_percent}% SIMILARITY
                      </div>
                    </div>
                  </div>
                </div>

                {/* Details Table */}
                <div className="bg-[#12131a] border border-white/[0.06] rounded-xl overflow-hidden text-xs">
                  <div className="grid grid-cols-2 divide-x divide-y divide-white/[0.06]">
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">TRACK ID</span>
                      <span className="font-bold text-[#f5dfc0]">{selectedPersonForModal.track_id}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">MATCH SCORE</span>
                      <span className="font-bold text-emerald-400">{selectedPersonForModal.similarity_percent}%</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">SOURCE FEED</span>
                      <span className="font-bold text-[#e5e2e1] truncate">{selectedPersonForModal.camera_name || selectedPersonForModal.source_name || selectedPersonForModal.source_id}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">LOCATION</span>
                      <span className="font-bold text-[#e5e2e1] truncate">{selectedPersonForModal.location || 'Surveillance Sector'}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">TIMELINE</span>
                      <span className="font-bold text-yellow-400">{selectedPersonForModal.first_seen || '00:00'} → {selectedPersonForModal.last_seen || selectedPersonForModal.first_seen || '00:00'}</span>
                    </div>
                    <div className="p-2.5 flex justify-between">
                      <span className="text-[#858585]">TOTAL SIGHTINGS</span>
                      <span className="font-bold text-cyan-300">{selectedPersonForModal.sighting_count || selectedPersonForModal.detection_count || 1} confirmed frame(s)</span>
                    </div>
                  </div>
                </div>

                {/* Sighting Timeline */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-[#f5dfc0] uppercase">
                    EVIDENCE SIGHTING OCCURRENCES ({selectedPersonForModal.sightings?.length || 1})
                  </span>
                  
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {selectedPersonForModal.sightings?.map((s, sIdx) => {
                      const sCropUrl = s.crop_url || s.evidence_image_url || s.crop_path || `/api/person/evidence/${selectedPersonForModal.source_id}/${selectedPersonForModal.track_id}`;
                      return (
                        <div key={sIdx} className="p-3 rounded-lg bg-[#0e0f14] border border-white/[0.06] flex items-center justify-between text-xs">
                          <div className="flex items-center gap-3">
                            <div className="w-12 h-14 rounded border border-[#333] bg-black flex-shrink-0 overflow-hidden flex items-center justify-center">
                              <img
                                src={sCropUrl}
                                alt={`Sighting ${sIdx+1}`}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                  e.target.style.display = 'none';
                                  e.target.parentElement.innerHTML = '<span class="text-[9px] text-[#666]">FRAME</span>';
                                }}
                              />
                            </div>
                            <div>
                              <div className="font-bold text-[#e5e2e1]">Sighting Occurrence #{sIdx + 1}</div>
                              <div className="text-[10px] text-[#858585]">Confidence: {Math.round((s.confidence || 0.90) * 100)}%</div>
                            </div>
                          </div>
                          <div className="text-right">
                            <span className="px-2 py-0.5 rounded bg-[#1c1c1c] text-yellow-400 font-bold text-[11px] border border-[#333]">
                              {s.formatted_time || `${Math.round(s.timestamp_sec || 0)}s`}
                            </span>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>

              <div className="p-4 bg-[#12131a] border-t border-white/[0.06] flex justify-end flex-shrink-0">
                <button
                  onClick={() => setSelectedPersonForModal(null)}
                  className="px-5 py-2 rounded-xl bg-[#222] hover:bg-[#333] text-xs text-[#e5e2e1]"
                >
                  Dismiss Profile
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ========================================================================= */}
      {/* 4B. UPLOAD CCTV / VIDEO EVIDENCE MODAL                                    */}
      {/* ========================================================================= */}
      <AnimatePresence>
        {isUploadVideoModalOpen && (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md font-mono"
            onClick={() => !isUploadingVideo && setIsUploadVideoModalOpen(false)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#141414] border border-[#2a2a2a] rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4 text-[#e5e2e1]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-[#222] pb-3">
                <div className="flex items-center gap-2">
                  <Video className="w-5 h-5 text-[#00F2FE]" />
                  <h3 className="text-sm font-bold text-[#f5dfc0] uppercase">
                    Add CCTV / Video Evidence
                  </h3>
                </div>
                {!isUploadingVideo && (
                  <button onClick={() => setIsUploadVideoModalOpen(false)} className="text-[#858585] hover:text-white">
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              <form onSubmit={handleUploadVideoEvidence} className="space-y-4 text-xs">
                {/* File Dropzone */}
                <div
                  onClick={() => !isUploadingVideo && videoFileInputRef.current?.click()}
                  className="p-6 border-2 border-dashed border-[#333] hover:border-[#00F2FE] rounded-xl text-center cursor-pointer bg-[#0a0a0a]"
                >
                  <input
                    ref={videoFileInputRef}
                    type="file"
                    accept="video/mp4,video/avi,video/quicktime,video/x-matroska,video/webm,.mp4,.avi,.mov,.mkv,.webm"
                    onChange={(e) => setUploadVideoFile(e.target.files[0] || null)}
                    className="hidden"
                  />
                  {uploadVideoFile ? (
                    <div className="space-y-1">
                      <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto" />
                      <div className="font-bold text-[#f5dfc0]">{uploadVideoFile.name}</div>
                      <div className="text-[10px] text-[#858585]">
                        {(uploadVideoFile.size / (1024 * 1024)).toFixed(2)} MB • Ready for ingestion
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-1">
                      <Upload className="w-6 h-6 text-[#777] mx-auto" />
                      <div className="font-bold text-[#e5e2e1]">Click to Select Video File</div>
                      <div className="text-[10px] text-[#666]">Supports MP4, AVI, MOV, MKV, WEBM</div>
                    </div>
                  )}
                </div>

                <div>
                  <label className="text-[10px] text-[#858585] uppercase block mb-1">
                    Feed / Camera Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={uploadSourceName}
                    onChange={(e) => setUploadSourceName(e.target.value)}
                    placeholder="e.g. CCTV Terminal Entrance Gate 4"
                    disabled={isUploadingVideo}
                    className="w-full px-3 py-2 rounded-lg bg-[#0a0a0a] border border-[#333] text-xs text-[#f5dfc0] outline-none"
                  />
                </div>

                <div>
                  <label className="text-[10px] text-[#858585] uppercase block mb-1">
                    Location Description (Optional)
                  </label>
                  <input
                    type="text"
                    value={uploadLocation}
                    onChange={(e) => setUploadLocation(e.target.value)}
                    placeholder="e.g. Commercial Corridor East"
                    disabled={isUploadingVideo}
                    className="w-full px-3 py-2 rounded-lg bg-[#0a0a0a] border border-[#333] text-xs text-[#e5e2e1] outline-none"
                  />
                </div>

                {videoUploadError && (
                  <div className="p-3 bg-red-950/40 border border-red-800 rounded-lg text-red-200 text-xs">
                    {videoUploadError}
                  </div>
                )}

                {isUploadingVideo && (
                  <div className="p-3 bg-[#1c1c1c] border border-cyan-800 rounded-xl space-y-2">
                    <div className="flex items-center gap-2 text-cyan-300 font-bold text-xs">
                      <RefreshCw className="w-4 h-4 animate-spin" />
                      <span>{uploadProgressText}</span>
                    </div>
                    <div className="w-full bg-[#111] h-1.5 rounded-full overflow-hidden">
                      <div className="bg-gradient-to-r from-cyan-400 to-emerald-400 h-full w-3/4 animate-pulse rounded-full" />
                    </div>
                  </div>
                )}

                <div className="flex justify-end gap-3 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsUploadVideoModalOpen(false)}
                    disabled={isUploadingVideo}
                    className="px-4 py-2 rounded-xl bg-[#222] hover:bg-[#333] text-xs text-[#858585]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={!uploadVideoFile || isUploadingVideo}
                    className="px-5 py-2 rounded-xl bg-gradient-to-r from-[#f5dfc0] to-[#00F2FE] hover:opacity-95 text-black font-black text-xs uppercase tracking-wider disabled:opacity-50 flex items-center gap-1.5 shadow"
                  >
                    {isUploadingVideo ? 'PROCESSING...' : 'PROCESS VIDEO EVIDENCE'}
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* ========================================================================= */}
      {/* 5. VEHICLE FLAGGING MODAL                                                 */}
      {/* ========================================================================= */}
      <AnimatePresence>
        {flagModalVehicle && (
          <div 
            className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4 font-mono"
            onClick={() => setFlagModalVehicle(null)}
          >
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-[#181818] border border-[#333333] rounded-2xl p-6 max-w-md w-full shadow-2xl space-y-4"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between border-b border-[#2a2a2a] pb-3">
                <div className="flex items-center gap-2">
                  <Flag className="w-4 h-4 text-red-400" />
                  <h3 className="text-sm font-bold text-[#f5dfc0] uppercase">
                    Flag Vehicle for Investigation
                  </h3>
                </div>
                <button onClick={() => setFlagModalVehicle(null)} className="text-[#858585] hover:text-white">
                  <X className="w-4 h-4" />
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div>
                  <label className="text-[10px] text-[#858585] uppercase block mb-1">Target Plate</label>
                  <div className="p-2 rounded bg-[#0a0a0a] border border-[#333] font-bold text-yellow-400">
                    {flagModalVehicle.plate} ({flagModalVehicle.color} {flagModalVehicle.type})
                  </div>
                </div>

                <div>
                  <label className="text-[10px] text-[#858585] uppercase block mb-1">Reason for Flagging</label>
                  <select
                    value={flagReason}
                    onChange={(e) => setFlagReason(e.target.value)}
                    className="w-full p-2 rounded bg-[#0a0a0a] border border-[#333] text-[#e5e2e1] outline-none"
                  >
                    <option value="Stolen Vehicle">Reported Stolen Vehicle</option>
                    <option value="Suspect Transit">Suspect Transit / BOLO Alert</option>
                    <option value="Traffic Violation">Hit & Run / Severe Collision</option>
                    <option value="Surveillance Watch">Active Surveillance Watch</option>
                  </select>
                </div>

                <div>
                  <label className="text-[10px] text-[#858585] uppercase block mb-1">Investigator Note</label>
                  <textarea
                    value={flagNote}
                    onChange={(e) => setFlagNote(e.target.value)}
                    placeholder="Enter case reference or details..."
                    className="w-full p-2 rounded bg-[#0a0a0a] border border-[#333] text-[#e5e2e1] outline-none h-20 resize-none text-xs"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-2">
                <button
                  onClick={() => setFlagModalVehicle(null)}
                  className="px-4 py-2 rounded-lg bg-[#222] hover:bg-[#333] text-xs text-[#858585] hover:text-white"
                >
                  Cancel
                </button>
                <button
                  onClick={handleFlagSubmit}
                  disabled={isFlaggingLoading}
                  className="px-5 py-2 rounded-lg bg-red-800 hover:bg-red-700 text-xs font-bold text-white flex items-center gap-2"
                >
                  {isFlaggingLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                  Confirm Flag
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Toast Notification */}
      {flagToast && (
        <div className="fixed bottom-6 right-6 z-50">
          <div className={`px-4 py-3 rounded-xl shadow-2xl border text-xs font-mono flex items-center gap-2 ${
            flagToast.type === 'success' ? 'bg-emerald-950 text-emerald-200 border-emerald-700' : 'bg-red-950 text-red-200 border-red-700'
          }`}>
            <CheckCircle2 className="w-4 h-4" />
            <span>{flagToast.message}</span>
            <button onClick={() => setFlagToast(null)} className="ml-2 text-white/60 hover:text-white">
              <X className="w-3 h-3" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
