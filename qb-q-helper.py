import requests
import time
import os
import json
from datetime import datetime

CONFIG_FILE = "config.json"
WARMUP_DURATION = 120
LOOP_INTERVAL = 600
MAX_LOG_HISTORY = 5

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

def get_port():
    config = load_config()
    if "port" in config:
        return config["port"]
    else:
        port = input("Enter qBittorrent WebUI port (e.g., 8088): ").strip()
        config["port"] = int(port)
        save_config(config)
        return config["port"]

def get_torrents(session, base_url):
    r = session.get(f"{base_url}/torrents/info")
    r.raise_for_status()
    return r.json()

def get_app_prefs(session, base_url):
    r = session.get(f"{base_url}/app/preferences")
    r.raise_for_status()
    return r.json()

def pause_torrents(session, base_url, hashes):
    if hashes:
        session.post(f"{base_url}/torrents/pause", data={"hashes": "|".join(hashes)})

def resume_torrents(session, base_url, hashes):
    if hashes:
        session.post(f"{base_url}/torrents/resume", data={"hashes": "|".join(hashes)})

def clear_console():
    os.system("cls" if os.name == "nt" else "clear")

def is_paused_like(state):
    return state in ("pausedUP", "pausedDL", "queuedDL", "queuedUP")

def print_red(msg):
    print(f"\033[91m{msg}\033[0m")

def main():
    port = get_port()
    base_url = f"http://127.0.0.1:{port}/api/v2"
    session = requests.Session()
    log_history = []

    def log(message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_history.append(f"[{timestamp}] {message}")
        if len(log_history) > MAX_LOG_HISTORY:
            log_history.pop(0)
        clear_console()
        print("\n".join(log_history))

    # --- Initial warm-up ---
    try:
        torrents = get_torrents(session, base_url)
    except Exception as e:
        print_red(f"ERROR: Could not connect to qBittorrent API ({e})")
        for remaining in range(180, 0, -1):
            time.sleep(1)
            if remaining % 30 == 0 or remaining <= 10:
                print_red(f"Exiting in {remaining} seconds...")
        exit(1)

    paused_hashes = [t["hash"] for t in torrents if is_paused_like(t["state"]) and t["progress"] < 1.0]
    if paused_hashes:
        resume_torrents(session, base_url, paused_hashes)
        log(f"Warm-up initiated: resumed {len(paused_hashes)} torrents for ETA/availability update.")
        time.sleep(WARMUP_DURATION)
        pause_torrents(session, base_url, paused_hashes)
        log("Warm-up complete: torrents paused again.")

    # --- Main loop ---
    while True:
        log("Starting new queue management cycle...")

        try:
            prefs = get_app_prefs(session, base_url)
            torrents = get_torrents(session, base_url)
        except Exception as e:
            print_red(f"ERROR: Lost connection to qBittorrent API ({e})")
            for remaining in range(180, 0, -1):
                time.sleep(1)
                if remaining % 30 == 0 or remaining <= 10:
                    print_red(f"Exiting in {remaining} seconds...")
            exit(1)

        max_active_downloads = prefs.get("max_active_downloads", 3)
        max_ratio = prefs.get("max_ratio", -1)

        # Only process if there are torrents to download
        downloading = [t for t in torrents if t["progress"] < 1.0]
        if downloading:
            # Stop torrents that meet ratio conditions
            stop_hashes = []
            for t in torrents:
                if t["progress"] >= 1.0:
                    if max_ratio != -1 and t["ratio"] >= max_ratio:
                        stop_hashes.append(t["hash"])
            pause_torrents(session, base_url, stop_hashes)
            if stop_hashes:
                log(f"Stopped {len(stop_hashes)} torrents (completed and ratio above limit).")

            # Warm-up for active queue scoring
            paused_hashes = [t["hash"] for t in torrents if is_paused_like(t["state"]) and t["progress"] < 1.0]
            resume_torrents(session, base_url, paused_hashes)
            if paused_hashes:
                log(f"Warm-up initiated: resumed {len(paused_hashes)} torrents for ETA/availability update.")
                time.sleep(WARMUP_DURATION)
                pause_torrents(session, base_url, paused_hashes)
                log("Warm-up complete: torrents paused again.")

            torrents = get_torrents(session, base_url)

            # Score torrents
            scores = []
            for t in torrents:
                if t["progress"] >= 1.0:
                    continue
                availability = t.get("availability", 0) or 0.1
                eta = t.get("eta", 10**9)
                size = t.get("size", 1)
                score = (availability / (eta + 1)) / size
                scores.append((score, t))

            scores.sort(key=lambda x: x[0], reverse=True)
            top_hashes = [t["hash"] for _, t in scores[:max_active_downloads]]
            other_hashes = [t["hash"] for _, t in scores[max_active_downloads:]]

            resume_torrents(session, base_url, top_hashes)
            pause_torrents(session, base_url, other_hashes)

            if top_hashes or other_hashes:
                log(f"Queue updated: {len(top_hashes)} torrents resumed, {len(other_hashes)} paused.")
            else:
                log("No changes made this cycle.")
        else:
            log("No torrents to download. Waiting for torrents to be added...")

        # Countdown to next cycle
        for remaining in range(LOOP_INTERVAL, 0, -1):
            time.sleep(1)
            if remaining % 60 == 0 or remaining <= 10:
                clear_console()
                print("\n".join(log_history))
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Next cycle in {remaining} seconds...")

if __name__ == "__main__":
    main()
