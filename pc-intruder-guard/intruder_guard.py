"""
 ════════════════════════════════════════════════════════════════════════
║                     NightWatch EDR                        ║
║                       by Wakamiya                         ║
║                                                           ║
║        Monitor your PC from your phone via Telegram       ║
 ════════════════════════════════════════════════════════════════════════

SETUP:
  1. pip install pynput requests pygetwindow watchdog
  2. Fill config below (WEBHOOK_URL, telegram_chat_id)
  3. execute: python intruder_guard.py
  4. press F12 to toggle Guard Mode ON/OFF

Features on Guard Mode:
  - Active Window Tracker (detects what app/site is being opened)
  - File & Folder Monitor (detects file access, creation, deletion, moves)
"""

import requests
import time
import threading
import os
from pynput import mouse, keyboard
from datetime import datetime

import pygetwindow as gw
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# CONFIG

# n8n Webhook URL
WEBHOOK_URL = "PLACEHOLDER"

# Telegram Chat ID
TELEGRAM_CHAT_ID = "PLACEHOLDER"

# Cooldown between alerts (seconds)
COOLDOWN_SECONDS = 20

# Hotkey to toggle Guard Mode
GUARD_HOTKEY = keyboard.Key.f12

# Folders to monitor for file activity
# Add or remove paths as needed
MONITORED_FOLDERS = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
    os.path.expanduser("~/Pictures"),
    os.path.expanduser("~/Videos"),  
]

# How often to check active window (seconds)
WINDOW_CHECK_INTERVAL = 5

# Apps to always ignore in window tracker (not worth alerting)
IGNORED_WINDOWS = [
    "", #add whatever u like to add, example  "Chrome", "Discord"
    "",
    "",
    "",
]

#END CONFIG

guard_mode = False
last_alert_time = 0
last_window_title = ""
lock = threading.Lock()
file_cooldowns = {}


def log(msg):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] {msg}")


def send_alert(event_type: str, detail: str, cooldown_key: str = None):
    """Send alert to n8n webhook with optional per-key cooldown."""
    global last_alert_time

    # per key cooldown (for file/window events) or global cooldown
    if cooldown_key:
        now = time.time()
        last_t = file_cooldowns.get(cooldown_key, 0)
        if now - last_t < COOLDOWN_SECONDS:
            return
        file_cooldowns[cooldown_key] = now
    else:
        with lock:
            now = time.time()
            if now - last_alert_time < COOLDOWN_SECONDS:
                return
            last_alert_time = now

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    payload = {
        "event": event_type,
        "detail": detail,
        "timestamp": timestamp,
        "chat_id": TELEGRAM_CHAT_ID
    }

    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=5)
        if response.status_code == 200:
            log(f"[+] Alert Sent → {event_type}: {detail}")
        else:
            log(f"[!]  Alert Failed (status {response.status_code})")
    except requests.exceptions.ConnectionError:
        log("❌ Failed to connect to n8n. Check connection / webhook URL.")
    except Exception as e:
        log(f"❌ Error: {e}")


#Active Window Tracker 

def window_tracker():
    """Polls active window every WINDOW_CHECK_INTERVAL seconds."""
    global last_window_title
    log("[+] Active Window Tracker started")

    while True:
        time.sleep(WINDOW_CHECK_INTERVAL)
        if not guard_mode:
            continue

        try:
            win = gw.getActiveWindow()
            if win is None:
                continue

            title = win.title.strip()

            # Skip ignored / unchanged windows
            if title == last_window_title:
                continue
            if any(ign and ign.lower() in title.lower() for ign in IGNORED_WINDOWS):
                last_window_title = title
                continue

            last_window_title = title
            send_alert(
                "window_change",
                f"Active window: {title}",
                cooldown_key=f"win:{title}"
            )

        except Exception:
            pass


#File & Folder Monitor 

class FileEventHandler(FileSystemEventHandler):
    """Handles file system events and sends alerts."""

    def _alert(self, event_type: str, path: str):
        if not guard_mode:
            return
        filename = os.path.basename(path)
        # Skip temp/system files
        if filename.startswith(("~$", ".")) or filename.endswith(".tmp"):
            return
        send_alert(
            f"file_{event_type}",
            f"{event_type.upper()}: {path}",
            cooldown_key=f"file:{path}:{event_type}"
        )

    def on_created(self, event):
        if not event.is_directory:
            self._alert("created", event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self._alert("deleted", event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._alert("modified", event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            send_alert(
                "file_moved",
                f"MOVED: {event.src_path} → {event.dest_path}",
                cooldown_key=f"file:{event.src_path}:moved"
            )


def start_file_monitor():
    """Start watchdog observer for all monitored folders."""
    observer = Observer()
    handler = FileEventHandler()

    active_paths = []
    for folder in MONITORED_FOLDERS:
        if os.path.exists(folder):
            observer.schedule(handler, folder, recursive=True)
            active_paths.append(folder)
        else:
            log(f"[!]  Folder not found, skipping: {folder}")

    observer.start()
    log(f"[+] File Monitor started → {', '.join(active_paths)}")
    return observer


#Mouse Listeners 

def on_move(x, y):
    if guard_mode:
        send_alert("mouse_move", f"Mouse Moved to ({x}, {y})")


def on_click(x, y, button, pressed):
    if guard_mode and pressed:
        send_alert("mouse_click", f"Mouse Clicked at ({x}, {y}) button {button}")


def on_scroll(x, y, dx, dy):
    if guard_mode:
        send_alert("mouse_scroll", f"Scroll at ({x}, {y})")


#Keyboard Listeners

def on_press(key):
    global guard_mode

    #Toggle guard mode
    if key == GUARD_HOTKEY:
        guard_mode = not guard_mode
        status = "🟢 ON" if guard_mode else "🔴 OFF"
        log(f"Guard Mode {status}")
        log("─" * 40)
        return

    if guard_mode:
        send_alert("keyboard_activity", "Keyboard Pressed")


#Main 

def main():
    print("""
╔══════════════════════════════════════════╗
║             NightWatch EDR               ║
╚══════════════════════════════════════════╝
  [F12]    → Toggle Guard Mode ON / OFF
  [Ctrl+C] → Exit

  Modules: Mouse/KB | Window Tracker | File Monitor
  Guard Mode: 🔴 OFF
""")

    # Start background threads
    threading.Thread(target=window_tracker, daemon=True).start()
    file_observer = start_file_monitor()

    # Start input listeners
    mouse_listener = mouse.Listener(
        on_move=on_move,
        on_click=on_click,
        on_scroll=on_scroll
    )
    keyboard_listener = keyboard.Listener(on_press=on_press)

    mouse_listener.start()
    keyboard_listener.start()

    try:
        mouse_listener.join()
    except KeyboardInterrupt:
        log("Script Stopped. Exiting...")
        mouse_listener.stop()
        keyboard_listener.stop()
        file_observer.stop()
        file_observer.join()


if __name__ == "__main__":
    main()
