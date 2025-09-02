import json
import time
import requests
from datetime import datetime

# ===============================
# qBittorrent Queue Helper (Console Version)
# ===============================

CONFIG_FILE = "config.json"
LOOP_INTERVAL = 10 * 60  # seconds

# -------------------------------
# Load or ask for port
# -------------------------------
try:
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)
except FileNotFoundError:
    config = {}

if "port" not in config:
    port = input("Enter qBittorrent port: ")
    config["port"] = port
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)
else:
    port = config["port"]

print(f"Using qBittorrent port: {port}")
BASE_URL = f"http://localhost:{port}/api/v2"

# -------------------------------
# Helper functions
# -------------------------------
def timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def api_get(endpoint):
    try:
        r = requests.get(f"{BASE_URL}{endpoint}")
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        print(f"[{timestamp()}] API GET Error: {e}")
        return None

def api_post(endpoint, data):
    try:
        r = requests.post(f"{BASE_URL}{endpoint}", data=data)
        r.raise_for_status()
        return r.json() if r.content else None
    except requests.exceptions.RequestException as e:
        print(f"[{timestamp()}] API POST Error: {e}")
        return None

def get_torrents():
    return api_get("/torrents/info") or []

def get_app_preferences():
    prefs = api_get("/app/preferences")
    return prefs or {}

# -------------------------------
# Warm-up: start all non-completed torrents briefly
# -------------------------------
def warmup_torrents(torrents):
    for t in torrents:
        if t['state'] != 'completed':
            api_post("/torrents/resume", {'hashes': t['hash']})
    print(f"[{timestamp()}] Warmup initiated for non-completed torrents.")
    time.sleep(10)  # short warmup

# -------------------------------
# Scoring and queue management
# -------------------------------
def manage_queue(torrents, prefs):
    resumed, paused = [], []

    max_active = prefs.get('max_active_downloads', 3)
    # Respect ratio/upload pausing
    ratio_limit_enabled = prefs.get('max_ratio_enabled', False)
    upload_limit_enabled = prefs.get('max_seeding_time_enabled', False)

    # Score: availability / (ETA+1) / (size+1)
    scored = []
    for t in torrents:
        availability = t.get('availability', 0)
        eta = t.get('eta', 0) or 999999
        size = t.get('size', 0)
        score = availability / (eta + 1) / (size + 1)
        scored.append((score, t))

    # Sort descending
    scored.sort(reverse=True, key=lambda x: x[0])

    active_count = 0
    for score, t in scored:
        hash_ = t['hash']
        name = t['name']
        state = t['state']

        # Stop torrents if completed and ratio >= 1
        if state == 'completed' and t.get('ratio', 0) >= 1.0:
            api_post("/torrents/pause", {'hashes': hash_})
            paused.append(name)
            continue

        # Manage active downloads
        if state != 'completed':
            if active_count < max_active:
                if state != 'downloading':
                    api_post("/torrents/resume", {'hashes': hash_})
                    resumed.append(name)
                active_count += 1
            else:
                if state == 'downloading':
                    api_post("/torrents/pause", {'hashes': hash_})
                    paused.append(name)

    return resumed, paused

# -------------------------------
# Main loop
# -------------------------------
iteration = 0
while True:
    iteration += 1
    ts = timestamp()
    print("\n" + "="*60)
    print(f"[{ts}] Loop {iteration} starting...")

    torrents = get_torrents()
    if not torrents:
        print(f"[{timestamp()}] No torrents found or API unreachable.")
        time.sleep(LOOP_INTERVAL)
        continue

    prefs = get_app_preferences()
    warmup_torrents(torrents)
    resumed, paused = manage_queue(torrents, prefs)

    if resumed or paused:
        print(f"[{timestamp()}] Torrents resumed: {', '.join(resumed) if resumed else 'None'}")
        print(f"[{timestamp()}] Torrents paused: {', '.join(paused) if paused else 'None'}")
    else:
        print(f"[{timestamp()}] Queue state checked: no changes necessary.")

    # Countdown timer until next loop
    print(f"[{timestamp()}] Next loop in {LOOP_INTERVAL//60} minutes.")
    for remaining in range(LOOP_INTERVAL, 0, -1):
        mins, secs = divmod(remaining, 60)
        print(f"\rNext loop in {mins:02d}:{secs:02d}", end="")
        time.sleep(1)
    print()  # newline before next loop
