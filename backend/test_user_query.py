import urllib.request
import json
import os

user_img_path = r"C:\Users\ASUS\.gemini\antigravity-ide\brain\a37facc1-81b2-4b82-a729-1e6a1a74d1e3\.user_uploaded\media_1787078208919.png"
with open(user_img_path, "rb") as f:
    file_bytes = f.read()

boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="user_query.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(
    "http://localhost:8000/api/person/search?min_similarity=0.30",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST"
)
res = urllib.request.urlopen(req)
data = json.loads(res.read().decode())
print(f"[OK] Matches Returned: {data.get('total_matches')}")
for idx, m in enumerate(data.get("matches", [])[:5]):
    s = m["sightings"][0]
    print(f"  [{idx+1}] Match: {m['name']} | Sim: {m['similarity']}% | Cam: {s['camera_name']} | Time: {s['timestamp']}")
