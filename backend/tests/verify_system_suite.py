import os, sys
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import urllib.request
import json
import sys

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

endpoints = [
    ('/api/status', 'System Telemetry & Health'),
    ('/api/cameras', 'Surveillance Camera Channels'),
    ('/api/events?limit=5', 'Live Detected Threat Events'),
    ('/api/vehicle/search?plate=MH', 'Vehicle Search Engine'),
    ('/api/events/1/reconstruction', 'Event Reconstruction (Event #1)'),
    ('/api/events/TEST-EVT-001/reconstruction', 'Event Reconstruction (TEST-EVT-001)')
]

print('=' * 75)
print('SYSTEM HEALTH & BACKEND API VERIFICATION')
print('=' * 75)

all_passed = True
for ep, name in endpoints:
    try:
        url = f'http://localhost:8000{ep}'
        req = urllib.request.urlopen(url, timeout=5)
        status = req.getcode()
        data = json.loads(req.read().decode())
        count = len(data) if isinstance(data, list) else (len(data.get('matches', [])) if 'matches' in data else 'OK')
        print(f'✅ [PASS] {status} OK | {name:<36} | {ep} (Result: {count})')
    except Exception as e:
        print(f'❌ [FAIL] | {name:<36} | {ep} -> Error: {e}')
        all_passed = False

print('=' * 75)
if all_passed:
    print('🎉 ALL BACKEND API ENDPOINTS ARE 100% OPERATIONAL & VERIFIED!')
else:
    print('⚠️ SOME BACKEND APIS RETURNED ERRORS')
print('=' * 75)
