import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import urllib.request
import os
import glob
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
crop_files = glob.glob(os.path.join(BASE_DIR, "snapshots", "crop_person_cam*.jpg"))

if crop_files:
    test_file = crop_files[0]
    print(f"Testing real query photo upload: {os.path.basename(test_file)}")

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(test_file, "rb") as f:
        file_bytes = f.read()

    header = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(test_file)}"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode()
    footer = f"\r\n--{boundary}--\r\n".encode()
    body = header + file_bytes + footer

    req = urllib.request.Request(
        "http://localhost:8000/api/person/search?min_similarity=0.40",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read().decode())
    print(f"\n[OK] REAL BIOMETRIC RE-ID MATCH RESULTS ({data.get('total_matches')} Matches Found):")
    for idx, m in enumerate(data.get("matches", [])[:5]):
        s = m["sightings"][0]
        print(f"  [{idx+1}] Match: {m['name']}")
        print(f"      - Similarity: {m['similarity']}%")
        print(f"      - Camera: {s['camera_name']} (Cam ID: {s['camera_id']})")
        print(f"      - Location: {s['city']} (GPS: {s['lat']}, {s['lon']})")
        print(f"      - Sighting Time: {s['timestamp']}")
        print(f"      - Evidence Crop: {s['snapshot']}")
else:
    print("No crop snapshots found yet.")
