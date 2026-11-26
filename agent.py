from collections import Counter
from datetime import date
from .rules import evaluate_rules

class SecurityAnalyst:
    def __init__(self, store):
        self.store = store

    def ingest(self, events):
        for event in events:
            alerts = evaluate_rules(event)
            self.store.add_event(event, alerts)
        return len(events)

    def summary(self, day: str | None = None) -> str:
        rows = self.store.list_frames()
        if day:
            rows = [r for r in rows if r["timestamp"].startswith(day)]
        if not rows:
            return "No indexed activity found for the selected date."
        counts = Counter(obj for row in rows for obj in row["objects"])
        trucks = [r for r in rows if "truck" in r["objects"] or "blue ford f150" in r["objects"]]
        alerts = [a for a in self.store.list_alerts() if (not day or a["timestamp"].startswith(day))]
        parts = [
            f"Indexed {len(rows)} frames across {len({r['location'] for r in rows})} locations.",
            f"Detected objects: {', '.join(f'{k} ({v})' for k, v in sorted(counts.items()))}.",
        ]
        if trucks:
            parts.append(f"Truck activity: {len(trucks)} truck-related frame(s), at " +
                         ", ".join(r['timestamp'][11:16] + " at " + r["location"] for r in trucks) + ".")
        if alerts:
            parts.append(f"Security alerts: {len(alerts)}. " + " ".join(a["message"] for a in alerts))
        else:
            parts.append("No rule-based security alerts were generated.")
        return " ".join(parts)

    def answer(self, question: str) -> str:
        q = question.lower()
        rows = self.store.list_frames()
        alerts = self.store.list_alerts()
        if any(k in q for k in ("truck", "ford", "vehicle")):
            matches = [r for r in rows if any(k in " ".join(r["objects"]) + " " + r["description"].lower()
                                               for k in ("truck", "ford", "vehicle"))]
            if not matches:
                return "I found no indexed truck or vehicle events."
            times = ", ".join(f"{r['timestamp'][11:16]} at {r['location']}" for r in matches)
            return f"I found {len(matches)} truck/vehicle-related frame(s): {times}."
        if any(k in q for k in ("loiter", "midnight", "gate", "alert")):
            matches = [a for a in alerts if "GATE" in a["alert_type"] or "LOITER" in a["alert_type"]]
            if not matches:
                return "No main-gate loitering alerts are currently indexed."
            return "Main-gate security alert(s): " + " ".join(a["message"] for a in matches)
        if "summar" in q or "today" in q or "activity" in q:
            return self.summary()
        if "how many" in q or "count" in q:
            return f"There are {len(rows)} indexed frames and {len(alerts)} alerts."
        if "help" in q:
            return "Ask about truck events, people near the gate, alerts, frame counts, or the daily activity summary."
        return ("I can answer using the local frame index. Try: 'How many times was the blue Ford F150 seen?', "
                "'Was anyone loitering near the gate?', or 'Summarize today's activity.'")
