// Canonical Offline-Ready Verified Surveillance Vehicle Dataset
// Ensures Vehicle Intelligence & Re-ID works instantly on any machine even when backend is offline

export const LOCAL_VEHICLES = [
  {
    vehicle_id: "VEH-MH43BF3945",
    plate_number: "MH 43 BF 3945",
    vehicle_type: "Auto-Rickshaw (3-Wheeler)",
    vehicle_model: "Bajaj RE Auto-Rickshaw Commercial",
    vehicle_color: "Yellow",
    is_stolen: true,
    bolo_status: "CRITICAL: BOLO Target Active Flag",
    snapshot: "/snapshots/autorickshaw_mh43bf3945.jpg",
    city: "Mumbai Safe City Mesh",
    location: "CBD Belapur Flyover Ingress",
    camera_id: "CAM-01",
    camera_name: "CAM-01 CBD Belapur Flyover Intercept",
    lat: 19.0180,
    lon: 73.0410,
    speed_kmh: 24.5,
    confidence: 0.984,
    first_seen: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    sightings: [
      { camera: "CAM-01 CBD Belapur Flyover", location: "CBD Belapur Flyover Ingress", timestamp: new Date(Date.now() - 1000 * 60 * 5).toLocaleTimeString(), speed: "24.5 km/h", direction: "Southbound" },
      { camera: "CAM-02 Kharghar Municipal Gantry", location: "Kharghar Sector 12 Arterial", timestamp: new Date(Date.now() - 1000 * 60 * 32).toLocaleTimeString(), speed: "28.0 km/h", direction: "Southbound" },
      { camera: "CAM-03 Vashi Toll Plaza", location: "Vashi Plaza Outer Lane 2", timestamp: new Date(Date.now() - 1000 * 60 * 75).toLocaleTimeString(), speed: "31.2 km/h", direction: "Eastbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH46CB0005",
    plate_number: "MH 46 CB 0005",
    vehicle_type: "Car (SUV)",
    vehicle_model: "Mahindra Thar 4x4 Offroad SUV",
    vehicle_color: "Green",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/mahindra_thar_mh46cb0005.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Navi Mumbai Rangoli Junction / Khandeshwar",
    camera_id: "CAM-01",
    camera_name: "CAM-01 Rangoli Intersection Intercept",
    lat: 19.0125,
    lon: 73.0880,
    speed_kmh: 38.0,
    confidence: 0.965,
    first_seen: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
    sightings: [
      { camera: "CAM-01 Rangoli Intersection", location: "Rangoli Junction North", timestamp: new Date(Date.now() - 1000 * 60 * 12).toLocaleTimeString(), speed: "38.0 km/h", direction: "Northbound" },
      { camera: "CAM-04 Panvel Bypass Gate", location: "Old Mumbai-Pune Highway", timestamp: new Date(Date.now() - 1000 * 60 * 45).toLocaleTimeString(), speed: "44.5 km/h", direction: "Northbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH46CT5126",
    plate_number: "MH 46 CT 5126",
    vehicle_type: "Car (Sedan)",
    vehicle_model: "BMW 3 Series Luxury Sedan",
    vehicle_color: "White",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/bmw_mh46ct5126.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Panvel East Expressway Corridor",
    camera_id: "CAM-02",
    camera_name: "CAM-02 Panvel East Expressway Gantry",
    lat: 18.9920,
    lon: 73.1250,
    speed_kmh: 62.0,
    confidence: 0.991,
    first_seen: new Date(Date.now() - 1000 * 60 * 150).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 18).toISOString(),
    sightings: [
      { camera: "CAM-02 Panvel East Expressway", location: "Panvel Expressway Toll Ingress", timestamp: new Date(Date.now() - 1000 * 60 * 18).toLocaleTimeString(), speed: "62.0 km/h", direction: "Westbound" },
      { camera: "CAM-05 Kalamboli Circle", location: "Kalamboli Expressway Junction", timestamp: new Date(Date.now() - 1000 * 60 * 55).toLocaleTimeString(), speed: "58.0 km/h", direction: "Westbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH48DX1051",
    plate_number: "MH 48 DX 1051",
    vehicle_type: "Car (Electric SUV)",
    vehicle_model: "Mahindra BE 6e Electric SUV",
    vehicle_color: "Blue",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/mahindra_ev_mh48dx1051.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Vasai-Virar Arterial Corridor",
    camera_id: "CAM-03",
    camera_name: "CAM-03 Vasai-Virar Municipal Corridor",
    lat: 19.3838,
    lon: 72.8282,
    speed_kmh: 35.0,
    confidence: 0.978,
    first_seen: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
    sightings: [
      { camera: "CAM-03 Vasai-Virar Corridor", location: "Vasai West Highway Checkpoint", timestamp: new Date(Date.now() - 1000 * 60 * 20).toLocaleTimeString(), speed: "35.0 km/h", direction: "Northbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH43CG3824",
    plate_number: "MH 43 CG 3824",
    vehicle_type: "Car (SUV)",
    vehicle_model: "Tata Punch Compact SUV",
    vehicle_color: "Blue",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/tata_punch_mh43cg3824.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Navi Mumbai Kharghar Sector 12",
    camera_id: "CAM-02",
    camera_name: "CAM-02 Kharghar Municipal Corridor",
    lat: 19.0345,
    lon: 73.0645,
    speed_kmh: 32.5,
    confidence: 0.972,
    first_seen: new Date(Date.now() - 1000 * 60 * 110).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 25).toISOString(),
    sightings: [
      { camera: "CAM-02 Kharghar Municipal Corridor", location: "Sector 12 Intersection", timestamp: new Date(Date.now() - 1000 * 60 * 25).toLocaleTimeString(), speed: "32.5 km/h", direction: "Eastbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH46DF9820",
    plate_number: "MH 46 DF 9820",
    vehicle_type: "Car (SUV)",
    vehicle_model: "Tata Punch SUV",
    vehicle_color: "White",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/tata_punch_mh46df9820.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Vashi Sector 17 Transit Gate",
    camera_id: "CAM-01",
    camera_name: "CAM-01 Vashi Transit Gate",
    lat: 19.0770,
    lon: 72.9980,
    speed_kmh: 22.0,
    confidence: 0.968,
    first_seen: new Date(Date.now() - 1000 * 60 * 85).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 28).toISOString(),
    sightings: [
      { camera: "CAM-01 Vashi Transit Gate", location: "Sector 17 Commercial Entrance", timestamp: new Date(Date.now() - 1000 * 60 * 28).toLocaleTimeString(), speed: "22.0 km/h", direction: "Inbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH43CB8645",
    plate_number: "MH 43 CB 8645",
    vehicle_type: "Auto-Rickshaw (3-Wheeler)",
    vehicle_model: "Bajaj RE Auto-Rickshaw",
    vehicle_color: "Yellow",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/autorickshaw_mh43cb8645.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Navi Mumbai Auto Stand Junction",
    camera_id: "CAM-02",
    camera_name: "CAM-02 Navi Mumbai Auto Stand",
    lat: 19.0330,
    lon: 73.0297,
    speed_kmh: 18.5,
    confidence: 0.954,
    first_seen: new Date(Date.now() - 1000 * 60 * 140).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    sightings: [
      { camera: "CAM-02 Navi Mumbai Auto Stand", location: "CBD Transit Stand", timestamp: new Date(Date.now() - 1000 * 60 * 30).toLocaleTimeString(), speed: "18.5 km/h", direction: "Stationary" }
    ]
  },
  {
    vehicle_id: "VEH-MH04KY5983",
    plate_number: "MH 04 KY 5983",
    vehicle_type: "Motorcycle",
    vehicle_model: "Yamaha YZF-R15 Sports Motorcycle",
    vehicle_color: "Blue",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/sports_bike_mh04ky5983.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Thane-Belapur Expressway Flyover",
    camera_id: "CAM-04",
    camera_name: "CAM-04 Thane-Belapur Expressway Gantry",
    lat: 19.1120,
    lon: 73.0110,
    speed_kmh: 58.0,
    confidence: 0.987,
    first_seen: new Date(Date.now() - 1000 * 60 * 95).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 35).toISOString(),
    sightings: [
      { camera: "CAM-04 Thane-Belapur Expressway", location: "Rabale Flyover Ingress", timestamp: new Date(Date.now() - 1000 * 60 * 35).toLocaleTimeString(), speed: "58.0 km/h", direction: "Northbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH46BK0500",
    plate_number: "MH 46 BK 0500",
    vehicle_type: "Car (MPV)",
    vehicle_model: "Toyota Innova Crysta MPV",
    vehicle_color: "Silver",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/toyota_innova_mh46bk0500.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Panvel Station Ring Road",
    camera_id: "CAM-03",
    camera_name: "CAM-03 Panvel Ring Road Gantry",
    lat: 18.9890,
    lon: 73.1190,
    speed_kmh: 29.0,
    confidence: 0.963,
    first_seen: new Date(Date.now() - 1000 * 60 * 160).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 40).toISOString(),
    sightings: [
      { camera: "CAM-03 Panvel Ring Road", location: "Panvel Station Approach", timestamp: new Date(Date.now() - 1000 * 60 * 40).toLocaleTimeString(), speed: "29.0 km/h", direction: "Eastbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH03BK8453",
    plate_number: "MH 03 BK 8453",
    vehicle_type: "Car (Sedan)",
    vehicle_model: "Honda City VTEC Sedan",
    vehicle_color: "Black",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/honda_city_mh03bk8453.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Kharghar Arterial Corridor",
    camera_id: "CAM-03",
    camera_name: "CAM-03 Kharghar Arterial Gantry",
    lat: 19.0380,
    lon: 73.0690,
    speed_kmh: 42.0,
    confidence: 0.958,
    first_seen: new Date(Date.now() - 1000 * 60 * 180).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
    sightings: [
      { camera: "CAM-03 Kharghar Arterial", location: "Kharghar Toll Node", timestamp: new Date(Date.now() - 1000 * 60 * 45).toLocaleTimeString(), speed: "42.0 km/h", direction: "Southbound" }
    ]
  },
  {
    vehicle_id: "VEH-MH01BUS204",
    plate_number: "MH 01 LA 4412",
    vehicle_type: "Public Transit Bus",
    vehicle_model: "BEST Electric Transit Bus",
    vehicle_color: "Red",
    is_stolen: false,
    bolo_status: "NORMAL: Verified Vehicle Registry",
    snapshot: "/snapshots/mumbai_bus_transit.jpg",
    city: "Mumbai Safe City Mesh",
    location: "Dadar Plaza Traffic Intersection",
    camera_id: "CAM-04",
    camera_name: "CAM-04 Dadar Plaza Intersection Gantry",
    lat: 19.0178,
    lon: 72.8478,
    speed_kmh: 28.0,
    confidence: 0.981,
    first_seen: new Date(Date.now() - 1000 * 60 * 200).toISOString(),
    last_seen: new Date(Date.now() - 1000 * 60 * 50).toISOString(),
    sightings: [
      { camera: "CAM-04 Dadar Plaza", location: "Dadar Central Bus Terminal", timestamp: new Date(Date.now() - 1000 * 60 * 50).toLocaleTimeString(), speed: "28.0 km/h", direction: "Westbound" }
    ]
  }
];

// Local offline search engine for fallback
export function searchLocalVehicles({ plate_number, vehicle_type, color, location, vehicle_model }) {
  let matches = [...LOCAL_VEHICLES];

  if (plate_number) {
    const q = plate_number.replace(/\s+/g, '').toUpperCase();
    matches = matches.filter(v => v.plate_number.replace(/\s+/g, '').toUpperCase().includes(q));
  }

  if (vehicle_type && vehicle_type !== 'All') {
    const vt = vehicle_type.toLowerCase();
    matches = matches.filter(v => v.vehicle_type.toLowerCase().includes(vt));
  }

  if (color && color !== 'All') {
    const c = color.toLowerCase();
    matches = matches.filter(v => v.vehicle_color.toLowerCase().includes(c));
  }

  if (location && location !== 'All') {
    const l = location.toLowerCase();
    matches = matches.filter(v => v.location.toLowerCase().includes(l) || v.camera_name.toLowerCase().includes(l));
  }

  if (vehicle_model) {
    const m = vehicle_model.toLowerCase();
    matches = matches.filter(v => v.vehicle_model.toLowerCase().includes(m));
  }

  return matches;
}
