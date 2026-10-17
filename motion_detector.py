import cv2
import numpy as np

class MotionDetector:
    def __init__(self, config):
        # Defaults to the full screen (640x480) if not specified in settings
        self.roi = config.get("fan_roi", {"x": 0, "y": 0, "w": 640, "h": 480})
        self.prev_gray = None
        self.motion_threshold = 15
        self.fan_is_spinning = False

    def analyze(self, frame):
        x, y, w, h = self.roi["x"], self.roi["y"], self.roi["w"], self.roi["h"]
        h_img, w_img = frame.shape[:2]
        
        # Clamp to screen edges
        x2, y2 = min(x + w, w_img), min(y + h, h_img)
        
        roi_frame = frame[y:y2, x:x2]
        if roi_frame.size == 0:
            return self.fan_is_spinning

        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if self.prev_gray is None:
            self.prev_gray = gray
            return self.fan_is_spinning

        frame_delta = cv2.absdiff(self.prev_gray, gray)
        thresh = cv2.threshold(frame_delta, self.motion_threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Ignore the bottom half of the screen (where people usually sit)
        # This prevents you from triggering the fan sensor by moving your head.
        thresh[int(thresh.shape[0]*0.6):, :] = 0
        
        motion_score = np.sum(thresh) / 255.0
        
        # If there are moving pixels (the spinning fan), trigger it
        if motion_score > 1500: 
            self.fan_is_spinning = True
        elif motion_score < 500:
            self.fan_is_spinning = False

        self.prev_gray = gray
        return self.fan_is_spinning