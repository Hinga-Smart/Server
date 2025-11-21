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

# ----- Swagger/OpenAPI -----
OPENAPI_DOC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Smart Irrigation API",
        "version": "1.0.1",
        "description": "API documentation for moisture monitoring + sensor management with Try-It-Out support."
    },
    "paths": {
        "/sensor/add": {
            "post": {
                "summary": "Add a new sensor",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "sensor_id": {"type": "integer", "example": 1},
                                    "sensor_name": {"type": "string", "example": "Garden Sensor"},
                                    "location": {"type": "string", "example": "Backyard"}
                                },
                                "required": ["sensor_id", "sensor_name"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Sensor added"}}
            }
        },
        "/sensor/update/{sensor_id}": {
            "put": {
                "summary": "Update sensor details",
                "parameters": [
                    {"name": "sensor_id", "in": "path", "required": True, "schema": {"type": "integer"}}
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "sensor_name": {"type": "string", "example": "Updated Sensor"},
                                    "location": {"type": "string", "example": "Front Yard"},
                                    "active": {"type": "boolean", "example": True}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Sensor updated"}}
            }
        },
        "/sensors": {
            "get": {
                "summary": "Get all sensors",
                "responses": {"200": {"description": "List of sensors"}}
            }
        },
        "/data": {
            "post": {
                "summary": "Submit moisture reading",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "sensor_id": {"type": "integer", "example": 1},
                                    "moisture": {"type": "integer", "example": 450}
                                },
                                "required": ["sensor_id", "moisture"]
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Reading recorded"}}
            }
        },
        "/latest": {
            "get": {
                "summary": "Get latest moisture reading",
                "parameters": [
                    {"name": "sensor_id", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "Latest reading"}}
            }
        },
        "/all": {
            "get": {
                "summary": "Get all moisture readings",
                "parameters": [
                    {"name": "sensor_id", "in": "query", "required": False, "schema": {"type": "integer"}}
                ],
                "responses": {"200": {"description": "All readings"}}
            }
        }
    }
}


@app.route("/")
def swagger_ui():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Irrigation API Docs</title>
        <link rel="stylesheet"
              href="https://unpkg.com/swagger-ui-dist/swagger-ui.css">
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({
                url: '/openapi.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.SwaggerUIStandalonePreset
                ],
                layout: "BaseLayout"
            });
        </script>
    </body>
    </html>
    """


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