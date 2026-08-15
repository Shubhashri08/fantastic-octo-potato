import osmium
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PBF = (
    ROOT
    / "data"
    / "raw"
    / "osm"
    / "OSM_SOUTHERN_ZONE_LATEST.osm.pbf"
)


print("=" * 70)
print("VIGRAH — BENGALURU OSM SOURCE CHECK")
print("=" * 70)

print("\nFile:")
print(PBF)

if not PBF.exists():
    raise FileNotFoundError(PBF)

print(
    f"\nSize: "
    f"{PBF.stat().st_size / (1024 * 1024):,.2f} MB"
)

processor = osmium.FileProcessor(str(PBF))

box = processor.header.box()

print("\nBounding box:")

print(
    f"West  : {box.bottom_left.lon:.6f}"
)

print(
    f"South : {box.bottom_left.lat:.6f}"
)

print(
    f"East  : {box.top_right.lon:.6f}"
)

print(
    f"North : {box.top_right.lat:.6f}"
)


# Bengaluru approximate target bounds
BLR_WEST = 77.325603
BLR_SOUTH = 12.657495
BLR_EAST = 77.836009
BLR_NORTH = 13.233085


covers_bengaluru = (
    box.bottom_left.lon <= BLR_WEST
    and box.top_right.lon >= BLR_EAST
    and box.bottom_left.lat <= BLR_SOUTH
    and box.top_right.lat >= BLR_NORTH
)


print("\nCovers complete Bengaluru boundary:")
print(covers_bengaluru)

if not covers_bengaluru:
    raise RuntimeError(
        "Southern Zone PBF does not cover the complete "
        "Bengaluru operational boundary."
    )

print("\nSOURCE CHECK PASSED.")