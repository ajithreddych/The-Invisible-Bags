from flask import Blueprint, request, jsonify
from db import get_db_connection
from utils import is_empty
import mysql.connector

bills_bp = Blueprint("bills_bp", __name__)

# -------------------------
# POST: Register a Bill
# -------------------------
@bills_bp.post("/api/bills")
def create_bill():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "No JSON body provided"}), 400

        bill_no = data.get("bill_no")
        bill_date = data.get("bill_date")
        farmer_id = data.get("farmer_id")
        trader_id = data.get("trader_id")
        mill_id = data.get("mill_id")
        vehicle_no = data.get("vehicle_no")
        manual_bag_count = data.get("manual_bag_count")
        manual_total_weight = data.get("manual_total_weight")
        net_weight_per_bag = data.get("net_weight_per_bag")

        # ---- validation ----
        required_fields = {
            "bill_no": bill_no,
            "bill_date": bill_date,
            "farmer_id": farmer_id,
            "trader_id": trader_id,
            "mill_id": mill_id,
            "vehicle_no": vehicle_no,
            "manual_bag_count": manual_bag_count,
            "manual_total_weight": manual_total_weight,
            "net_weight_per_bag": net_weight_per_bag,
        }

        for key, val in required_fields.items():
            if is_empty(val):
                return jsonify({"status": "error", "message": f"{key} is required"}), 400

        # number validation
        try:
            manual_bag_count = int(manual_bag_count)
            manual_total_weight = float(manual_total_weight)
            net_weight_per_bag = float(net_weight_per_bag)
        except:
            return jsonify({"status": "error", "message": "Bag count and weights must be numbers"}), 400

        if manual_bag_count <= 0 or manual_total_weight <= 0 or net_weight_per_bag <= 0:
            return jsonify({"status": "error", "message": "Bag count and weights must be > 0"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # insert bill
        query = """
            INSERT INTO bills
            (bill_no, farmer_id, trader_id, mill_id, vehicle_no, bill_date,
             manual_bag_count, manual_total_weight, net_weight_per_bag, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'PENDING')
        """

        values = (
            bill_no,
            farmer_id,
            trader_id,
            mill_id,
            vehicle_no,
            bill_date,
            manual_bag_count,
            manual_total_weight,
            net_weight_per_bag
        )

        cursor.execute(query, values)
        conn.commit()

        new_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Bill registered successfully",
            "bill_id": new_id
        }), 201

    except mysql.connector.IntegrityError:
        return jsonify({
            "status": "error",
            "message": "Bill number already exists. Use a unique bill_no."
        }), 409

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# -------------------------
# GET: List Bills
# -------------------------
@bills_bp.get("/api/bills")
def get_bills():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, bill_no, farmer_id, trader_id, mill_id, vehicle_no,
                   bill_date, manual_bag_count, manual_total_weight,
                   net_weight_per_bag, status, created_at
            FROM bills
            ORDER BY created_at DESC
        """)

        bills = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "count": len(bills),
            "bills": bills
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
