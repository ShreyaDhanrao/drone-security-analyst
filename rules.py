from datetime import datetime
from .models import FrameEvent

def evaluate_rules(event: FrameEvent) -> list[dict]:
    """Auditable deterministic security rules; timestamps are local property time."""
    alerts = []
    dt = datetime.fromisoformat(event.telemetry.timestamp)
    hour = dt.hour
    objects = {x.lower() for x in event.objects}

    if "person" in objects and event.telemetry.location.lower() == "main gate":
        if 0 <= hour < 5 and event.dwell_minutes >= 10:
            alerts.append({
                "severity": "HIGH",
                "alert_type": "MIDNIGHT_LOITERING",
                "message": (
                    f"Person loitering at {event.telemetry.location}, "
                    f"{dt.strftime('%H:%M')} for {event.dwell_minutes} minutes."
                ),
            })

    if event.telemetry.altitude_m < 5:
        alerts.append({
            "severity": "MEDIUM",
            "alert_type": "LOW_ALTITUDE",
            "message": f"Drone altitude unusually low ({event.telemetry.altitude_m:.1f} m) at {event.telemetry.location}.",
        })
    return alerts
