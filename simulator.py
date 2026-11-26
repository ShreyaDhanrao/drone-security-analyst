from .models import FrameEvent, Telemetry

def demo_events() -> list[FrameEvent]:
    """Reproducible synthetic scenario spanning midnight and daytime."""
    raw = [
        ("F001", "2026-11-26T00:01:00", "Main Gate", 18, 19.0760, 72.8777,
         "A person is standing near the main gate for 12 minutes.", ["person"], 12),
        ("F002", "2026-11-26T08:30:00", "Parking Area", 22, 19.0762, 72.8779,
         "A delivery van is parked in the parking area.", ["van", "vehicle"], 0),
        ("F003", "2026-11-26T12:00:00", "Garage", 20, 19.0764, 72.8780,
         "A blue Ford F150 pickup truck enters the garage.", ["blue ford f150", "truck", "vehicle"], 0),
        ("F004", "2026-11-26T14:00:00", "Main Gate", 21, 19.0760, 72.8777,
         "The same blue Ford F150 pickup truck enters through the main gate again.", ["blue ford f150", "truck", "vehicle"], 0),
        ("F005", "2026-11-26T18:45:00", "Boundary Wall", 25, 19.0765, 72.8782,
         "A person walks along the boundary wall and exits the camera view.", ["person"], 0),
        ("F006", "2026-11-26T22:10:00", "Main Gate", 19, 19.0760, 72.8777,
         "A security guard patrols the main gate.", ["person", "security guard"], 0),
    ]
    events = []
    for fid, ts, loc, alt, lat, lon, desc, objects, dwell in raw:
        telemetry = Telemetry(ts, loc, float(alt), float(lat), float(lon))
        events.append(FrameEvent(fid, telemetry, desc, objects, dwell))
    return events
