import cv2
import threading
import time
import numpy as np
from ultralytics import YOLO


class PersonDetector:
    def __init__(self, config):
        self.config = config
        self.model = YOLO("yolov8n.pt")
        self.cap = None
        self.current_frame = None
        self.person_count = 0
        self.running = False
        self.lock = threading.Lock()
        self.roi = config.get("roi", {"x": 100, "y": 50, "w": 440, "h": 380})

    def start_camera(self, source=0):
        print("[Detector] Opening camera...")
        self.cap = cv2.VideoCapture(source)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config["frame_width"])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config["frame_height"])
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        
        # Give the webcam 1.5 seconds to warm up
        time.sleep(1.5)
        
        # Create a placeholder frame so the browser isn't blank
        placeholder = np.zeros((self.config["frame_height"], self.config["frame_width"], 3), dtype=np.uint8)
        cv2.putText(placeholder, "Camera starting...", (50, 240), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        with self.lock:
            self.current_frame = placeholder
            
        self.running = True
        print("[Detector] Camera ready.")

    def detect_frame(self, frame):
        results = self.model(frame, verbose=False,
                             conf=self.config["confidence_threshold"])
        count = 0
        annotated = frame.copy()
        x, y, w, h = self.roi["x"], self.roi["y"], self.roi["w"], self.roi["h"]

        cv2.rectangle(annotated, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(annotated, "ROI", (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        for r in results:
            boxes = r.boxes
            if boxes is not None:
                for box in boxes:
                    cls = int(box.cls[0])
                    if cls == 0:  # person
                        bx1, by1, bx2, by2 = map(int, box.xyxy[0])
                        cx, cy = (bx1 + bx2) // 2, (by1 + by2) // 2
                        inside = (x < cx < x + w) and (y < cy < y + h)
                        color = (0, 255, 0) if inside else (0, 165, 255)
                        cv2.rectangle(annotated, (bx1, by1), (bx2, by2), color, 2)
                        cv2.putText(annotated, f"Person {box.conf[0]:.2f}",
                                    (bx1, by1 - 5), cv2.FONT_HERSHEY_SIMPLEX,
                                    0.5, color, 2)
                        if inside:
                            count += 1

        with self.lock:
            self.person_count = count
        return annotated, count

    def get_frame(self):
        with self.lock:
            return None if self.current_frame is None else self.current_frame.copy()

    def get_count(self):
        with self.lock:
            return self.person_count

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()