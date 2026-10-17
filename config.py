import json
import os

DEFAULT_SETTINGS = {
    "camera_source": 0,
    "confidence_threshold": 0.5,
    "frame_width": 640,
    "frame_height": 480,
    "target_fps": 30,
    "roi": {"x": 100, "y": 50, "w": 440, "h": 380},
    "electricity_rate": 8.5,
    "power_per_light_watt": 36,
    "power_per_ac_watt": 1500,
    "alert_latency_seconds": 30,
    "alert_email": "",
    "whatsapp_enabled": False,
    "light_on_threshold": 90,
    "light_off_threshold": 60
}

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return json.load(f)
    save_settings(DEFAULT_SETTINGS)
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)