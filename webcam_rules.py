
def evaluate_webcam_observation(description: str, objects: list[str]) -> list[dict]:
    """
    Generate review-required alerts from visible image observations.
    These are not verified threat detections.
    """
    alerts = []

    text = description.lower()
    visible_objects = {obj.lower() for obj in objects}

    if "person" in visible_objects or "person" in text or "people" in text:
        alerts.append({
            "severity": "INFO",
            "alert_type": "PERSON_OBSERVED",
            "message": (
                "A person was described in the webcam image. "
                "Human review is required."
            ),
        })

    if any(
        word in visible_objects or word in text
        for word in ("car", "truck", "vehicle", "van", "motorcycle")
    ):
        alerts.append({
            "severity": "INFO",
            "alert_type": "VEHICLE_OBSERVED",
            "message": (
                "A vehicle was described in the webcam image. "
                "Human review is required."
            ),
        })

    if "fire" in text or "smoke" in text:
        alerts.append({
            "severity": "HIGH",
            "alert_type": "POTENTIAL_FIRE_OR_SMOKE",
            "message": (
                "Moondream described possible fire or smoke. "
                "Urgent human verification is required."
            ),
        })

    return alerts
