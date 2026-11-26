from dataclasses import dataclass, asdict
from typing import Any

@dataclass
class Telemetry:
    timestamp: str
    location: str
    altitude_m: float
    latitude: float
    longitude: float

@dataclass
class FrameEvent:
    frame_id: str
    telemetry: Telemetry
    description: str
    objects: list[str]
    dwell_minutes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "frame_id": self.frame_id,
            "timestamp": self.telemetry.timestamp,
            "location": self.telemetry.location,
            "altitude_m": self.telemetry.altitude_m,
            "latitude": self.telemetry.latitude,
            "longitude": self.telemetry.longitude,
            "description": self.description,
            "objects": self.objects,
            "dwell_minutes": self.dwell_minutes,
        }
