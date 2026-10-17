import time
from datetime import datetime

class EnergyMonitor:
    def __init__(self, config):
        self.config = config
        self.occupied = False
        self.lights_on = False
        self.fan_spinning = False
        self.total_waste_kwh = 0.0
        self.session_start = datetime.now()

        self.light_watt = config.get("power_per_light_watt", 36)
        self.fan_watt = config.get("power_per_fan_watt", 70) # Added fan
        self.ac_watt = config.get("power_per_ac_watt", 1500)
        self.rate = config.get("electricity_rate", 8.5)

    def update(self, person_count, lights_on, fan_spinning):
        # Waste is calculated if room is empty AND something is ON
        wasting_now = (person_count == 0) and (lights_on or fan_spinning)

        if wasting_now:
            # Calculate wattage based on what is actually running
            current_watt = 0
            if lights_on: current_watt += self.light_watt
            if fan_spinning: current_watt += self.fan_watt
            # Note: We don't add AC here unless you have a way to detect it.
            
            kwh = (current_watt / 1000.0) / 3600.0
            self.total_waste_kwh += kwh

        self.occupied = (person_count > 0)
        self.lights_on = lights_on
        self.fan_spinning = fan_spinning

    def get_stats(self):
        return {
            "total_waste_kwh": round(self.total_waste_kwh, 6),
            "total_waste_rupees": round(self.total_waste_kwh * self.rate, 4),
            "session_start": self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
            "currently_occupied": self.occupied,
            "lights_on": self.lights_on,
            "fan_spinning": self.fan_spinning
        }