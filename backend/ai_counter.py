import cv2
import requests
import base64
import math
import time
import os

# ---------------------------
# CONFIG
# ---------------------------
API_KEY = "DoBw7BmlswzkYMd3n9Ti"
WORKSPACE = "ajith-reddy"
WORKFLOW_ID = "find-bags-3"
URL = f"https://serverless.roboflow.com/{WORKSPACE}/workflows/{WORKFLOW_ID}"

FRAME_SKIP = 10              # same as bags_count.py
DIST_THRESHOLD = 80
MAX_FRAMES = None            # ✅ process full video

# ---------------------------
# HELPERS
# ---------------------------
def extract_predictions(data):
    outputs = data.get("outputs", [])
    if outputs and isinstance(outputs, list):
        out0 = outputs[0]

        if "predictions" in out0 and isinstance(out0["predictions"], list):
            return out0["predictions"]

        if "predictions" in out0 and isinstance(out0["predictions"], dict):
            if "predictions" in out0["predictions"]:
                return out0["predictions"]["predictions"]

        if "output" in out0 and isinstance(out0["output"], list):
            return out0["output"]

    if "predictions" in data:
        if isinstance(data["predictions"], list):
            return data["predictions"]
        if isinstance(data["predictions"], dict) and "predictions" in data["predictions"]:
            return data["predictions"]["predictions"]

    return []


def pred_to_box(pred):
    if all(k in pred for k in ["x", "y", "width", "height"]):
        x = float(pred["x"])
        y = float(pred["y"])
        w = float(pred["width"])
        h = float(pred["height"])
        x1 = int(x - w / 2)
        y1 = int(y - h / 2)
        x2 = int(x + w / 2)
        y2 = int(y + h / 2)
        return x1, y1, x2, y2

    if all(k in pred for k in ["x1", "y1", "x2", "y2"]):
        return int(pred["x1"]), int(pred["y1"]), int(pred["x2"]), int(pred["y2"])

    return None


def box_center(box):
    x1, y1, x2, y2 = box
    return int((x1 + x2) / 2), int((y1 + y2) / 2)


def roboflow_request(payload, retries=5):
    for attempt in range(retries):
        try:
            response = requests.post(URL, json=payload, timeout=60)

            # retry on 500 errors
            if response.status_code >= 500:
                time.sleep(1.0)
                continue

            return response

        except Exception:
            time.sleep(1.0)

    raise Exception("Roboflow request failed after retries")


# ---------------------------
# MAIN FUNCTION
# ---------------------------
def count_unique_bags_from_video(video_path):

    if not os.path.exists(video_path):
        raise Exception(f"Video not found: {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception(f"Cannot open video: {video_path}")

    tracked = {}
    next_id = 0
    unique_ids = set()

    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # optional limit (disabled by default)
        if MAX_FRAMES and frame_count > MAX_FRAMES:
            break

        if frame_count % FRAME_SKIP != 0:
            continue

        ok, buffer = cv2.imencode(".jpg", frame)
        if not ok:
            continue

        jpg_base64 = base64.b64encode(buffer).decode("utf-8")

        payload = {
            "api_key": API_KEY,
            "inputs": {
                "image": {"type": "base64", "value": jpg_base64}
            }
        }

        response = roboflow_request(payload)

        if response.status_code != 200:
            cap.release()
            raise Exception(f"Roboflow error {response.status_code}: {response.text[:200]}")

        data = response.json()
        predictions = extract_predictions(data)

        boxes = []
        for pred in predictions:
            if not isinstance(pred, dict):
                continue
            box = pred_to_box(pred)
            if box is None:
                continue
            boxes.append(box)

        detections = [box_center(b) for b in boxes]

        new_tracked = {}

        for (cx, cy) in detections:
            matched_id = None
            min_dist = 999999

            for obj_id, (px, py) in tracked.items():
                dist = math.dist((cx, cy), (px, py))
                if dist < min_dist and dist < DIST_THRESHOLD:
                    min_dist = dist
                    matched_id = obj_id

            if matched_id is None:
                matched_id = next_id
                next_id += 1

            new_tracked[matched_id] = (cx, cy)
            unique_ids.add(matched_id)

        tracked = new_tracked

        # small delay (same style as bags_count.py)
        time.sleep(0.05)

    cap.release()
    return len(unique_ids)
