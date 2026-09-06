// Canonical Offline-Ready Verified Surveillance Vehicle Dataset
// Matches backend format_vehicle_dossier contract exactly
// Ensures Vehicle Intelligence & Re-ID works instantly on any machine even when backend is offline

export const LOCAL_VEHICLES = [
  {
    vehicle_id: "VEH-MH43BF3945",
    plate: "MH 43 BF 3945",
    plate_number: "MH 43 BF 3945",
    plate_confidence: 0.99,
    match_confidence: 0.98,
    type: "Auto-Rickshaw (3-Wheeler)",
    vehicle_type: "Auto-Rickshaw (3-Wheeler)",
    model: "Bajaj RE Commercial",
    vehicle_model: "Bajaj RE Commercial",
    color: "Yellow",
    vehicle_color: "Yellow",
    is_stolen: true,
    bolo_status: "CRITICAL BOLO: Reported Stolen Commercial Transport",
    snapshot: "/snapshots/autorickshaw_mh43bf3945.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 14:42:15",
      location: "CBD Belapur Flyover Ingress",
      camera_id: "CAM-01",
      camera_name: "CAM-01 CBD Belapur Flyover Intercept",
      city: "Mumbai Safe City Mesh",
      latitude: 19.0180,
      longitude: 73.0410,
      speed_kmh: 24.5,
      evidence_image: "/snapshots/autorickshaw_mh43bf3945.jpg"
    },
    metadata: {
      first_seen: "Today, 12:45:00",
      last_seen: "Today, 14:42:15",
      total_sightings: 3,
      associated_cameras: ["CAM-01", "CAM-02", "CAM-03"]
    },
    flag_status: {
      is_flagged: true,
      reason: "Stolen Commercial Vehicle",
      note: "Reported missing from CBD Belapur depot. High priority intercept.",
      flagged_at: "Today, 13:00:00"
    },
    sightings: [
      { camera_id: "CAM-01", camera_name: "CAM-01 CBD Belapur Flyover", location: "CBD Belapur Flyover Ingress", timestamp: "14:42:15", speed_kmh: 24.5, direction: "Southbound", latitude: 19.0180, longitude: 73.0410 },
      { camera_id: "CAM-02", camera_name: "CAM-02 Kharghar Municipal Gantry", location: "Kharghar Sector 12 Arterial", timestamp: "14:15:30", speed_kmh: 28.0, direction: "Southbound", latitude: 19.0345, longitude: 73.0645 },
      { camera_id: "CAM-03", camera_name: "CAM-03 Vashi Toll Plaza", location: "Vashi Plaza Outer Lane 2", timestamp: "13:30:10", speed_kmh: 31.2, direction: "Eastbound", latitude: 19.0770, longitude: 72.9980 }
    ]
  },
  {
    vehicle_id: "VEH-MH46CB0005",
    plate: "MH 46 CB 0005",
    plate_number: "MH 46 CB 0005",
    plate_confidence: 0.97,
    match_confidence: 0.96,
    type: "SUV / Offroad",
    vehicle_type: "SUV / Offroad",
    model: "Mahindra Thar 4x4",
    vehicle_model: "Mahindra Thar 4x4",
    color: "Green",
    vehicle_color: "Green",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/mahindra_thar_mh46cb0005.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 14:35:40",
      location: "Rangoli Junction / Khandeshwar",
      camera_id: "CAM-01",
      camera_name: "CAM-01 Rangoli Intersection Intercept",
      city: "Mumbai Safe City Mesh",
      latitude: 19.0125,
      longitude: 73.0880,
      speed_kmh: 38.0,
      evidence_image: "/snapshots/mahindra_thar_mh46cb0005.jpg"
    },
    metadata: {
      first_seen: "Today, 13:10:00",
      last_seen: "Today, 14:35:40",
      total_sightings: 2,
      associated_cameras: ["CAM-01", "CAM-04"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-01", camera_name: "CAM-01 Rangoli Intersection", location: "Rangoli Junction North", timestamp: "14:35:40", speed_kmh: 38.0, direction: "Northbound", latitude: 19.0125, longitude: 73.0880 },
      { camera_id: "CAM-04", camera_name: "CAM-04 Panvel Bypass Gate", location: "Old Mumbai-Pune Highway", timestamp: "14:02:18", speed_kmh: 44.5, direction: "Northbound", latitude: 18.9890, longitude: 73.1190 }
    ]
  },
  {
    vehicle_id: "VEH-MH46CT5126",
    plate: "MH 46 CT 5126",
    plate_number: "MH 46 CT 5126",
    plate_confidence: 0.99,
    match_confidence: 0.99,
    type: "Sedan (Luxury)",
    vehicle_type: "Sedan (Luxury)",
    model: "BMW 3 Series Luxury",
    vehicle_model: "BMW 3 Series Luxury",
    color: "White",
    vehicle_color: "White",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/bmw_mh46ct5126.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 14:28:10",
      location: "Panvel East Expressway Corridor",
      camera_id: "CAM-02",
      camera_name: "CAM-02 Panvel East Expressway Gantry",
      city: "Mumbai Safe City Mesh",
      latitude: 18.9920,
      longitude: 73.1250,
      speed_kmh: 62.0,
      evidence_image: "/snapshots/bmw_mh46ct5126.jpg"
    },
    metadata: {
      first_seen: "Today, 12:20:00",
      last_seen: "Today, 14:28:10",
      total_sightings: 2,
      associated_cameras: ["CAM-02", "CAM-05"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-02", camera_name: "CAM-02 Panvel East Expressway", location: "Panvel Expressway Toll Ingress", timestamp: "14:28:10", speed_kmh: 62.0, direction: "Westbound", latitude: 18.9920, longitude: 73.1250 },
      { camera_id: "CAM-05", camera_name: "CAM-05 Kalamboli Circle", location: "Kalamboli Expressway Junction", timestamp: "13:51:22", speed_kmh: 58.0, direction: "Westbound", latitude: 19.0300, longitude: 73.1000 }
    ]
  },
  {
    vehicle_id: "VEH-MH48DX1051",
    plate: "MH 48 DX 1051",
    plate_number: "MH 48 DX 1051",
    plate_confidence: 0.98,
    match_confidence: 0.97,
    type: "Electric SUV",
    vehicle_type: "Electric SUV",
    model: "Mahindra BE 6e EV",
    vehicle_model: "Mahindra BE 6e EV",
    color: "Blue",
    vehicle_color: "Blue",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/mahindra_ev_mh48dx1051.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 14:22:05",
      location: "Vasai-Virar Arterial Corridor",
      camera_id: "CAM-03",
      camera_name: "CAM-03 Vasai-Virar Municipal Corridor",
      city: "Mumbai Safe City Mesh",
      latitude: 19.3838,
      longitude: 72.8282,
      speed_kmh: 35.0,
      evidence_image: "/snapshots/mahindra_ev_mh48dx1051.jpg"
    },
    metadata: {
      first_seen: "Today, 13:40:00",
      last_seen: "Today, 14:22:05",
      total_sightings: 1,
      associated_cameras: ["CAM-03"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-03", camera_name: "CAM-03 Vasai-Virar Corridor", location: "Vasai West Highway Checkpoint", timestamp: "14:22:05", speed_kmh: 35.0, direction: "Northbound", latitude: 19.3838, longitude: 72.8282 }
    ]
  },
  {
    vehicle_id: "VEH-MH43CG3824",
    plate: "MH 43 CG 3824",
    plate_number: "MH 43 CG 3824",
    plate_confidence: 0.97,
    match_confidence: 0.96,
    type: "Compact SUV",
    vehicle_type: "Compact SUV",
    model: "Tata Punch SUV",
    vehicle_model: "Tata Punch SUV",
    color: "Blue",
    vehicle_color: "Blue",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/tata_punch_mh43cg3824.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 14:18:50",
      location: "Kharghar Sector 12 Corridor",
      camera_id: "CAM-02",
      camera_name: "CAM-02 Kharghar Municipal Corridor",
      city: "Mumbai Safe City Mesh",
      latitude: 19.0345,
      longitude: 73.0645,
      speed_kmh: 32.5,
      evidence_image: "/snapshots/tata_punch_mh43cg3824.jpg"
    },
    metadata: {
      first_seen: "Today, 12:50:00",
      last_seen: "Today, 14:18:50",
      total_sightings: 1,
      associated_cameras: ["CAM-02"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-02", camera_name: "CAM-02 Kharghar Municipal Corridor", location: "Sector 12 Intersection", timestamp: "14:18:50", speed_kmh: 32.5, direction: "Eastbound", latitude: 19.0345, longitude: 73.0645 }
    ]
  },
  {
    vehicle_id: "VEH-MH46DF9820",
    plate: "MH 46 DF 9820",
    plate_number: "MH 46 DF 9820",
    plate_confidence: 0.96,
    match_confidence: 0.95,
    type: "Compact SUV",
    vehicle_type: "Compact SUV",
    model: "Tata Punch White Edition",
    vehicle_model: "Tata Punch White Edition",
    color: "White",
    vehicle_color: "White",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/tata_punch_mh46df9820.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 14:12:30",
      location: "Vashi Sector 17 Transit Gate",
      camera_id: "CAM-01",
      camera_name: "CAM-01 Vashi Transit Gate",
      city: "Mumbai Safe City Mesh",
      latitude: 19.0770,
      longitude: 72.9980,
      speed_kmh: 22.0,
      evidence_image: "/snapshots/tata_punch_mh46df9820.jpg"
    },
    metadata: {
      first_seen: "Today, 13:00:00",
      last_seen: "Today, 14:12:30",
      total_sightings: 1,
      associated_cameras: ["CAM-01"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-01", camera_name: "CAM-01 Vashi Transit Gate", location: "Sector 17 Commercial Entrance", timestamp: "14:12:30", speed_kmh: 22.0, direction: "Inbound", latitude: 19.0770, longitude: 72.9980 }
    ]
  },
  {
    vehicle_id: "VEH-MH43CB8645",
    plate: "MH 43 CB 8645",
    plate_number: "MH 43 CB 8645",
    plate_confidence: 0.95,
    match_confidence: 0.95,
    type: "Auto-Rickshaw (3-Wheeler)",
    vehicle_type: "Auto-Rickshaw (3-Wheeler)",
    model: "Bajaj RE City Auto",
    vehicle_model: "Bajaj RE City Auto",
    color: "Yellow",
    vehicle_color: "Yellow",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/autorickshaw_mh43cb8645.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 14:05:15",
      location: "Navi Mumbai Auto Stand Junction",
      camera_id: "CAM-02",
      camera_name: "CAM-02 Navi Mumbai Auto Stand",
      city: "Mumbai Safe City Mesh",
      latitude: 19.0330,
      longitude: 73.0297,
      speed_kmh: 18.5,
      evidence_image: "/snapshots/autorickshaw_mh43cb8645.jpg"
    },
    metadata: {
      first_seen: "Today, 12:15:00",
      last_seen: "Today, 14:05:15",
      total_sightings: 1,
      associated_cameras: ["CAM-02"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-02", camera_name: "CAM-02 Navi Mumbai Auto Stand", location: "CBD Transit Stand", timestamp: "14:05:15", speed_kmh: 18.5, direction: "Stationary", latitude: 19.0330, longitude: 73.0297 }
    ]
  },
  {
    vehicle_id: "VEH-MH04KY5983",
    plate: "MH 04 KY 5983",
    plate_number: "MH 04 KY 5983",
    plate_confidence: 0.99,
    match_confidence: 0.98,
    type: "Motorcycle (Sports)",
    vehicle_type: "Motorcycle (Sports)",
    model: "Yamaha YZF-R15",
    vehicle_model: "Yamaha YZF-R15",
    color: "Blue",
    vehicle_color: "Blue",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/sports_bike_mh04ky5983.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 13:58:45",
      location: "Thane-Belapur Expressway Flyover",
      camera_id: "CAM-04",
      camera_name: "CAM-04 Thane-Belapur Expressway Gantry",
      city: "Mumbai Safe City Mesh",
      latitude: 19.1120,
      longitude: 73.0110,
      speed_kmh: 58.0,
      evidence_image: "/snapshots/sports_bike_mh04ky5983.jpg"
    },
    metadata: {
      first_seen: "Today, 13:00:00",
      last_seen: "Today, 13:58:45",
      total_sightings: 1,
      associated_cameras: ["CAM-04"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-04", camera_name: "CAM-04 Thane-Belapur Expressway", location: "Rabale Flyover Ingress", timestamp: "13:58:45", speed_kmh: 58.0, direction: "Northbound", latitude: 19.1120, longitude: 73.0110 }
    ]
  },
  {
    vehicle_id: "VEH-MH46BK0500",
    plate: "MH 46 BK 0500",
    plate_number: "MH 46 BK 0500",
    plate_confidence: 0.97,
    match_confidence: 0.96,
    type: "MPV / Van",
    vehicle_type: "MPV / Van",
    model: "Toyota Innova Crysta",
    vehicle_model: "Toyota Innova Crysta",
    color: "Silver",
    vehicle_color: "Silver",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/toyota_innova_mh46bk0500.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 13:52:10",
      location: "Panvel Station Ring Road",
      camera_id: "CAM-03",
      camera_name: "CAM-03 Panvel Ring Road Gantry",
      city: "Mumbai Safe City Mesh",
      latitude: 18.9890,
      longitude: 73.1190,
      speed_kmh: 29.0,
      evidence_image: "/snapshots/toyota_innova_mh46bk0500.jpg"
    },
    metadata: {
      first_seen: "Today, 12:00:00",
      last_seen: "Today, 13:52:10",
      total_sightings: 1,
      associated_cameras: ["CAM-03"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-03", camera_name: "CAM-03 Panvel Ring Road", location: "Panvel Station Approach", timestamp: "13:52:10", speed_kmh: 29.0, direction: "Eastbound", latitude: 18.9890, longitude: 73.1190 }
    ]
  },
  {
    vehicle_id: "VEH-MH03BK8453",
    plate: "MH 03 BK 8453",
    plate_number: "MH 03 BK 8453",
    plate_confidence: 0.96,
    match_confidence: 0.96,
    type: "Sedan (Executive)",
    vehicle_type: "Sedan (Executive)",
    model: "Honda City VTEC",
    vehicle_model: "Honda City VTEC",
    color: "Black",
    vehicle_color: "Black",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/honda_city_mh03bk8453.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 13:45:00",
      location: "Kharghar Arterial Corridor",
      camera_id: "CAM-03",
      camera_name: "CAM-03 Kharghar Arterial Gantry",
      city: "Mumbai Safe City Mesh",
      latitude: 19.0380,
      longitude: 73.0690,
      speed_kmh: 42.0,
      evidence_image: "/snapshots/honda_city_mh03bk8453.jpg"
    },
    metadata: {
      first_seen: "Today, 11:30:00",
      last_seen: "Today, 13:45:00",
      total_sightings: 1,
      associated_cameras: ["CAM-03"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-03", camera_name: "CAM-03 Kharghar Arterial", location: "Kharghar Toll Node", timestamp: "13:45:00", speed_kmh: 42.0, direction: "Southbound", latitude: 19.0380, longitude: 73.0690 }
    ]
  },
  {
    vehicle_id: "VEH-MH01BUS204",
    plate: "MH 01 LA 4412",
    plate_number: "MH 01 LA 4412",
    plate_confidence: 0.99,
    match_confidence: 0.98,
    type: "Public Transit Bus",
    vehicle_type: "Public Transit Bus",
    model: "BEST Electric City Transit",
    vehicle_model: "BEST Electric City Transit",
    color: "Red",
    vehicle_color: "Red",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/mumbai_bus_transit.jpg",
    city: "Mumbai Safe City Mesh",
    latest_sighting: {
      timestamp: "Today, 13:40:20",
      location: "Dadar Plaza Traffic Intersection",
      camera_id: "CAM-04",
      camera_name: "CAM-04 Dadar Plaza Intersection Gantry",
      city: "Mumbai Safe City Mesh",
      latitude: 19.0178,
      longitude: 72.8478,
      speed_kmh: 28.0,
      evidence_image: "/snapshots/mumbai_bus_transit.jpg"
    },
    metadata: {
      first_seen: "Today, 11:00:00",
      last_seen: "Today, 13:40:20",
      total_sightings: 1,
      associated_cameras: ["CAM-04"]
    },
    flag_status: {
      is_flagged: false,
      reason: null,
      note: "",
      flagged_at: null
    },
    sightings: [
      { camera_id: "CAM-04", camera_name: "CAM-04 Dadar Plaza", location: "Dadar Central Bus Terminal", timestamp: "13:40:20", speed_kmh: 28.0, direction: "Westbound", latitude: 19.0178, longitude: 72.8478 }
    ]
  }
];

