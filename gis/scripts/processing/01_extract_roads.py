from pathlib import Path
import osmium
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString
from pyproj import Transformer


# ============================================================
# VIGRAH — PHASE A / A3
# Extract road network from OSM PBFs
# ============================================================

ROOT = Path(__file__).resolve().parents[2]

RAW_OSM = ROOT / "data" / "raw" / "osm"
BOUNDARY_DIR = ROOT / "data" / "processed" / "boundaries"
OUTPUT_DIR = ROOT / "data" / "processed" / "osm"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Road classes to retain
# ------------------------------------------------------------

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


# ------------------------------------------------------------
# Dataset configuration
# ------------------------------------------------------------

DATASETS = {
    "Mumbai": {
        "pbf": RAW_OSM / "OSM_WESTERN_ZONE_LATEST.osm.pbf",
        "boundary": BOUNDARY_DIR / "mumbai_boundary.gpkg",
        "output": OUTPUT_DIR / "mumbai_roads.parquet",
    },

    "Bengaluru": {
        "pbf": RAW_OSM / "OSM_SOUTHERN_ZONE_LATEST.osm.pbf",
        "boundary": BOUNDARY_DIR / "bengaluru_boundary.gpkg",
        "output": OUTPUT_DIR / "bengaluru_roads.parquet",
    },
}


# ------------------------------------------------------------
# OSM streaming handler
# ------------------------------------------------------------

class RoadHandler(osmium.SimpleHandler):

    def __init__(self, boundary, city):
        super().__init__()

        self.boundary = boundary
        self.city = city

        self.roads = []

        self.total_ways = 0
        self.highway_ways = 0
        self.retained_ways = 0

    def way(self, w):

        self.total_ways += 1

        highway = w.tags.get("highway")

        if highway is None:
            return

        self.highway_ways += 1

        if highway not in ROAD_CLASSES:
            return

        # Need at least two points for a line
        if len(w.nodes) < 2:
            return

        coordinates = []

        try:

            for node in w.nodes:

                if not node.location.valid():
                    return

                coordinates.append(
                    (
                        node.lon,
                        node.lat
                    )
                )

        except Exception:
            return

        if len(coordinates) < 2:
            return

        try:

            geometry = LineString(coordinates)

        except Exception:
            return

        # Spatial filtering
        #
        # We first check the road bounding box against
        # the target city boundary.
        if not geometry.intersects(self.boundary):
            return

        self.retained_ways += 1

        tags = w.tags

        self.roads.append(
            {
                "road_id": int(w.id),

                "road_name":
                    tags.get("name"),

                "highway":
                    highway,

                "oneway":
                    tags.get("oneway"),

                "lanes":
                    tags.get("lanes"),

                "maxspeed":
                    tags.get("maxspeed"),

                "surface":
                    tags.get("surface"),

                "bridge":
                    tags.get("bridge"),

                "tunnel":
                    tags.get("tunnel"),

                "city":
                    self.city,

                "geometry":
                    geometry,
            }
        )


# ------------------------------------------------------------
# Process one city
# ------------------------------------------------------------

def process_city(city, config):

    print("\n" + "=" * 80)
    print(f"EXTRACTING ROADS — {city.upper()}")
    print("=" * 80)

    pbf = config["pbf"]
    boundary_file = config["boundary"]
    output = config["output"]

    if not pbf.exists():
        raise FileNotFoundError(
            f"OSM PBF not found:\n{pbf}"
        )

    if not boundary_file.exists():
        raise FileNotFoundError(
            f"Boundary not found:\n{boundary_file}"
        )

    print(f"\nPBF:")
    print(pbf)

    print(
        f"Size: "
        f"{pbf.stat().st_size / (1024 * 1024):,.2f} MB"
    )

    print("\nReading boundary...")

    boundary_gdf = gpd.read_file(
        boundary_file,
        layer="boundary"
    )

    if boundary_gdf.empty:
        raise ValueError(
            f"Boundary is empty: {boundary_file}"
        )

    boundary_gdf = boundary_gdf.to_crs(
        "EPSG:4326"
    )

    boundary = boundary_gdf.geometry.union_all()

    print(
        f"Boundary CRS: {boundary_gdf.crs}"
    )

    print("\nStreaming OSM PBF...")

    handler = RoadHandler(
        boundary=boundary,
        city=city
    )

    # IMPORTANT:
    # locations=True is required because we need
    # coordinates for way nodes.
    handler.apply_file(
        str(pbf),
        locations=True
    )

    print("\n--- Extraction statistics ---")

    print(
        f"Total ways read:       "
        f"{handler.total_ways:,}"
    )

    print(
        f"Highway ways:          "
        f"{handler.highway_ways:,}"
    )

    print(
        f"Roads retained:        "
        f"{handler.retained_ways:,}"
    )

    if not handler.roads:
        raise RuntimeError(
            f"No roads were extracted for {city}."
        )

    # --------------------------------------------------------
    # Create GeoDataFrame
    # --------------------------------------------------------

    roads = gpd.GeoDataFrame(
        handler.roads,
        geometry="geometry",
        crs="EPSG:4326"
    )

    # --------------------------------------------------------
    # Clip geometries exactly to boundary
    # --------------------------------------------------------

    print("\nClipping roads to city boundary...")

    roads = gpd.clip(
        roads,
        boundary_gdf
    )

    roads = roads[
        ~roads.geometry.is_empty
    ].copy()

    roads = roads[
        roads.geometry.notna()
    ].copy()

    # --------------------------------------------------------
    # Normalize IDs
    # --------------------------------------------------------

    roads["road_id"] = (
        roads["road_id"]
        .astype("int64")
    )

    roads["city"] = city

    # --------------------------------------------------------
    # Save GeoParquet
    # --------------------------------------------------------

    print("\nSaving:")

    print(output)

    roads.to_parquet(
        output,
        index=False
    )

    print("\n--- Final dataset ---")

    print(
        f"Road features: "
        f"{len(roads):,}"
    )

    print(
        f"CRS: "
        f"{roads.crs}"
    )

    print("\nHighway distribution:")

    print(
        roads["highway"]
        .value_counts()
        .to_string()
    )

    print("\nNamed roads:")

    print(
        roads["road_name"]
        .notna()
        .sum()
    )

    print(
        f"\nOutput size: "
        f"{output.stat().st_size / (1024 * 1024):,.2f} MB"
    )

    print("\nSUCCESS")


# ------------------------------------------------------------
# Main
# ------------------------------------------------------------

def main():

    print("=" * 80)
    print("VIGRAH — A3 OSM ROAD EXTRACTION")
    print("=" * 80)

    for city, config in DATASETS.items():

        process_city(
            city,
            config
        )

    print("\n" + "=" * 80)
    print("A3 COMPLETE")
    print("=" * 80)

    print("\nCreated:")

    for file in OUTPUT_DIR.glob("*.parquet"):

        print(
            f"  {file.name} "
            f"({file.stat().st_size / (1024 * 1024):,.2f} MB)"
        )

def main():

    print("=" * 80)
    print("VIGRAH — A3 OSM ROAD EXTRACTION")
    print("=" * 80)

    process_city(
        "Bengaluru",
        DATASETS["Bengaluru"]
    )

    print("\n" + "=" * 80)
    print("BENGALURU A3 COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()