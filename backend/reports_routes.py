from flask import Blueprint, jsonify
from db import get_db_connection

reports_bp = Blueprint("reports_bp", __name__)

# ---------------------------------------------------------
# 1) VERIFIED BILLS
# ---------------------------------------------------------
@reports_bp.get("/api/verified-bills")
def get_verified_bills():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                b.bill_no,
                b.farmer_id,
                b.trader_id,
                b.vehicle_no,
                b.manual_bag_count,
                b.status,
                b.created_at AS verified_at,

                r.ai_bag_count,
                r.difference

            FROM bills b
            LEFT JOIN reconciliation r ON r.bill_id = b.id
            where b.status = 'VERIFIED'
            ORDER BY b.created_at DESC
            LIMIT 1000
        """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"status": "success", "bills": rows})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500



# ---------------------------------------------------------
# 2) FRAUD ALERTS
# ---------------------------------------------------------
@reports_bp.get("/api/fraud-alerts")
def get_fraud_alerts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                b.bill_no,
                b.vehicle_no,
                r.manual_bag_count,
                r.ai_bag_count,
                r.difference,
                f.severity,
                f.message,
                f.created_at AS alert_time
            FROM fraud_alerts f
            JOIN bills b ON b.id = f.bill_id
            JOIN reconciliation r ON r.bill_id = b.id AND r.batch_id = f.batch_id
            ORDER BY f.created_at DESC
            LIMIT 500
        """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "alerts": rows
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ---------------------------------------------------------
# 3) ALL RECORDS
# ---------------------------------------------------------
@reports_bp.get("/api/all-records")
def get_all_records():
    """
    Shows a combined view:
    - bills
    - latest reconciliation if exists
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                b.bill_no,
                b.farmer_id,
                b.trader_id,
                b.vehicle_no,
                b.manual_bag_count,
                b.status,
                b.created_at AS updated_at,

                r.ai_bag_count,
                r.difference

            FROM bills b
            LEFT JOIN reconciliation r ON r.bill_id = b.id
            ORDER BY b.created_at DESC
            LIMIT 1000
        """)

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "records": rows
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
