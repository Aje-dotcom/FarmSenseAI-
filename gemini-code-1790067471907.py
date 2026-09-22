# analytics_engine.py
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

DB_PATH = "farmsense_analytics.db"

def init_analytics_db():
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # Diagnostics log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visual_diagnostics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                node_id TEXT,
                crop_type TEXT,
                disease TEXT,
                confidence REAL,
                severity TEXT
            )
        """)
        # IoT Telemetry log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS node_telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                node_id TEXT,
                soil_moisture REAL,
                soil_ph REAL,
                ambient_temp REAL,
                canopy_humidity REAL,
                pump_state INTEGER,
                power_status TEXT
            )
        """)
        # Actuator & System Turn-off Event log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS turn_off_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                node_id TEXT,
                actuator_type TEXT, -- e.g., 'irrigation_valve', 'misting_sprayer', 'main_pump'
                trigger_cause TEXT,
                telemetry_snapshot TEXT,
                explanation TEXT
            )
        """)
        conn.commit()

def record_diagnostic_event(node_id, crop_type, disease, confidence, severity="moderate"):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO visual_diagnostics (node_id, crop_type, disease, confidence, severity) VALUES (?, ?, ?, ?, ?)",
            (node_id, crop_type, disease, confidence, severity)
        )

def get_dashboard_metrics(time_window_hours=24):
    with sqlite3.connect(DB_PATH) as conn:
        since = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        # Disease incidence breakdown
        disease_df = pd.read_sql_query(
            "SELECT disease, COUNT(*) as count FROM visual_diagnostics WHERE timestamp >= ? GROUP BY disease ORDER BY count DESC",
            conn, params=(since,)
        )
        
        # Telemetry averages
        telemetry_df = pd.read_sql_query(
            "SELECT AVG(soil_moisture) as avg_moisture, AVG(ambient_temp) as avg_temp, AVG(canopy_humidity) as avg_humidity FROM node_telemetry WHERE timestamp >= ?",
            conn, params=(since,)
        )
        
        # Recent turn-off events
        turn_offs_df = pd.read_sql_query(
            "SELECT timestamp, node_id, actuator_type, trigger_cause, explanation FROM turn_off_events ORDER BY id DESC LIMIT 5",
            conn
        )
        
    return {
        "disease_distribution": disease_df.to_dict(orient="records"),
        "environmental_summary": telemetry_df.to_dict(orient="records")[0] if not telemetry_df.empty else {},
        "recent_turn_off_events": turn_offs_df.to_dict(orient="records")
    }