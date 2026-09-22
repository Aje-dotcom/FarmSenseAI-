# app.py
from flask import Flask, request, jsonify
from analytics_engine import init_analytics_db, record_diagnostic_event, get_dashboard_metrics, DB_PATH
from xai_event_monitor import analyze_and_explain_turn_off
import sqlite3
import json

app = Flask(__name__)
init_analytics_db()

@app.route('/api/telemetry/ingest', methods=['POST'])
def ingest_telemetry():
    payload = request.get_json(force=True)
    node_id = payload.get("node_id")
    telemetry = payload.get("telemetry", {})
    prev_pump_state = payload.get("prev_pump_state", 1)
    current_pump_state = payload.get("current_pump_state", 0)

    # 1. Log Telemetry
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO node_telemetry 
            (node_id, soil_moisture, ambient_temp, canopy_humidity, pump_state, power_status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                telemetry.get("soil_moisture_pct"),
                telemetry.get("ambient_temp_c"),
                telemetry.get("canopy_humidity_pct"),
                current_pump_state,
                payload.get("power_status", "NORMAL")
            )
        )

    # 2. Evaluate Turn-Off Events & Generate Real-Time Explanation
    turn_off_report = analyze_and_explain_turn_off(
        node_id=node_id,
        actuator_type=payload.get("actuator_name", "irrigation_valve"),
        previous_state=prev_pump_state,
        current_state=current_pump_state,
        telemetry=telemetry
    )

    return jsonify({
        "status": "success",
        "turn_off_report": turn_off_report
    })

@app.route('/api/analytics/summary', methods=['GET'])
def fetch_analytics():
    hours = request.args.get("window", default=24, type=int)
    metrics = get_dashboard_metrics(time_window_hours=hours)
    return jsonify(metrics)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)