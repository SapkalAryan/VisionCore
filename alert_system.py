import threading
import time
import winsound

class AlertSystem:
    def __init__(self, config):
        self.latency = config.get("alert_latency_seconds", 10)
        self.waste_start = None
        self.is_alarming = False
        self.running = True
        
        # Start the background beeping thread
        threading.Thread(target=self._beep_loop, daemon=True).start()

    def update(self, person_count, lights_on, fan_spinning):
        """Checks if we need to trigger the alarm."""
        wasting_now = (person_count == 0) and (lights_on or fan_spinning)
        
        if wasting_now:
            if self.waste_start is None:
                self.waste_start = time.time()
            elif (time.time() - self.waste_start) >= self.latency:
                self.is_alarming = True
        else:
            # Reset if a person enters or everything is turned off
            self.waste_start = None
            self.is_alarming = False

    def _beep_loop(self):
        """Plays a beep every second if the alarm is active."""
        while self.running:
            if self.is_alarming:
                try:
                    # Frequency: 1000Hz, Duration: 500ms
                    winsound.Beep(1000, 500) 
                except Exception as e:
                    print(f"[Audio Error] {e}")
            time.sleep(1)