import os
from datetime import datetime

LOGS_FILE = os.path.join(os.path.dirname(__file__), '../logs.txt')

def log_action(action, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {action}"
    if details:
        log_entry += f" - {details}"
    log_entry += "\n"

    with open(LOGS_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)

def get_logs():
    if not os.path.exists(LOGS_FILE):
        return []

    with open(LOGS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return lines[::-1]

def clear_logs():
    if os.path.exists(LOGS_FILE):
        os.remove(LOGS_FILE)
