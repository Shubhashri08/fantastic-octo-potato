import osmium
from pathlib import Path
from collections import Counter


ROOT = Path(__file__).resolve().parents[2]
OSM_DIR = ROOT / "data" / "raw" / "osm"

FILES = {
    "Mumbai / Western Zone":
        OSM_DIR / "OSM_WESTERN_ZONE_LATEST.osm.pbf",

    "Bengaluru / Central Zone":
        OSM_DIR / "OSM_CENTRAL_ZONE_LATEST.osm.pbf",
}


class OSMInspector(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()

        self.nodes = 0
        self.ways = 0
        self.relations = 0

        self.highway_counts = Counter()
        self.named_roads = 0
        self.total_ways_with_highway = 0

    def node(self, n):
        self.nodes += 1

    def way(self, w):

        self.ways += 1

        highway = w.tags.get("highway")

        if highway:
            self.total_ways_with_highway += 1
            self.highway_counts[highway] += 1

        if w.tags.get("name"):
            self.named_roads += 1

    def relation(self, r):
        self.relations += 1


def inspect(label, path):

    print("\n" + "=" * 80)
    print(label)
    print("=" * 80)

    if not path.exists():
        print("[MISSING]")
        print(path)
        return

    print(f"File: {path}")
    print(
        f"Size: {path.stat().st_size / (1024 * 1024):,.2f} MB"
    )

    inspector = OSMInspector()

    print("\nReading PBF...")
    print("This may take a while because the extract is large.")

    inspector.apply_file(
        str(path),
        locations=False
    )

    print("\n--- Element counts ---")
    print(f"Nodes:      {inspector.nodes:,}")
    print(f"Ways:       {inspector.ways:,}")
    print(f"Relations:  {inspector.relations:,}")

    print("\n--- Road information ---")
    print(
        f"Ways containing highway tag: "
        f"{inspector.total_ways_with_highway:,}"
    )

    print(
        f"Named road ways: "
        f"{inspector.named_roads:,}"
    )

    print("\n--- Highway classes ---")

    for highway, count in inspector.highway_counts.most_common():

        print(
            f"{highway:<25} {count:,}"
        )


def main():

    print("=" * 80)
    print("VIGRAH — OSM RAW DATA INSPECTION")
    print("=" * 80)

    print(f"\nOSM directory: {OSM_DIR}")

    print("\nIMPORTANT:")
    print("This script ONLY reads the PBF files.")
    print("It does NOT modify them.")
    print("It does NOT create processed datasets.")

    for label, path in FILES.items():

        inspect(
            label,
            path
        )

    print("\n" + "=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()