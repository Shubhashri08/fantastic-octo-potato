import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
JSON_SRC = os.path.join(BASE_DIR, "city_mesh_networks.json")

with open(JSON_SRC, "r", encoding="utf-8") as f:
    data = json.load(f)

# 1. Export Clean JSON in Project Root
out_json = os.path.join(PROJECT_ROOT, "MUMBAI_BENGALURU_CCTV_DATA.json")
with open(out_json, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

# 2. Export Human-Readable Markdown in Project Root
out_md = os.path.join(PROJECT_ROOT, "MUMBAI_BENGALURU_CCTV_DATA.md")
with open(out_md, "w", encoding="utf-8") as f:
    f.write("# 📡 VIGRAH AI — Multi-City CCTV Surveillance Grid Dataset\n\n")
    f.write("This file contains the verified GPS coordinates, intersection names, surveillance zones, and mapped video feeds for **Mumbai** and **Bengaluru**.\n\n")

    for city_name, city_info in data.items():
        f.write(f"## 🏙️ {city_name} CCTV Network\n")
        f.write(f"- **State**: {city_info.get('state')}\n")
        f.write(f"- **GPS Center**: `{city_info.get('center')}`\n")
        f.write(f"- **Total Nodes**: `{city_info.get('total_nodes')}`\n")
        f.write(f"- **Dataset Source**: {city_info.get('source')}\n\n")

        f.write("| Node ID | Camera / Location Name | Latitude | Longitude | Zone | Mapped Video Feed |\n")
        f.write("| :--- | :--- | :---: | :---: | :--- | :--- |\n")
        for node in city_info.get("nodes", [])[:25]:
            f.write(f"| **{node['id']}** | {node['name']} | `{node['lat']}` | `{node['lon']}` | {node.get('zone', 'City Grid')} | `{node.get('video_filename', 'Mapped Feed')}` |\n")
        
        remaining = len(city_info.get("nodes", [])) - 25
        if remaining > 0:
            f.write(f"| *...and {remaining} more nodes* | *(Full list in MUMBAI_BENGALURU_CCTV_DATA.json)* | - | - | - | - |\n")
        f.write("\n---\n\n")

print(f"Generated:")
print(f"  - {out_json}")
print(f"  - {out_md}")
