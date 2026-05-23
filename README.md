# PC Intruder Guard

PC Intruder Guard known as NightWatch EDR is a personal endpoint monitoring system that runs silently in the background on your PC. Any suspicious activity someone touching the mouse, opening an application, or accessing files triggers an instant notification to your Telegram.

This project implements Host-based Monitoring and Security Automation (SOAR) concepts on a personal scale using Python and n8n.

---

## Features

- 🖱️ **Mouse & Keyboard Guard** detects input activity when PC is left unattended
- 🪟 **Active Window Tracker** monitors which apps or websites are being opened
- 📁 **File & Folder Monitor** detects file creation, deletion, modification, and moves
- 📲 **Telegram Notification** all alerts delivered to your phone via Telegram bot
-  ⚡ **n8n Automation** webhook based pipeline to process and forward alerts
- 🔒 **Guard Mode Toggle**  enable/disable monitoring by pressing F12

---

## Architecture

```text
PC (Python Script)
    │
    ├── Mouse/Keyboard Listener  (pynput)
    ├── Active Window Tracker    (pygetwindow)
    └── File System Monitor      (watchdog)
            │
            ▼ HTTP POST (JSON)
        n8n Webhook
            │
            ├── Check Event → Format Message
            └── Send Telegram Alert
                    │
                    ▼
              📱 Your Phone (Telegram)
```

---

## Tech Stack

| Component | Technology |
|---|---|
| Monitoring Script | Python 3.x |
| Input Detection | pynput |
| Window Tracking | pygetwindow |
| File Monitoring | watchdog |
| Automation | n8n (self-hosted / cloud) |
| Notification | Telegram Bot API |

---

## Setup Guide

### 1. Clone Repository

```bash
git clone https://github.com/AllMightyLethal/NightWatch-EDR.git
cd /pc-intruder-guard
```

### 2. Install Dependencies

```bash
pip install pynput requests pygetwindow watchdog
```

### 3. Create a Telegram Bot

1. Open Telegram → search `@BotFather`
2. Send `/newbot` → follow the steps → get your Bot Token
3. Search `@userinfobot` → get your Chat ID

### 4. Import n8n Workflow

1. Open your n8n instance
2. Click `+` → Import from file
3. Upload `n8n_workflow.json` from this repo
4. Open the `Send Telegram Alert` node → add your Telegram Bot Token credential
5. Enable the workflow (toggle `Active`)

### 5. Configure the Script

Open `intruder_guard.py` and edit the CONFIG section:

```python
WEBHOOK_URL      = "https://your-n8n-instance/webhook/intruder-guard"
TELEGRAM_CHAT_ID = "your_chat_id"
COOLDOWN_SECONDS = 20   # seconds between alerts
```

Set folders to monitor:

```python
MONITORED_FOLDERS = [
    os.path.expanduser("~/Desktop"),
    os.path.expanduser("~/Documents"),
    os.path.expanduser("~/Downloads"),
]
```

Add apps to ignore (won't trigger alerts):

```python
IGNORED_WINDOWS = [
    "Visual Studio Code",
    "Discord",
    "Spotify",
]
```

### 6. Run the Script

```bash
python intruder_guard.py
```

---

## Usage

| Action | Function |
|---|---|
| F12 | Toggle Guard Mode ON / OFF |
| Ctrl+C | Stop the script |

When Guard Mode is ON, all activity is monitored and alerts are sent to Telegram.

---

## Sample Telegram Notification

```text
🚨 INTRUDER ALERT!

📍 Event: window_change
🖱️ Detail: Active window: YouTube - Google Chrome
🕐 Time: 2025-05-23 14:02:13

⚠️ Someone is touching your PC!
```

---

## Concepts Applied

- Host based Intrusion Detection (HIDS)
- Security Orchestration, Automation and Response (SOAR)
- Endpoint Detection & Response (EDR) personal scale
- Event driven architecture via webhooks
- Realtime alerting pipeline

---

Built by **Wakamiya** TJKT Student | Networking & Cybersecurity Enthusiast
