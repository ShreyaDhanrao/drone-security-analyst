
import json
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from .models import FrameEvent

DEFAULT_DB = Path(__file__).resolve().parents[2] / "data" / "drone_security.db"


class EventStore:
    def __init__(self, db_path=DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def close(self):
        pass

    def _init_db(self):
        with self.connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS frames (
                    frame_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    location TEXT NOT NULL,
                    altitude_m REAL NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    description TEXT NOT NULL,
                    objects_json TEXT NOT NULL,
                    dwell_minutes INTEGER NOT NULL DEFAULT 0
                )
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_frames_timestamp
                ON frames(timestamp)
            """)

            con.execute("""
                CREATE INDEX IF NOT EXISTS idx_frames_location
                ON frames(location)
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    frame_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    FOREIGN KEY(frame_id) REFERENCES frames(frame_id)
                )
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS webcam_observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    image_filename TEXT NOT NULL,
                    description TEXT NOT NULL,
                    objects_json TEXT NOT NULL
                )
            """)

            con.execute("""
                CREATE TABLE IF NOT EXISTS webcam_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    observation_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    FOREIGN KEY(observation_id)
                        REFERENCES webcam_observations(id)
                )
            """)

    def clear(self):
        with self.connect() as con:
            con.execute("DELETE FROM alerts")
            con.execute("DELETE FROM frames")

    def add_event(self, event: FrameEvent, alerts: list[dict]):
        d = event.to_dict()

        with self.connect() as con:
            con.execute("""
                INSERT OR REPLACE INTO frames
                (frame_id, timestamp, location, altitude_m,
                 latitude, longitude, description,
                 objects_json, dwell_minutes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                d["frame_id"],
                d["timestamp"],
                d["location"],
                d["altitude_m"],
                d["latitude"],
                d["longitude"],
                d["description"],
                json.dumps(d["objects"]),
                d["dwell_minutes"]
            ))

            con.execute(
                "DELETE FROM alerts WHERE frame_id=?",
                (d["frame_id"],)
            )

            for alert in alerts:
                con.execute("""
                    INSERT INTO alerts
                    (frame_id, timestamp, severity, alert_type, message)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    d["frame_id"],
                    d["timestamp"],
                    alert["severity"],
                    alert["alert_type"],
                    alert["message"]
                ))

    def list_frames(self):
        with self.connect() as con:
            rows = con.execute(
                "SELECT * FROM frames ORDER BY timestamp"
            ).fetchall()

        return [self._decode(r) for r in rows]

    def _decode(self, row):
        d = dict(row)
        d["objects"] = json.loads(d.pop("objects_json"))
        return d

    def search_frames(self, query="", start="", end="", location=""):
        sql = "SELECT * FROM frames WHERE 1=1"
        args = []

        if query:
            sql += """
                AND (LOWER(description) LIKE ?
                OR LOWER(objects_json) LIKE ?)
            """
            q = f"%{query.lower()}%"
            args.extend([q, q])

        if start:
            sql += " AND timestamp >= ?"
            args.append(start)

        if end:
            sql += " AND timestamp <= ?"
            args.append(end)

        if location:
            sql += " AND LOWER(location) LIKE ?"
            args.append(f"%{location.lower()}%")

        sql += " ORDER BY timestamp"

        with self.connect() as con:
            rows = con.execute(sql, args).fetchall()

        return [self._decode(r) for r in rows]

    def list_alerts(self):
        with self.connect() as con:
            rows = con.execute(
                "SELECT * FROM alerts ORDER BY timestamp"
            ).fetchall()

        return [dict(r) for r in rows]

    def add_webcam_observation(
        self, timestamp, image_filename, description, objects, alerts
    ):
        with self.connect() as con:
            cursor = con.execute("""
                INSERT INTO webcam_observations
                (timestamp, image_filename, description, objects_json)
                VALUES (?, ?, ?, ?)
            """, (
                timestamp,
                image_filename,
                description,
                json.dumps(objects)
            ))

            observation_id = cursor.lastrowid

            for alert in alerts:
                con.execute("""
                    INSERT INTO webcam_alerts
                    (observation_id, timestamp, severity, alert_type, message)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    observation_id,
                    timestamp,
                    alert["severity"],
                    alert["alert_type"],
                    alert["message"]
                ))

        return observation_id

    def list_webcam_observations(self):
        with self.connect() as con:
            rows = con.execute("""
                SELECT * FROM webcam_observations
                ORDER BY timestamp DESC
            """).fetchall()

        results = []

        for row in rows:
            item = dict(row)
            item["objects"] = json.loads(item.pop("objects_json"))
            results.append(item)

        return results

    def list_webcam_alerts(self):
        with self.connect() as con:
            rows = con.execute("""
                SELECT * FROM webcam_alerts
                ORDER BY timestamp DESC
            """).fetchall()

        return [dict(row) for row in rows]

    def object_counts(self):
        counts = {}

        for row in self.list_frames():
            for obj in row["objects"]:
                counts[obj] = counts.get(obj, 0) + 1

        return counts