// Local offline search engine for fallback
export function searchLocalVehicles({ plate_number, vehicle_type, color, location, vehicle_model }) {
  let matches = [...LOCAL_VEHICLES];

  if (plate_number && plate_number.trim()) {
    const q = plate_number.replace(/\s+/g, '').toUpperCase();
    matches = matches.filter(v => {
      const p = (v.plate || v.plate_number || '').replace(/\s+/g, '').toUpperCase();
      return p.includes(q);
    });
  }

  if (vehicle_type && vehicle_type !== 'All') {
    const vt = vehicle_type.toLowerCase();
    matches = matches.filter(v => {
      const t = (v.type || v.vehicle_type || '').toLowerCase();
      return t.includes(vt);
    });
  }

  if (color && color !== 'All') {
    const c = color.toLowerCase();
    matches = matches.filter(v => {
      const col = (v.color || v.vehicle_color || '').toLowerCase();
      return col.includes(c);
    });
  }

  if (location && location !== 'All') {
    const l = location.toLowerCase();
    matches = matches.filter(v => {
      const loc = (v.latest_sighting?.location || '').toLowerCase();
      const cam = (v.latest_sighting?.camera_name || v.latest_sighting?.camera_id || '').toLowerCase();
      return loc.includes(l) || cam.includes(l);
    });
  }

  if (vehicle_model && vehicle_model.trim()) {
    const m = vehicle_model.toLowerCase();
    matches = matches.filter(v => {
      const mod = (v.model || v.vehicle_model || '').toLowerCase();
      return mod.includes(m);
    });
  }

  return matches;
}
