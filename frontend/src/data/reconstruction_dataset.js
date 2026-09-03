// Comprehensive Local Dataset & Reconstruction Engine for all 7 Threat Types
// Covers all Cameras (CAM-01 to CAM-07) across Mumbai & Bengaluru

export const LOCAL_RECONSTRUCTION_EVENTS = [
  // 1. VEHICLE COLLISION
  {
    id: 6001,
    camera_id: 2,
    event_type: "Vehicle Collision",
    camera_name: "CAM-02: Bengaluru MG Road Commercial Corridor",
    location: "MG Road Commercial Corridor (Near Brigade Cross)",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9756,
    lon: 77.6067,
    severity: "Critical",
    confidence: 0.96,
    confirmation_count: 6,
    timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6008,
    camera_id: 5,
    event_type: "Vehicle Collision",
    camera_name: "CAM-05: Bengaluru Outer Ring Road Hub",
    location: "Outer Ring Road High-Speed Flyover",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9820,
    lon: 77.6200,
    severity: "Critical",
    confidence: 0.95,
    confirmation_count: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6015,
    camera_id: 6,
    event_type: "Vehicle Collision",
    camera_name: "CAM-06: Mumbai Worli Sea Face Intercept",
    location: "Worli Sea Face Coastal Expressway",
    city: "Mumbai Safe City Mesh",
    lat: 18.9650,
    lon: 72.8180,
    severity: "Critical",
    confidence: 0.98,
    confirmation_count: 7,
    timestamp: new Date(Date.now() - 1000 * 60 * 55).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },

  // 2. FIGHTING / ALTERCATION
  {
    id: 6005,
    camera_id: 1,
    event_type: "Fighting",
    camera_name: "CAM-01: Mumbai CSMT Concourse Altercation",
    location: "CSMT Central Transit Concourse Platform 4",
    city: "Mumbai Safe City Mesh",
    lat: 18.9401,
    lon: 72.8351,
    severity: "Critical",
    confidence: 0.97,
    confirmation_count: 6,
    timestamp: new Date(Date.now() - 1000 * 60 * 18).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_person_cam1_1.jpg"
  },
  {
    id: 6012,
    camera_id: 4,
    event_type: "Fighting",
    camera_name: "CAM-04: Bengaluru Trinity Circle Transit Node",
    location: "Trinity Circle Metro Ingress Plaza",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9725,
    lon: 77.6200,
    severity: "High",
    confidence: 0.92,
    confirmation_count: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 42).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_person_cam1_1.jpg"
  },
  {
    id: 6016,
    camera_id: 7,
    event_type: "Fighting",
    camera_name: "CAM-07: Mall Concourse Platform",
    location: "Shopping Atrium South Escalator Corridor",
    city: "Mumbai Safe City Mesh",
    lat: 18.9350,
    lon: 72.8290,
    severity: "Critical",
    confidence: 0.94,
    confirmation_count: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 64).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_person_cam1_1.jpg"
  },

  // 3. FIRE OUTBREAK
  {
    id: 6003,
    camera_id: 3,
    event_type: "Fire",
    camera_name: "CAM-03: Mumbai Marine Drive Coastal Unit",
    location: "Marine Drive Commercial Complex Sub-Station",
    city: "Mumbai Safe City Mesh",
    lat: 18.9438,
    lon: 72.8233,
    severity: "Critical",
    confidence: 0.98,
    confirmation_count: 7,
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6009,
    camera_id: 2,
    event_type: "Fire",
    camera_name: "CAM-02: Bengaluru MG Road Commercial Corridor",
    location: "Commercial Arcade Transformer Unit",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9756,
    lon: 77.6067,
    severity: "Critical",
    confidence: 0.96,
    confirmation_count: 6,
    timestamp: new Date(Date.now() - 1000 * 60 * 48).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6017,
    camera_id: 5,
    event_type: "Fire",
    camera_name: "CAM-05: Bengaluru Outer Ring Road Hub",
    location: "Logistics Terminal Fuel Depot Perimeter",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9820,
    lon: 77.6200,
    severity: "High",
    confidence: 0.93,
    confirmation_count: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 80).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },

  // 4. SMOKE SENSOR
  {
    id: 6007,
    camera_id: 3,
    event_type: "Smoke",
    camera_name: "CAM-03: Mumbai Marine Drive Coastal Unit",
    location: "Basement Ventilation Exhaust Shaft 2",
    city: "Mumbai Safe City Mesh",
    lat: 18.9438,
    lon: 72.8233,
    severity: "Medium",
    confidence: 0.89,
    confirmation_count: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 22).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6010,
    camera_id: 1,
    event_type: "Smoke",
    camera_name: "CAM-01: Mumbai CSMT Concourse Ingress",
    location: "CSMT Underground Utility Passage",
    city: "Mumbai Safe City Mesh",
    lat: 18.9401,
    lon: 72.8351,
    severity: "High",
    confidence: 0.91,
    confirmation_count: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 50).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6018,
    camera_id: 4,
    event_type: "Smoke",
    camera_name: "CAM-04: Bengaluru Trinity Circle Transit Node",
    location: "Electrical Sub-Chamber Ingress",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9725,
    lon: 77.6200,
    severity: "Medium",
    confidence: 0.88,
    confirmation_count: 3,
    timestamp: new Date(Date.now() - 1000 * 60 * 95).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },

  // 5. ACCIDENT
  {
    id: 6006,
    camera_id: 6,
    event_type: "Accident",
    camera_name: "CAM-06: Mumbai Worli Sea Face Intercept",
    location: "Worli Northbound U-Turn Arterial",
    city: "Mumbai Safe City Mesh",
    lat: 18.9650,
    lon: 72.8180,
    severity: "High",
    confidence: 0.93,
    confirmation_count: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 26).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6011,
    camera_id: 2,
    event_type: "Accident",
    camera_name: "CAM-02: Bengaluru MG Road Commercial Corridor",
    location: "MG Road - Residency Road Intersection",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9756,
    lon: 77.6067,
    severity: "Critical",
    confidence: 0.95,
    confirmation_count: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6019,
    camera_id: 4,
    event_type: "Accident",
    camera_name: "CAM-04: Bengaluru Trinity Circle Transit Node",
    location: "Trinity Flyover Down-Ramp",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9725,
    lon: 77.6200,
    severity: "High",
    confidence: 0.91,
    confirmation_count: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 110).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },

  // 6. VEHICLE BOLO
  {
    id: 6004,
    camera_id: 5,
    event_type: "Vehicle",
    camera_name: "CAM-05: Bengaluru Outer Ring Road Hub",
    location: "Outer Ring Road Express Toll Gantry",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9820,
    lon: 77.6200,
    severity: "High",
    confidence: 0.94,
    confirmation_count: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6013,
    camera_id: 2,
    event_type: "Vehicle",
    camera_name: "CAM-02: Bengaluru MG Road Commercial Corridor",
    location: "MG Road ANPR Vehicle Checkpoint 1",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9756,
    lon: 77.6067,
    severity: "Critical",
    confidence: 0.97,
    confirmation_count: 6,
    timestamp: new Date(Date.now() - 1000 * 60 * 75).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },
  {
    id: 6020,
    camera_id: 6,
    event_type: "Vehicle",
    camera_name: "CAM-06: Mumbai Worli Sea Face Intercept",
    location: "Coastal Highway Fastag Scanner 3",
    city: "Mumbai Safe City Mesh",
    lat: 18.9650,
    lon: 72.8180,
    severity: "High",
    confidence: 0.93,
    confirmation_count: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 125).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_vehicle_cam2_1.jpg"
  },

  // 7. PERSON / PEDESTRIAN
  {
    id: 6002,
    camera_id: 4,
    event_type: "Person",
    camera_name: "CAM-04: Bengaluru Trinity Circle Transit Node",
    location: "Trinity Metro Station Escalator Lobby",
    city: "Bengaluru Safe City Mesh",
    lat: 12.9725,
    lon: 77.6200,
    severity: "High",
    confidence: 0.91,
    confirmation_count: 4,
    timestamp: new Date(Date.now() - 1000 * 60 * 16).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_person_cam1_1.jpg"
  },
  {
    id: 6014,
    camera_id: 1,
    event_type: "Person",
    camera_name: "CAM-01: Mumbai CSMT Concourse Walkway",
    location: "Suburban Foot-Over-Bridge Ingress",
    city: "Mumbai Safe City Mesh",
    lat: 18.9401,
    lon: 72.8351,
    severity: "High",
    confidence: 0.95,
    confirmation_count: 5,
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_person_cam1_1.jpg"
  },
  {
    id: 6021,
    camera_id: 7,
    event_type: "Person",
    camera_name: "CAM-07: Mall Concourse Ingress Turnstile",
    location: "Central Pedestrian Screening Corridor",
    city: "Mumbai Safe City Mesh",
    lat: 18.9350,
    lon: 72.8290,
    severity: "Medium",
    confidence: 0.89,
    confirmation_count: 3,
    timestamp: new Date(Date.now() - 1000 * 60 * 105).toISOString(),
    status: "Active",
    snapshot_path: "/snapshots/crop_person_cam1_1.jpg"
  }
];

