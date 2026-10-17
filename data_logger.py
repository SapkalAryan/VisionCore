import csv
import os
from datetime import datetime

OCCUPANCY_CSV = "data/occupancy_log.csv"
ENERGY_CSV = "data/energy_audit.csv"


def init_csvs():
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(OCCUPANCY_CSV):
        with open(OCCUPANCY_CSV, "w", newline="") as f:
            csv.writer(f).writerow([
                "timestamp", "person_count", "hour", "weekday",
                "occupied", "lights_on", "brightness"
            ])

    if not os.path.exists(ENERGY_CSV):
        with open(ENERGY_CSV, "w", newline="") as f:
            csv.writer(f).writerow(["timestamp", "waste_kwh", "waste_rupees"])


def log_occupancy(person_count, lights_on=None, brightness=None):
    now = datetime.now()
    with open(OCCUPANCY_CSV, "a", newline="") as f:
        csv.writer(f).writerow([
            now.strftime("%Y-%m-%d %H:%M:%S"),
            person_count,
            now.hour,
            now.weekday(),
            1 if person_count > 0 else 0,
            1 if lights_on else 0,
            brightness if brightness is not None else 0
        ])


def log_energy(waste_kwh, waste_rupees):
    with open(ENERGY_CSV, "a", newline="") as f:
        csv.writer(f).writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            round(waste_kwh, 6),
            round(waste_rupees, 4)
        ])