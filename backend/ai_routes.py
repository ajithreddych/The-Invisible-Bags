from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

from db import get_db_connection
from ai_counter import count_unique_bags_from_video

ai_bp = Blueprint("ai_bp", __name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@ai_bp.post("/api/ai/verify")
def ai_verify_bill():
    try:
        # --- bill_id from form-data ---
        bill_id = request.form.get("bill_id")
        if not bill_id:
            return jsonify({"status": "error", "message": "bill_id is required"}), 400

        try:
            bill_id = int(bill_id)
        except:
            return jsonify({"status": "error", "message": "bill_id must be integer"}), 400

        # --- video file ---
        if "video" not in request.files:
            return jsonify({"status": "error", "message": "video file is required"}), 400

        video = request.files["video"]
        if video.filename == "":
            return jsonify({"status": "error", "message": "video filename empty"}), 400

        filename = secure_filename(video.filename)
        unique_name = f"{uuid.uuid4()}_{filename}"
        save_path = os.path.join(UPLOAD_FOLDER, unique_name)
        video.save(save_path)

        # --- get bill details from DB ---
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM bills WHERE id=%s", (bill_id,))
        bill = cursor.fetchone()

        if not bill:
            cursor.close()
            conn.close()
            return jsonify({"status": "error", "message": "Bill not found"}), 404

        # --- run AI counting ---
        ai_bag_count = count_unique_bags_from_video(save_path)

        net_weight_per_bag = float(bill["net_weight_per_bag"])
        ai_total_weight = ai_bag_count * net_weight_per_bag

        manual_bag_count = int(bill["manual_bag_count"])
        difference = manual_bag_count - ai_bag_count

        result = "MATCH" if difference == 0 else "MISMATCH"
        new_status = "VERIFIED" if difference == 0 else "MISMATCH"

        # --- create batch_id ---
        batch_id = f"BATCH_{bill_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # --- insert ai_batches ---
        cursor.execute("""
            INSERT INTO ai_batches
            (batch_id, mill_id, gate_id, vehicle_no, entry_time, ai_bag_count, ai_est_weight, video_path)
            VALUES (%s, %s, %s, %s, NOW(), %s, %s, %s)
        """, (
            batch_id,
            bill["mill_id"],
            "GATE_1",
            bill["vehicle_no"],
            ai_bag_count,
            ai_total_weight,
            save_path
        ))

        # --- insert reconciliation ---
        cursor.execute("""
            INSERT INTO reconciliation
            (bill_id, batch_id, manual_bag_count, ai_bag_count, difference, result)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            bill_id,
            batch_id,
            manual_bag_count,
            ai_bag_count,
            difference,
            result
        ))

        # --- update bill status ---
        cursor.execute("""
            UPDATE bills
            SET status=%s
            WHERE id=%s
        """, (new_status, bill_id))

        # --- if mismatch create fraud alert ---
        if result == "MISMATCH":
            severity = "HIGH" if abs(difference) >= 5 else "MEDIUM"

            msg = (
                f"Mismatch detected for Bill {bill['bill_no']}. "
                f"Manual={manual_bag_count}, AI={ai_bag_count}, Diff={difference}"
            )

            cursor.execute("""
                INSERT INTO fraud_alerts
                (bill_id, batch_id, severity, message)
                VALUES (%s, %s, %s, %s)
            """, (
                bill_id,
                batch_id,
                severity,
                msg
            ))

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "AI verification completed",
            "bill_id": bill_id,
            "bill_no": bill["bill_no"],
            "ai_bag_count": ai_bag_count,
            "ai_total_weight": round(ai_total_weight, 2),
            "manual_bag_count": manual_bag_count,
            "manual_total_weight": float(bill["manual_total_weight"]),
            "difference": difference,
            "result": result,
            "new_status": new_status,
            "batch_id": batch_id
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
