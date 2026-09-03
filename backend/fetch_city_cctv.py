import urllib.request
import urllib.parse
import json
import os

headers = {'User-Agent': 'VigrahAI-CCTV-Mesh-Scraper/1.0'}

def fetch_osm_cctv(city_name, bbox):
    """
    Fetches real CCTV surveillance camera nodes from OpenStreetMap Overpass API
    within the bounding box [south, west, north, east].
    """
    s, w, n, e = bbox
    query = f"""
    [out:json][timeout:25];
    (
      node["man_made"="surveillance"]({s},{w},{n},{e});
      node["surveillance"]({s},{w},{n},{e});
      node["camera:type"]({s},{w},{n},{e});
    );
    out body 60;
    """
    url = 'https://overpass-api.de/api/interpreter?data=' + urllib.parse.quote(query)
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            elements = data.get('elements', [])
            cams = []
            for el in elements:
                tags = el.get('tags', {})
                name = tags.get('name') or tags.get('description') or tags.get('operator') or f"{city_name} CCTV Node"
                cams.append({
                    "id": el.get('id'),
                    "name": name,
                    "lat": el.get('lat'),
                    "lon": el.get('lon'),
                    "type": tags.get('surveillance:type') or tags.get('camera:type') or 'surveillance'
                })
            print(f"✅ {city_name}: Successfully retrieved {len(cams)} real CCTV nodes from OpenStreetMap!")
            return cams
    except Exception as e:
        print(f"⚠️ {city_name} query: {e}")
        return []

# Bounding boxes for major cities: [south, west, north, east]
city_bboxes = {
    "Mumbai": [18.8900, 72.7700, 19.2800, 73.0200],
    "Delhi": [28.4000, 76.8400, 28.8800, 77.3500],
    "Hyderabad": [17.2500, 78.2500, 17.5500, 78.6500],
    "London": [51.4500, -0.2500, 51.5800, 0.0500],
    "New York": [40.6500, -74.0500, 40.8500, -73.8500]
}

all_city_networks = {}

for city, bbox in city_bboxes.items():
    print(f"Fetching CCTV mesh for {city}...")
    nodes = fetch_osm_cctv(city, bbox)
    all_city_networks[city] = {
        "city": city,
        "center": [(bbox[0] + bbox[2]) / 2.0, (bbox[1] + bbox[3]) / 2.0],
        "total_nodes": len(nodes),
        "nodes": nodes
    }

out_path = os.path.join(os.path.dirname(__file__), "city_mesh_networks.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(all_city_networks, f, indent=2)

print(f"\n🎉 Saved all multi-city CCTV mesh networks to {out_path} ({os.path.getsize(out_path):,} bytes)!")
