import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app.database import SessionLocal
from app.vehicle_service import search_vehicles

def test_searches():
    db = SessionLocal()
    test_plates = [
        "MH 46 CB 0005",
        "MH46CB0005",
        "0005",
        "MH 43 CG 3824",
        "3824",
        "MH 03 BK 8453",
        "8453",
        "MH 46 BK 0500",
        "0500",
        "MH 43 BF 3945",
        "3945",
        "MH 04 KY 5983",
        "5983"
    ]

    print("=================================================================")
    print("  VERIFYING SEARCH BY LICENSE PLATE FOR ALL NEW VEHICLES")
    print("=================================================================\n")

    all_passed = True
    for query in test_plates:
        res = search_vehicles(db, plate_number=query)
        matches = res.get("matches", []) or res.get("items", [])
        if matches:
            top = matches[0]
            print(f"✓ Search '{query}' -> Found {len(matches)} result(s) | Top Match: {top['plate_number']} ({top['vehicle_model']}) - Snapshot: {top['snapshot']}")
        else:
            print(f"✗ Search '{query}' -> NO RESULTS FOUND!")
            all_passed = False

    db.close()
    if all_passed:
        print("\n🎉 ALL LICENSE PLATE SEARCH TESTS PASSED 100% SUCCESSFULLY!")

if __name__ == "__main__":
    test_searches()
