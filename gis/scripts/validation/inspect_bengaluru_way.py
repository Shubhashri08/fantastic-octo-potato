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


class HighwayInspector(osmium.SimpleHandler):

    def __init__(self):
        super().__init__()
        self.found = False

    def way(self, w):

        if self.found:
            return

        highway = w.tags.get("highway")

        if highway is None:
            return

        print("=" * 70)
        print("FIRST HIGHWAY WAY FOUND")
        print("=" * 70)

        print("Way ID:", w.id)
        print("Highway:", highway)
        print("Name:", w.tags.get("name"))

        print("\nNode count:", len(w.nodes))

        print("\nFirst 5 nodes:")

        for node in list(w.nodes)[:5]:

            print(
                "node:",
                node.ref,
                "lon:",
                node.lon,
                "lat:",
                node.lat,
                "valid:",
                node.location.valid()
            )

        self.found = True


print("Reading:", PBF)
print("Please wait...")

handler = HighwayInspector()

handler.apply_file(
    str(PBF),
    locations=True
)

print("\nInspection complete.")