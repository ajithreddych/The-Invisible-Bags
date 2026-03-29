from flask import Flask, jsonify
from flask_cors import CORS
from db import get_db_connection

from bills_routes import bills_bp
from ai_routes import ai_bp
from reports_routes import reports_bp   # ✅ NEW

app = Flask(__name__)
CORS(app)

# register blueprints
app.register_blueprint(bills_bp)
app.register_blueprint(ai_bp)
app.register_blueprint(reports_bp)      # ✅ NEW

@app.get("/")
def home():
    return jsonify({"message": "Rice Mill AI Backend Running ✅"})

@app.get("/api/test-db")
def test_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "tables": [t[0] for t in tables]
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


if __name__ == "__main__":
    app.run(debug=False, port=5000)
