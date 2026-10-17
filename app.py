from flask import Flask, render_template, Response, jsonify, request
import threading
import time
import cv2
import numpy as np

from config import load_settings, save_settings
from motion_detector import MotionDetector
from light_detector import LightDetector
from detector import PersonDetector
from energy_monitor import EnergyMonitor
from alert_system import AlertSystem
from data_logger import init_csvs, log_occupancy, log_energy
from ml_analytics import run_all_analytics

app = Flask(__name__)

settings = load_settings()
init_csvs()

detector = PersonDetector(settings)
energy = EnergyMonitor(settings)
motion_detector = MotionDetector(settings)
light_detector = LightDetector(settings)
alert_system = AlertSystem(settings)


def processing_loop():
    detector.start_camera(settings["camera_source"])
    last_log_time = 0
    
    while True:
        if detector.cap is None or not detector.cap.isOpened():
            time.sleep(1)
            continue
            
        ret, frame = detector.cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        frame = cv2.resize(frame,
                           (settings["frame_width"], settings["frame_height"]))

        # 1) Person detection
        annotated, count = detector.detect_frame(frame)

        # 2) Light status
        lights_on, mean_brightness = light_detector.analyze(frame)

        # 3) Fan motion detection
        fan_spinning = motion_detector.analyze(frame)

        # 4) Draw light status on frame
        status_text = f"Lights: {'ON' if lights_on else 'OFF'} ({mean_brightness})"
        color = (0, 255, 0) if lights_on else (0, 0, 255)
        cv2.putText(annotated, status_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

                # 5) Draw Fan motion status text on the top right
        fan_color = (0, 255, 255) if fan_spinning else (128, 128, 128)
        fan_text = "Fan: SPINNING" if fan_spinning else "Fan: OFF"
        cv2.putText(annotated, fan_text, (450, 30), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, fan_color, 2)

        with detector.lock:
            detector.current_frame = annotated

        # 6) Energy and Alerts
        energy.update(count, lights_on, fan_spinning)
        alert_system.update(count, lights_on, fan_spinning)

        # 7) Log to CSV (Only log once every 5 seconds to keep ML data clean)
        current_time = time.time()
        if current_time - last_log_time >= 5.0:
            log_occupancy(count, lights_on, mean_brightness)
            stats = energy.get_stats()
            log_energy(stats["total_waste_kwh"], stats["total_waste_rupees"])
            last_log_time = current_time

        # Limit loop to target FPS
        time.sleep(1.0 / settings["target_fps"])


# Start background thread
threading.Thread(target=processing_loop, daemon=True).start()


@app.route("/")
def index():
    return render_template("index.html")


def gen_frames():
    while True:
        frame = detector.get_frame()
        if frame is None:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(frame, "Waiting for camera...", (150, 240), 
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

        ok, buf = cv2.imencode(".jpg", frame)
        if not ok:
            continue
            
        frame_bytes = buf.tobytes()
        
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n"
               b"Content-Length: " + str(len(frame_bytes)).encode() + b"\r\n\r\n"
               + frame_bytes + b"\r\n")
               
        time.sleep(0.05)  # Cap stream at ~20 FPS


@app.route("/video_feed")
def video_feed():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame",
                    headers={"Cache-Control": "no-cache, no-store, must-revalidate",
                             "Pragma": "no-cache",
                             "Expires": "0"})


@app.route("/status")
def status():
    return jsonify({
        "person_count": detector.get_count(),
        "energy": energy.get_stats()
    })


@app.route("/analytics")
def analytics():
    return render_template("analytics.html")


@app.route("/api/analytics")
def api_analytics():
    return jsonify(run_all_analytics())


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    global settings
    if request.method == "POST":
        data = request.get_json() or {}
        settings.update(data)
        save_settings(settings)
        return jsonify({"status": "ok", "settings": settings})
    return jsonify(settings)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)