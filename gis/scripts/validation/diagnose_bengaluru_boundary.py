from pathlib import Path
import geopandas as gpd
from shapely.geometry import Point


ROOT = Path(__file__).resolve().parents[2]

boundary_file = (
    ROOT
    / "data"
    / "processed"
    / "boundaries"
    / "bengaluru_boundary.gpkg"
)


print("=" * 70)
print("VIGRAH — BENGALURU BOUNDARY DIAGNOSTIC")
print("=" * 70)

print("\nBoundary file:")
print(boundary_file)

gdf = gpd.read_file(
    boundary_file,
    layer="boundary"
)

print("\n--- Boundary information ---")
print("CRS:", gdf.crs)
print("Features:", len(gdf))

geometry = gdf.geometry.union_all()

print("\nBoundary bounds:")
print(
    f"West  : {geometry.bounds[0]:.6f}"
)
print(
    f"South : {geometry.bounds[1]:.6f}"
)
print(
    f"East  : {geometry.bounds[2]:.6f}"
)
print(
    f"North : {geometry.bounds[3]:.6f}"
)

print("\nGeometry:")
print("Valid:", geometry.is_valid)
print("Empty:", geometry.is_empty)
print("Type:", geometry.geom_type)


# Known Bengaluru CCTV point from our validated dataset
test_point = Point(
    77.584179,
    12.977914
)

print("\n--- Known Bengaluru CCTV point ---")
print("Longitude:", test_point.x)
print("Latitude :", test_point.y)

print(
    "Inside boundary:",
    geometry.contains(test_point)
)

print(
    "Intersects boundary:",
    geometry.intersects(test_point)
)

print(
    "Distance to boundary:",
    geometry.distance(test_point)
)

print("\n--- Test complete ---")