import sys
import socket
import urllib.request

def check_ip(ip_str):
    url = ip_str.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "http://" + url
    if not url.endswith("/video"):
        if url.endswith("/videos"):
            url = url[:-7] + "/video"
        elif url.endswith("/"):
            url = url + "video"
        elif url.count("/") == 2:
            url = url + "/video"

    print(f"Testing connectivity to: {url}")

    # Extract host and port
    from urllib.parse import urlparse
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 8080

    print(f"1. Testing TCP Socket ({host}:{port})...")
    s = socket.socket()
    s.settimeout(3.0)
    try:
        err = s.connect_ex((host, port))
        if err == 0:
            print("   ✓ TCP Port is OPEN and REACHABLE!")
        else:
            print(f"   ✗ Connection failed (error code {err}).")
            print("     -> The phone is unreachable from your computer on this IP.")
            print("     -> Cause A: The phone's IP address has changed in the app.")
            print("     -> Cause B: The WiFi router blocks device-to-device communication (AP Isolation).")
            print("     -> SOLUTION: Turn on 'Personal Hotspot' on your phone and connect your Mac to it!")
            return False
    except Exception as e:
        print(f"   ✗ Socket error: {e}")
        return False
    finally:
        s.close()

    print(f"2. Testing HTTP MJPEG Stream ({url})...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'VigrahAI-Test'})
        res = urllib.request.urlopen(req, timeout=3.0)
        print(f"   ✓ HTTP Status: {res.status} OK! Stream is ACTIVE!")
        chunk = res.read(1024)
        print(f"   ✓ Received {len(chunk)} bytes of video data successfully!")
        return True
    except Exception as e:
        print(f"   ✗ HTTP request failed: {e}")
        return False

if __name__ == "__main__":
    test_target = sys.argv[1] if len(sys.argv) > 1 else "http://10.49.119.32:8080"
    check_ip(test_target)
