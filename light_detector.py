import cv2
import numpy as np

class LightDetector:
    def __init__(self, config):
        self.on_threshold = config.get("light_on_threshold", 90)
        self.off_threshold = config.get("light_off_threshold", 60)
        self.roi = config.get("roi", {"x": 100, "y": 50, "w": 440, "h": 380})
        self.last_state = False
        self.prev_brightness = None

    def analyze(self, frame):
        x, y, w, h = self.roi["x"], self.roi["y"], self.roi["w"], self.roi["h"]
        h_img, w_img = frame.shape[:2]
        
        x2, y2 = min(x + w, w_img), min(y + h, h_img)
        if x2 <= x or y2 <= y:
            return self.last_state, 0.0

        roi = frame[y:y2, x:x2]
        if roi.size == 0:
            return self.last_state, 0.0

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        mean_v = float(np.mean(hsv[:, :, 2]))

        # If sunlight is pouring in, we don't want to false trigger.
        # We check if the brightness changed SUDDENLY compared to last frame.
        if self.prev_brightness is not None:
            diff = mean_v - self.prev_brightness
            # A sudden jump of +20 means a light switch was flipped ON
            if diff > 20:
                self.last_state = True
            # A sudden drop of -20 means a light switch was flipped OFF
            elif diff < -20:
                self.last_state = False
            # Otherwise, use the absolute thresholds as a fallback
            elif mean_v >= self.on_threshold:
                self.last_state = True
            elif mean_v <= self.off_threshold:
                self.last_state = False
        
        self.prev_brightness = mean_v
        return self.last_state, round(mean_v, 2)