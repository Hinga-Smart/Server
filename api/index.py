from flask import Flask, request, jsonify
from supabase import create_client, Client
from datetime import datetime
import os, traceback

app = Flask(__name__)

# --- Supabase Client ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Moisture thresholds
DRY_THRESHOLD = 300
WET_THRESHOLD = 700

# --- Utilities ---
def log_error(message):
    # Vercel filesystem is read-only → log to console
    print("[ERROR]", message)

def get_state(moisture):
    if moisture < DRY_THRESHOLD:
        return "DRY"
    elif moisture > WET_THRESHOLD:
        return "WET"
    else:
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

        if sensor_id is None or sensor_name is None:
            return {"status": "sensor_id and sensor_name required"}, 400

        # Check if sensor exists
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

        return {"status": "Sensor added successfully"}

    except Exception:
        log_error(traceback.format_exc())
        return {"status": "Server error"}, 500


@app.route('/sensor/update/<int:sensor_id>', methods=['PUT'])
def update_sensor(sensor_id):
    try:
        data = request.get_json(force=True)
        update_data = {k: v for k, v in data.items() if k in ["sensor_name", "location", "active"]}

        if not update_data:
            return {"status": "No valid fields to update"}, 400

        supabase.table("sensors").update(update_data).eq("sensor_id", sensor_id).execute()
        return {"status": "Sensor updated successfully"}

    except Exception:
        log_error(traceback.format_exc())
        return {"status": "Server error"}, 500


@app.route('/sensors', methods=['GET'])
def get_sensors():
    try:
        # Correct order syntax for Supabase Python client
        res = supabase.table("sensors").select("*").order("sensor_id", "asc").execute()
        return jsonify(res.data)
    except Exception:
        log_error(traceback.format_exc())
        return jsonify([])


# ---------------------------
#     MOISTURE DATA ROUTES
# ---------------------------

@app.route('/data', methods=['POST'])
def sensor_data():
    try:
        body = request.get_json(force=True)

        if "sensor_id" not in body or "moisture" not in body:
            return {"status": "sensor_id and moisture required"}, 400

        sensor_id = int(body["sensor_id"])
        moisture = int(body["moisture"])

        # Validate sensor exists & active
        sensor = supabase.table("sensors").select("*") \
            .eq("sensor_id", sensor_id).eq("active", True).execute()

        if not sensor.data:
            return {"status": "Invalid or inactive sensor_id"}, 400

        record = {
            "sensor_id": sensor_id,
            "moisture": moisture,
            "state": get_state(moisture),
            "timestamp": datetime.utcnow().isoformat()
        }

        supabase.table("moisture_records").insert(record).execute()
        return {"status": "Data recorded successfully"}

    except Exception:
        log_error(traceback.format_exc())
        return {"status": "Server error"}, 500


@app.route('/latest', methods=['GET'])
def latest_data():
    try:
        sensor_id = request.args.get("sensor_id")

        query = supabase.table("moisture_records").select("*") \
            .order("timestamp", "desc").limit(1)

        if sensor_id:
            query = query.eq("sensor_id", int(sensor_id))

        res = query.execute()
        return jsonify(res.data[0] if res.data else {})

    except Exception:
        log_error(traceback.format_exc())
        return jsonify({})


@app.route('/all', methods=['GET'])
def all_data():
    try:
        sensor_id = request.args.get("sensor_id")

        query = supabase.table("moisture_records").select("*") \
            .order("timestamp", "asc")

        if sensor_id:
            query = query.eq("sensor_id", int(sensor_id))

        res = query.execute()
        return jsonify(res.data)

    except Exception:
        log_error(traceback.format_exc())
        return jsonify([])


# --- Local Dev Only ---
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 1000))
    app.run(host="0.0.0.0", port=port)