// Client-Side Forensic Reconstruction Generator (Guaranteed Fallback & Simulation)
export function generateClientReconstruction(event) {
  if (!event) return null;

  const lat = typeof event.lat === 'number' ? event.lat : 12.9756;
  const lon = typeof event.lon === 'number' ? event.lon : 77.6067;
  const isBengaluru = (lat < 15.0) || ((event.camera_name || '').toLowerCase().includes('bengaluru')) || (event.camera_id in [2, 4, 5]);
  const evType = (event.event_type || 'Incident').trim();
  const evDate = event.timestamp ? new Date(event.timestamp) : new Date();

  // Mode resolution
  let mode = 'vehicle';
  let modeLabel = 'VEHICLE RE-ID & ARTERIAL ROAD TRAJECTORY PREDICTION';
  if (['Fire', 'Smoke'].some(t => evType.toLowerCase().includes(t.toLowerCase()))) {
    mode = 'incident_spread';
    modeLabel = 'THERMAL INCIDENT CONTAINMENT & EMERGENCY SECTOR ACCESS';
  } else if (['Fighting', 'Person', 'Altercation', 'Crowd'].some(t => evType.toLowerCase().includes(t.toLowerCase()))) {
    mode = 'pedestrian';
    modeLabel = 'PEDESTRIAN DISPERSAL & ESCAPE CORRIDOR TRACKING';
  }

  const formatTime = (d) => d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  let observedCheckpoints = [];
  let observedGeometry = [];
  let candidatePaths = [];
  let nextCheckpoints = [];

  if (mode === 'incident_spread') {
    // Thermal containment mode
    const tResp = formatTime(new Date(evDate.getTime() + 4 * 60000));
    const accessP1 = [
      [lat - 0.008, lon - 0.006],
      [lat - 0.004, lon - 0.003],
      [lat, lon]
    ];
    const accessP2 = [
      [lat + 0.007, lon + 0.005],
      [lat + 0.003, lon + 0.002],
      [lat, lon]
    ];

    candidatePaths = [
      {
        path_id: 'ZONE-01',
        name: 'Priority Emergency Response Ingress Corridor (Primary Foam Tender)',
        is_most_likely: true,
        score: 0.85,
        likelihood_percent: 85,
        estimated_minutes: 4,
        eta_window: `${formatTime(evDate)}–${tResp}`,
        distance_km: 1.2,
        camera_count: 2,
        factors: {
          road_connectivity: 'Designated Emergency Fire Lane',
          travel_time: 'Priority Siren Clearance',
          direction_compatibility: 'Direct Inbound Fire Access',
          camera_coverage: '2 Perimeter CCTV Checkpoints'
        },
        checkpoints: [
          { camera_id: 'CAM-FIRE-01', name: 'Emergency Marshalling Staging Node', lat: lat - 0.008, lon: lon - 0.006, eta: '0 min' },
          { camera_id: `CAM-0${event.camera_id || 1}`, name: 'Incident Sector Access Gate', lat, lon, eta: '+4 min' }
        ],
        geometry: accessP1
      },
      {
        path_id: 'ZONE-02',
        name: 'Secondary Emergency Evacuation & Hazmat Ingress Corridor',
        is_most_likely: false,
        score: 0.15,
        likelihood_percent: 15,
        estimated_minutes: 7,
        eta_window: `${formatTime(evDate)}–${formatTime(new Date(evDate.getTime() + 7 * 60000))}`,
        distance_km: 1.8,
        camera_count: 1,
        factors: {
          road_connectivity: 'Secondary Arterial Bypass',
          travel_time: 'Controlled intersection flow',
          direction_compatibility: 'Downwind Hazmat Approach',
          camera_coverage: '1 Checkpoint'
        },
        checkpoints: [
          { camera_id: 'CAM-SEC-01', name: 'Secondary Perimeter Sector', lat: lat + 0.007, lon: lon + 0.005, eta: '0 min' },
          { camera_id: `CAM-0${event.camera_id || 1}`, name: 'Incident Ground Zero', lat, lon, eta: '+7 min' }
        ],
        geometry: accessP2
      }
    ];

    nextCheckpoints = [
      {
        camera_id: 'CAM-EMERGENCY-01',
        camera_name: 'Primary Ingress Checkpoint',
        distance_km: 0.6,
        eta_window: `${formatTime(evDate)}–${tResp}`,
        likelihood_percent: 85,
        lat: lat - 0.004,
        lon: lon - 0.003
      }
    ];
  } else if (mode === 'pedestrian') {
    // Pedestrian Dispersal
    const tPre = formatTime(new Date(evDate.getTime() - 8 * 60000));
    const preLat = lat - 0.002;
    const preLon = lon - 0.001;

    observedCheckpoints = [
      {
        camera_id: 'CAM-PED-PRE',
        camera_name: 'Concourse Ingress Turnstile',
        location: 'Concourse Ingress',
        lat: preLat,
        lon: preLon,
        timestamp: tPre,
        speed_kmh: 4.2,
        is_origin: true
      },
      {
        camera_id: `CAM-0${event.camera_id || 1}`,
        camera_name: event.camera_name || 'Ground Zero',
        location: `Incident Sector (CAM-0${event.camera_id || 1})`,
        lat,
        lon,
        timestamp: formatTime(evDate),
        speed_kmh: 1.5,
        is_origin: false
      }
    ];
    observedGeometry = [
      [preLat, preLon],
      [lat, lon]
    ];

    const p1EndLat = isBengaluru ? 12.9750 : 18.9430;
    const p1EndLon = isBengaluru ? 77.6090 : 72.8330;
    const p2EndLat = isBengaluru ? 12.9712 : 18.9370;
    const p2EndLon = isBengaluru ? 77.6075 : 72.8380;

    candidatePaths = [
      {
        path_id: 'PATH-01',
        name: 'Metro Underground Transit Ingress (Subway Escape Corridor)',
        is_most_likely: true,
        score: 0.68,
        likelihood_percent: 68,
        estimated_minutes: 4,
        eta_window: `${formatTime(new Date(evDate.getTime() + 3 * 60000))}–${formatTime(new Date(evDate.getTime() + 6 * 60000))}`,
        distance_km: 0.4,
        camera_count: 2,
        factors: {
          road_connectivity: 'High (Pedestrian walkway + Subway)',
          travel_time: 'Fast concourse traversal',
          direction_compatibility: 'Direct transit access',
          camera_coverage: '2 High-Res CCTVs'
        },
        checkpoints: [
          { camera_id: `CAM-0${event.camera_id || 1}`, name: 'Incident Sector', lat, lon, eta: '0 min' },
          { camera_id: 'CAM-METRO-01', name: 'Subway Platform Ingress', lat: p1EndLat, lon: p1EndLon, eta: '+4 min' }
        ],
        geometry: [[lat, lon], [(lat + p1EndLat) / 2, (lon + p1EndLon) / 2], [p1EndLat, p1EndLon]]
      },
      {
        path_id: 'PATH-02',
        name: 'Surface Alleyway Dispersal (Commercial Market Corridor)',
        is_most_likely: false,
        score: 0.32,
        likelihood_percent: 32,
        estimated_minutes: 6,
        eta_window: `${formatTime(new Date(evDate.getTime() + 5 * 60000))}–${formatTime(new Date(evDate.getTime() + 8 * 60000))}`,
        distance_km: 0.6,
        camera_count: 1,
        factors: {
          road_connectivity: 'Medium (Narrow commercial alley)',
          travel_time: 'Crowd friction delay',
          direction_compatibility: 'Secondary side exit',
          camera_coverage: '1 Security Cam'
        },
        checkpoints: [
          { camera_id: `CAM-0${event.camera_id || 1}`, name: 'Incident Sector', lat, lon, eta: '0 min' },
          { camera_id: 'CAM-ALLEY-02', name: 'Market South Portal', lat: p2EndLat, lon: p2EndLon, eta: '+6 min' }
        ],
        geometry: [[lat, lon], [(lat + p2EndLat) / 2, (lon + p2EndLon) / 2], [p2EndLat, p2EndLon]]
      }
    ];

    nextCheckpoints = [
      {
        camera_id: 'CAM-METRO-01',
        camera_name: 'Metro Ingress Concourse',
        distance_km: 0.4,
        eta_window: `${formatTime(new Date(evDate.getTime() + 3 * 60000))}–${formatTime(new Date(evDate.getTime() + 6 * 60000))}`,
        likelihood_percent: 68,
        lat: p1EndLat,
        lon: p1EndLon
      }
    ];
  } else {
    // Vehicle Route
    const tPre2 = formatTime(new Date(evDate.getTime() - 25 * 60000));
    const tPre1 = formatTime(new Date(evDate.getTime() - 10 * 60000));
    const preLat2 = lat - 0.008;
    const preLon2 = lon - 0.006;
    const preLat1 = lat - 0.003;
    const preLon1 = lon - 0.002;

    observedCheckpoints = [
      {
        camera_id: `CAM-ENTRY-0${event.camera_id || 2}`,
        camera_name: 'Corridor Ingress Gate 1',
        location: 'Corridor Ingress Gate 1',
        lat: preLat2,
        lon: preLon2,
        timestamp: tPre2,
        speed_kmh: 54.0,
        is_origin: true
      },
      {
        camera_id: `CAM-MID-0${event.camera_id || 2}`,
        camera_name: 'Midway Speed Telemetry Gantry',
        location: 'Midway Gantry Checkpoint',
        lat: preLat1,
        lon: preLon1,
        timestamp: tPre1,
        speed_kmh: 46.0,
        is_origin: false
      },
      {
        camera_id: `CAM-0${event.camera_id || 2}`,
        camera_name: event.camera_name || 'Ground Zero',
        location: `Incident Ground Zero (CAM-0${event.camera_id || 2})`,
        lat,
        lon,
        timestamp: formatTime(evDate),
        speed_kmh: 22.0,
        is_origin: false
      }
    ];
    observedGeometry = [
      [preLat2, preLon2],
      [preLat1, preLon1],
      [lat, lon]
    ];

    const dest1Lat = isBengaluru ? 12.9784 : 18.9650;
    const dest1Lon = isBengaluru ? 77.6408 : 72.8180;
    const dest2Lat = isBengaluru ? 12.9820 : 18.9490;
    const dest2Lon = isBengaluru ? 77.6200 : 72.8430;

    candidatePaths = [
      {
        path_id: 'PATH-01',
        name: isBengaluru ? 'Eastbound Transit Arterial (MG Road → Trinity Circle → Indiranagar)' : 'Northbound Coastal Expressway (Marine Drive → Worli Sea Face)',
        is_most_likely: true,
        score: 0.74,
        likelihood_percent: 74,
        estimated_minutes: 5,
        eta_window: `${formatTime(new Date(evDate.getTime() + 4 * 60000))}–${formatTime(new Date(evDate.getTime() + 7 * 60000))}`,
        distance_km: 3.8,
        camera_count: 3,
        factors: {
          road_connectivity: 'High (Multi-lane arterial)',
          travel_time: 'Optimal green wave throughput',
          direction_compatibility: 'Direct outbound flow',
          camera_coverage: '3 CCTV checkpoints'
        },
        checkpoints: [
          { camera_id: `CAM-0${event.camera_id || 2}`, name: 'Incident Sector', lat, lon, eta: '0 min' },
          { camera_id: isBengaluru ? 'CAM-04' : 'CAM-03', name: isBengaluru ? 'Trinity Circle Node' : 'Marine Drive Unit', lat: (lat + dest1Lat)/2, lon: (lon + dest1Lon)/2, eta: '+2 min' },
          { camera_id: isBengaluru ? 'CAM-BLR-06' : 'CAM-06', name: isBengaluru ? 'Indiranagar 100ft Hub' : 'Worli Sea Face Intercept', lat: dest1Lat, lon: dest1Lon, eta: '+5 min' }
        ],
        geometry: [
          [lat, lon],
          [(lat * 0.6 + dest1Lat * 0.4), (lon * 0.6 + dest1Lon * 0.4)],
          [(lat * 0.3 + dest1Lat * 0.7), (lon * 0.3 + dest1Lon * 0.7)],
          [dest1Lat, dest1Lon]
        ]
      },
      {
        path_id: 'PATH-02',
        name: isBengaluru ? 'Northbound Link (Commercial Street → Outer Ring Road)' : 'Eastbound Port Access (Eastern Freeway Entry Ramp)',
        is_most_likely: false,
        score: 0.26,
        likelihood_percent: 26,
        estimated_minutes: 6,
        eta_window: `${formatTime(new Date(evDate.getTime() + 5 * 60000))}–${formatTime(new Date(evDate.getTime() + 8 * 60000))}`,
        distance_km: 2.4,
        camera_count: 2,
        factors: {
          road_connectivity: 'Medium (Urban grid)',
          travel_time: 'Moderate intersection delay',
          direction_compatibility: 'Perpendicular egress',
          camera_coverage: '2 CCTV checkpoints'
        },
        checkpoints: [
          { camera_id: `CAM-0${event.camera_id || 2}`, name: 'Incident Sector', lat, lon, eta: '0 min' },
          { camera_id: isBengaluru ? 'CAM-05' : 'CAM-MUM-04', name: isBengaluru ? 'Outer Ring Road Hub' : 'Eastern Freeway Entry', lat: dest2Lat, lon: dest2Lon, eta: '+6 min' }
        ],
        geometry: [
          [lat, lon],
          [(lat + dest2Lat)/2, (lon + dest2Lon)/2],
          [dest2Lat, dest2Lon]
        ]
      }
    ];

    nextCheckpoints = [
      {
        camera_id: isBengaluru ? 'CAM-04' : 'CAM-03',
        camera_name: isBengaluru ? 'Trinity Circle Checkpoint' : 'Marine Drive Coastal Unit',
        distance_km: 1.8,
        eta_window: `${formatTime(new Date(evDate.getTime() + 2 * 60000))}–${formatTime(new Date(evDate.getTime() + 4 * 60000))}`,
        likelihood_percent: 74,
        lat: (lat + dest1Lat)/2,
        lon: (lon + dest1Lon)/2
      }
    ];
  }

  const topPath = candidatePaths[0] || {};
  const topCheckpoint = nextCheckpoints[0] || null;

  return {
    event: {
      id: event.id,
      event_type: event.event_type,
      severity: event.severity || 'Critical',
      confidence: Number(event.confidence || 0.95),
      timestamp: formatTime(evDate),
      camera_id: `CAM-0${event.camera_id || 1}`,
      camera_name: event.camera_name || `CAM-0${event.camera_id || 1}`,
      location: event.location || event.camera_name || 'Surveillance Node',
      city: event.city || (isBengaluru ? 'Bengaluru Safe City Mesh' : 'Mumbai Safe City Mesh'),
      lat,
      lon,
      confirmation_count: event.confirmation_count || 5,
      snapshot_path: event.snapshot_path || '/snapshots/crop_vehicle_cam2_1.jpg'
    },
    mode,
    mode_label: modeLabel,
    summary: {
      last_known_checkpoint: `CAM-0${event.camera_id || 1} (${event.camera_name || 'Ground Zero'})`,
      most_likely_next_checkpoint: topCheckpoint ? `${topCheckpoint.camera_id} (${topCheckpoint.camera_name})` : 'Incident Sector',
      most_likely_route_name: topPath.name || 'Primary Corridor',
      likelihood_percent: topPath.likelihood_percent || 75,
      estimated_window: topPath.eta_window || '5–8 min',
      total_candidate_routes: candidatePaths.length
    },
    observed_path: {
      status: observedCheckpoints.length > 0 ? 'CONFIRMED_HISTORICAL_SIGHTING' : 'NO_PREVIOUS_SIGHTING',
      description: observedCheckpoints.length > 0 
        ? 'Solid cyan polyline denotes confirmed surveillance checkpoints prior to incident detection.'
        : 'Historical pre-incident movement unavailable. Ranking based on road network connectivity and travel time.',
      checkpoints: observedCheckpoints,
      geometry: observedGeometry
    },
    candidate_paths: candidatePaths,
    next_checkpoints: nextCheckpoints
  };
}
