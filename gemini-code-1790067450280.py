# xai_event_monitor.py
import json
import sqlite3
from analytics_engine import DB_PATH

SAFETY_THRESHOLDS = {
    "max_soil_moisture": 75.0,  # Saturation risk / Root rot prevention
    "min_soil_moisture": 18.0,  # Critical drought threshold
    "max_canopy_temp": 42.0,    # Heat stress protection
    "min_battery_voltage": 3.4  # Edge power brownout prevention
}

def analyze_and_explain_turn_off(node_id, actuator_type, previous_state, current_state, telemetry):
    """
    Evaluates state transitions from Active (1) to Turn-Off (0)
    and generates causal attribution explanations.
    """
    # Only evaluate active-to-inactive transitions
    if previous_state == 1 and current_state == 0:
        moisture = telemetry.get("soil_moisture_pct", 0)
        temp = telemetry.get("ambient_temp_c", 0)
        voltage = telemetry.get("battery_voltage", 4.0)
        flow_rate = telemetry.get("water_flow_rate_lpm", 0.0)

        trigger_cause = "Normal Schedule"
        explanation = f"{actuator_type} deactivated according to preset operational cycles."

        # Causal Rule 1: Soil Saturation Protection
        if moisture >= SAFETY_THRESHOLDS["max_soil_moisture"]:
            trigger_cause = "Soil Moisture Saturation"
            explanation = (
                f"Automated turn-off executed for {actuator_type}. Soil moisture hit {moisture:.1f}% "
                f"(threshold: {SAFETY_THRESHOLDS['max_soil_moisture']}%). Shutting down prevents "
                "leaching, anaerobic root rot, and fertilizer runoff."
            )
        # Causal Rule 2: Dry Run / Pipe Pressure Drop
        elif flow_rate < 0.5 and actuator_type in ["main_pump", "irrigation_valve"]:
            trigger_cause = "Zero-Flow / Dry Run Protection"
            explanation = (
                f"Emergency shutoff triggered for {actuator_type}. Zero water flow detected during "
                "active duty cycle. The system shut off to prevent motor cavitation and overheating."
            )
        # Causal Rule 3: Node Brownout Sleep Protection
        elif voltage <= SAFETY_THRESHOLDS["min_battery_voltage"]:
            trigger_cause = "Low Battery Voltage Protection"
            explanation = (
                f"System shutdown activated. Battery voltage dropped to {voltage:.2f}V "
                f"(cutoff: {SAFETY_THRESHOLDS['min_battery_voltage']}V). Actuators disabled to safeguard "
                "telemetry retention and prevent deep discharge."
            )

        # Log event for analytics
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                """
                INSERT INTO turn_off_events (node_id, actuator_type, trigger_cause, telemetry_snapshot, explanation)
                VALUES (?, ?, ?, ?, ?)
                """,
                (node_id, actuator_type, trigger_cause, json.dumps(telemetry), explanation)
            )

        return {
            "turn_off_detected": True,
            "trigger_cause": trigger_cause,
            "explanation": explanation
        }

    return {"turn_off_detected": False}