import cv2
import requests
import base64
import math
import time

# ---------------------------
# CONFIG
# ---------------------------
API_KEY = "DoBw7BmlswzkYMd3n9Ti"
WORKSPACE = "ajith-reddy"
WORKFLOW_ID = "find-bags-3"

VIDEO_PATH = "IMG_6929.MP4"   # keep video in same folder as this file

FRAME_SKIP = 10              # process every 10th frame (reduce API calls)
DIST_THRESHOLD = 80          # matching distance for tracking
SHOW_VIDEO = False           # change to True if you want to see live output

URL = f"https://serverless.roboflow.com/{WORKSPACE}/workflows/{WORKFLOW_ID}"

# ---------------------------
# HELPERS
# ---------------------------

def extract_predictions(data):
    """
    Robustly extract predictions list from Roboflow workflow response.
    Returns a list of prediction dicts.
    """

    # Most workflows:
    # data["outputs"][0]["predictions"] -> list
    outputs = data.get("outputs", [])
    if outputs and isinstance(outputs, list):
        out0 = outputs[0]

        # case 1: predictions is list
        if "predictions" in out0 and isinstance(out0["predictions"], list):
            return out0["predictions"]

        # case 2: predictions is dict containing "predictions"
        if "predictions" in out0 and isinstance(out0["predictions"], dict):
            if "predictions" in out0["predictions"]:
                return out0["predictions"]["predictions"]

        # case 3: sometimes called "output"
        if "output" in out0 and isinstance(out0["output"], list):
            return out0["output"]

    # fallback:
    if "predictions" in data:
        if isinstance(data["predictions"], list):
            return data["predictions"]
        if isinstance(data["predictions"], dict) and "predictions" in data["predictions"]:
            return data["predictions"]["predictions"]

    return []


def pred_to_box(pred):
    """
    Convert prediction dict to (x1, y1, x2, y2).
    Supports both:
    - x,y,width,height
    - x1,y1,x2,y2
    """

    # Format A: center-based
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

    # Format B: corner-based
    if all(k in pred for k in ["x1", "y1", "x2", "y2"]):
        return int(pred["x1"]), int(pred["y1"]), int(pred["x2"]), int(pred["y2"])

    return None


def box_center(box):
    x1, y1, x2, y2 = box
    cx = int((x1 + x2) / 2)
    cy = int((y1 + y2) / 2)
    return cx, cy


# ---------------------------
# MAIN
# ---------------------------

cap = cv2.VideoCapture(VIDEO_PATH)

if not cap.isOpened():
    print(f"❌ ERROR: Cannot open video: {VIDEO_PATH}")
    print("👉 Keep the video in same folder as bags_count.py")
    exit()

tracked = {}     # id -> (cx, cy)
next_id = 0
unique_ids = set()

frame_count = 0

print("\n🚀 Running bag detection + unique counting...\n")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # skip frames to reduce API usage
    if frame_count % FRAME_SKIP != 0:
        continue

    # frame -> jpg -> base64
    ok, buffer = cv2.imencode(".jpg", frame)
    if not ok:
        continue

    jpg_base64 = base64.b64encode(buffer).decode("utf-8")

    payload = {
        "api_key": API_KEY,
        "inputs": {
            "image": {
                "type": "base64",
                "value": jpg_base64
            }
        }
    }

    # send request
    try:
        response = requests.post(URL, json=payload, timeout=30)
    except Exception as e:
        print("❌ Network error:", e)
        break

    if response.status_code != 200:
        print("❌ Roboflow error:", response.status_code)
        print(response.text[:400])
        break

    try:
        data = response.json()
    except Exception:
        print("❌ Response not JSON. First 400 chars:")
        print(response.text[:400])
        break

    predictions = extract_predictions(data)

    # Convert predictions -> boxes
    boxes = []
    for pred in predictions:
        if not isinstance(pred, dict):
            continue
        box = pred_to_box(pred)
        if box is None:
            continue
        boxes.append(box)

    # Convert boxes -> centers
    detections = [box_center(b) for b in boxes]

    # TRACKING (simple nearest matching)
    new_tracked = {}

    for (cx, cy) in detections:
        matched_id = None
        min_dist = 999999

        for obj_id, (px, py) in tracked.items():
            dist = math.dist((cx, cy), (px, py))
            if dist < min_dist and dist < DIST_THRESHOLD:
                min_dist = dist
                matched_id = obj_id

        # new object
        if matched_id is None:
            matched_id = next_id
            next_id += 1

        new_tracked[matched_id] = (cx, cy)
        unique_ids.add(matched_id)

    tracked = new_tracked

    print(f"Frame {frame_count}: detected={len(detections)} | total_unique={len(unique_ids)}")

    # OPTIONAL: show video
    if SHOW_VIDEO:
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        cv2.imshow("Bag Detection", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # small delay to avoid rate-limit
    time.sleep(0.05)

cap.release()
cv2.destroyAllWindows()

print("\n✅ FINAL UNIQUE BAG COUNT =", len(unique_ids))
