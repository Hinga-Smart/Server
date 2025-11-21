from flask import Flask, request, jsonify
from supabase import create_client, Client
from datetime import datetime
from flask_cors import CORS
import os, traceback

app = Flask(__name__)

# --- Enable CORS using frontend URL from env ---
FRONTEND_URL = os.environ.get("FRONTEND_URL", "*")  # fallback "*" if not set
CORS(app, origins=[FRONTEND_URL])

# --- Supabase Client ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Moisture thresholds
DRY_THRESHOLD = 300
WET_THRESHOLD = 700

# ----- Swagger/OpenAPI -----
OPENAPI_DOC = { ... }  # Keep your existing OpenAPI definition here

@app.route("/")
def swagger_ui():
    return """ ... """  # Keep your existing Swagger UI HTML here

@app.route("/openapi.json")
def openapi_spec():
    return jsonify(OPENAPI_DOC)

# --- Helpers ---
def log_error(message):
    print("[ERROR]", message)

def get_state(moisture):
    if moisture < DRY_THRESHOLD:
        return "DRY"
    elif moisture > WET_THRESHOLD:
        return "WET"
    return "MODERATE"

# ---------------------------
#       SENSOR ROUTES
# ---------------------------
@app.route('/sensor/add', methods=['POST'])
def add_sensor():
    try:
        data = request.get_json(force=True)
        sensor_id = data.get("sensor_id")
        sensor_name = data.get("sensor_name")
        location = data.get("location", "")

        if not sensor_id or not sensor_name:
            return {"status": "sensor_id and sensor_name required"}, 400

        exists = supabase.table("sensors").select("*").eq("sensor_id", sensor_id).execute()
        if exists.data:
            return {"status": "Sensor already exists"}, 400

        supabase.table("sensors").insert({
            "sensor_id": sensor_id,
            "sensor_name": sensor_name,
            "location": location,
            "installed_at": datetime.utcnow().isoformat(),
            "active": True
        }).execute()

        return {"status": "Sensor added"}

    except Exception:
        log_error(traceback.format_exc())
        return {"status": "Server error"}, 500

@app.route('/sensor/update/<int:sensor_id>', methods=['PUT'])
def update_sensor(sensor_id):
    try:
        data = request.get_json(force=True)
        update_data = {k: v for k, v in data.items() if k in ["sensor_name", "location", "active"]}
        supabase.table("sensors").update(update_data).eq("sensor_id", sensor_id).execute()
        return {"status": "Sensor updated"}
    except Exception:
        log_error(traceback.format_exc())
        return {"status": "Server error"}, 500

@app.route('/sensors', methods=['GET'])
def get_sensors():
    try:
        res = supabase.table("sensors").select("*").order("sensor_id", desc=False).execute()
        return jsonify(res.data)
    except Exception:
        log_error(traceback.format_exc())
        return jsonify([])

# ---------------------------
#     MOISTURE ROUTES
# ---------------------------
@app.route('/data', methods=['POST'])
def sensor_data():
    try:
        body = request.get_json(force=True)
        if "sensor_id" not in body or "moisture" not in body:
            return {"status": "sensor_id and moisture required"}, 400

        sensor_id = int(body["sensor_id"])
        moisture = int(body["moisture"])

        sensor = supabase.table("sensors").select("*").eq("sensor_id", sensor_id).eq("active", True).execute()
        if not sensor.data:
            return {"status": "Invalid or inactive sensor_id"}, 400

        rec = {
            "sensor_id": sensor_id,
            "moisture": moisture,
            "state": get_state(moisture),
            "timestamp": datetime.utcnow().isoformat()
        }
        supabase.table("moisture_records").insert(rec).execute()
        return {"status": "Data recorded"}

    except Exception:
        log_error(traceback.format_exc())
        return {"status": "Server error"}, 500

@app.route('/latest', methods=['GET'])
def latest_data():
    try:
        sid = request.args.get("sensor_id")
        q = supabase.table("moisture_records").select("*").order("timestamp", desc=True).limit(1)
        if sid:
            q = q.eq("sensor_id", int(sid))
        res = q.execute()
        return jsonify(res.data[0] if res.data else {})
    except Exception:
        log_error(traceback.format_exc())
        return jsonify({})

@app.route('/all', methods=['GET'])
def all_data():
    try:
        sid = request.args.get("sensor_id")
        q = supabase.table("moisture_records").select("*").order("timestamp", desc=False)
        if sid:
            q = q.eq("sensor_id", int(sid))
        res = q.execute()
        return jsonify(res.data)
    except Exception:
        log_error(traceback.format_exc())
        return jsonify([])

# Local dev
if __name__ == '__main__':
    app.run(debug=True)