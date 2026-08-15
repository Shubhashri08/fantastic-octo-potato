import osmium
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OSM_DIR = ROOT / "data" / "raw" / "osm"

FILES = {
    "Western Zone": OSM_DIR / "OSM_WESTERN_ZONE_LATEST.osm.pbf",
    "Central Zone": OSM_DIR / "OSM_CENTRAL_ZONE_LATEST.osm.pbf",
}


for name, path in FILES.items():

    print("\n" + "=" * 70)
    print(name)
    print("=" * 70)

    if not path.exists():
        print("[MISSING]")
        print(path)
        continue

    print(f"File: {path.name}")
    print(
        f"Size: {path.stat().st_size / (1024 * 1024):,.2f} MB"
    )

    processor = osmium.FileProcessor(str(path))
    box = processor.header.box()

    if not box.valid():
        print("\nNo valid bounding box stored in PBF header.")
        continue

    bottom_left = box.bottom_left
    top_right = box.top_right

    print("\nHeader bounding box:")

    print(
        f"  West  (xmin): {bottom_left.lon:.6f}"
    )

    print(
        f"  South (ymin): {bottom_left.lat:.6f}"
    )

    print(
        f"  East  (xmax): {top_right.lon:.6f}"
    )

    print(
        f"  North (ymax): {top_right.lat:.6f}"
    )