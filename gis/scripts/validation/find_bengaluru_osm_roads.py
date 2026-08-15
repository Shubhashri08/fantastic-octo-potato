from pathlib import Path
import osmium


ROOT = Path(__file__).resolve().parents[2]

PBF = (
    ROOT
    / "data"
    / "raw"
    / "osm"
    / "OSM_CENTRAL_ZONE_LATEST.osm.pbf"
)


# Bengaluru operational boundary bounds
WEST = 77.325603
SOUTH = 12.657495
EAST = 77.836009
NORTH = 13.233085


ROAD_CLASSES = {
    "motorway",
    "motorway_link",
    "trunk",
    "trunk_link",
    "primary",
    "primary_link",
    "secondary",
    "secondary_link",
    "tertiary",
    "tertiary_link",
    "residential",
    "living_street",
    "unclassified",
    "road",
}


class BengaluruRoadFinder(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.highway_ways = 0
        self.bbox_candidates = 0
        self.examples = []

    def way(self, w):

        highway = w.tags.get("highway")

        if highway is None:
            return

        self.highway_ways += 1

        if highway not in ROAD_CLASSES:
            return

        if len(w.nodes) < 2:
            return

        # Find whether ANY node of this way falls inside
        # the Bengaluru boundary bounding box.
        found = False

        for node in w.nodes:

            if not node.location.valid():
                continue

            lon = node.lon
            lat = node.lat

            if (
                WEST <= lon <= EAST
                and
                SOUTH <= lat <= NORTH
            ):
                found = True
                break

        if not found:
            return

        self.bbox_candidates += 1

        if len(self.examples) < 10:

            self.examples.append(
                {
                    "id": w.id,
                    "highway": highway,
                    "name": w.tags.get("name"),
                    "lon": lon,
                    "lat": lat,
                    "nodes": len(w.nodes),
                }
            )


print("=" * 70)
print("VIGRAH — BENGALURU OSM COVERAGE DIAGNOSTIC")
print("=" * 70)

print("\nPBF:")
print(PBF)

print("\nTarget bounding box:")
print(f"West : {WEST}")
print(f"South: {SOUTH}")
print(f"East : {EAST}")
print(f"North: {NORTH}")

print("\nScanning highway ways...")
print("This will read the PBF but will NOT create any output dataset.")

handler = BengaluruRoadFinder()

handler.apply_file(
    str(PBF),
    locations=True
)

print("\n" + "=" * 70)
print("RESULT")
print("=" * 70)

print(
    f"\nHighway ways encountered: "
    f"{handler.highway_ways:,}"
)

print(
    f"Highway ways with at least one node "
    f"inside Bengaluru bbox: "
    f"{handler.bbox_candidates:,}"
)

print("\nExample Bengaluru-area roads:")

for road in handler.examples:

    print(
        f"\nOSM ID: {road['id']}"
        f"\n  highway: {road['highway']}"
        f"\n  name: {road['name']}"
        f"\n  coordinate: "
        f"{road['lon']:.6f}, {road['lat']:.6f}"
        f"\n  nodes: {road['nodes']}"
    )

print("\nDiagnostic complete.")