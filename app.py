
import sys
import threading
from pathlib import Path
from datetime import datetime

# Make the project's src folder available to Python.
PROJECT_DIR = Path(__file__).resolve().parent
SRC_DIR = PROJECT_DIR / "src"
sys.path.insert(0, str(SRC_DIR))

import cv2
import pandas as pd
import streamlit as st

from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

from drone_agent.storage import EventStore
from drone_agent.simulator import demo_events
from drone_agent.agent import SecurityAnalyst
from drone_agent.vlm import caption_image
from drone_agent.webcam_rules import evaluate_webcam_observation


# -----------------------------
# Streamlit page setup
# -----------------------------

st.set_page_config(
    page_title="Drone Security Analyst",
    page_icon="🚁",
    layout="wide"
)

st.title("🚁 Drone Security Analyst")
st.caption(
    "Prototype dashboard for simulated drone events and "
    "periodic webcam image observations."
)


# -----------------------------
# Database and agent
# -----------------------------

store = EventStore()
agent = SecurityAnalyst(store)


# -----------------------------
# Webcam frame processor
# -----------------------------

class WebcamProcessor(VideoProcessorBase):
    def __init__(self):
        self.lock = threading.Lock()
        self.latest_frame = None

    def recv(self, frame):
        image = frame.to_ndarray(format="bgr24")

        with self.lock:
            self.latest_frame = image.copy()

        return frame

    def get_latest_frame(self):
        with self.lock:
            if self.latest_frame is None:
                return None

            return self.latest_frame.copy()


# -----------------------------
# Sidebar controls
# -----------------------------

with st.sidebar:
    st.header("Controls")

    if st.button(
        "Load / reset demo data",
        type="primary",
        use_container_width=True
    ):
        store.clear()
        count = agent.ingest(demo_events())
        st.success(f"Loaded {count} simulated frames.")

    st.info(
        "Demo data is synthetic. Webcam input is real, "
        "but it is not a live drone feed."
    )

    st.caption(
        "Moondream analyzes webcam images periodically while "
        "the Live Camera tab is active and the camera is running."
    )


# -----------------------------
# Dashboard metrics
# -----------------------------

frames = store.list_frames()
alerts = store.list_alerts()
webcam_alerts = store.list_webcam_alerts()

if st.button("Refresh dashboard alerts"):
    st.rerun()

c1, c2, c3, c4 = st.columns(4)

c1.metric("Indexed frames", len(frames))
c2.metric(
    "Security alerts",
    len(alerts) + len(webcam_alerts)
)
c3.metric(
    "Locations",
    len({x["location"] for x in frames})
)
c4.metric(
    "Vehicle frames",
    sum(
        1 for x in frames
        if "vehicle" in x["objects"] or "truck" in x["objects"]
    )
)


# -----------------------------
# Dashboard tabs
# -----------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "Live-style monitor",
    "Frame index & search",
    "Analyst Q&A",
    "Architecture & notes",
    "📷 Live Camera"
])


# -----------------------------
# Tab 1: Live-style monitor
# -----------------------------

with tab1:
    left, right = st.columns([1.5, 1])

    with left:
        st.subheader("Recent frame activity")

        if frames:
            df = pd.DataFrame([{
                "Time": r["timestamp"].replace("T", " "),
                "Frame": r["frame_id"],
                "Location": r["location"],
                "Objects": ", ".join(r["objects"]),
                "Description": r["description"],
            } for r in frames])

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.warning(
                "No frames loaded yet. "
                "Use 'Load / reset demo data' in the sidebar."
            )

    with right:
        st.subheader("Simulated drone security alerts")

        if alerts:
            for alert in alerts:
                st.error(
                    f"**{alert['severity']} · "
                    f"{alert['timestamp'][11:16]}**\n\n"
                    f"{alert['message']}"
                )
        else:
            st.success("No simulated drone alerts indexed.")

    st.divider()
    st.subheader("Webcam observation alerts")

    if webcam_alerts:
        for alert in webcam_alerts:
            message = (
                f"**{alert['severity']} · "
                f"{alert['alert_type']}**\n\n"
                f"{alert['message']}"
            )

            if alert["severity"] == "HIGH":
                st.error(message)
            else:
                st.info(message)

        st.caption(
            "These are preliminary image-based observations. "
            "They require human verification and are not confirmed threats."
        )
    else:
        st.info(
            "No webcam observation alerts have been saved yet. "
            "Start the camera in the Live Camera tab."
        )


# -----------------------------
# Tab 2: Frame index and search
# -----------------------------

with tab2:
    st.subheader("Search indexed frames")

    col1, col2, col3 = st.columns(3)

    query = col1.text_input(
        "Object / keyword",
        placeholder="truck, person, Ford"
    )

    location = col2.text_input(
        "Location",
        placeholder="Main Gate"
    )

    day = col3.text_input(
        "Date (YYYY-MM-DD)",
        placeholder="2026-11-26"
    )

    start = f"{day}T00:00:00" if day else ""
    end = f"{day}T23:59:59" if day else ""

    results = store.search_frames(
        query=query,
        start=start,
        end=end,
        location=location
    )

    st.caption(f"{len(results)} matching frame(s)")

    if results:
        search_df = pd.DataFrame([{
            "Timestamp": r["timestamp"],
            "Frame ID": r["frame_id"],
            "Location": r["location"],
            "Objects": ", ".join(r["objects"]),
            "Description": r["description"],
            "Altitude (m)": r["altitude_m"]
        } for r in results])

        st.dataframe(
            search_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "No matching frames. "
            "Load demo data or adjust the filters."
        )


# -----------------------------
# Tab 3: Analyst Q&A
# -----------------------------

with tab3:
    st.subheader("Ask the Security Analyst")

    st.write(
        "Ask questions about the indexed simulated drone events "
        "and their rule-based alerts."
    )

    question = st.text_input(
        "Enter your question",
        placeholder="How many times was the blue Ford F150 seen?"
    )

    if st.button("Ask analyst", key="ask_analyst"):
        if question.strip():
            answer = agent.answer(question)
            st.markdown("**Analyst response:**")
            st.write(answer)
        else:
            st.warning("Please enter a question first.")

    st.markdown("**Example questions:**")
    st.markdown(
        "- How many times was the blue Ford F150 seen?\n"
        "- Was anyone loitering near the gate?\n"
        "- Summarize today's activity.\n"
        "- How many alerts were generated?"
    )


# -----------------------------
# Tab 4: Architecture and notes
# -----------------------------

with tab4:
    st.subheader("Prototype architecture")

    st.markdown("""
    **1. Input layer**
    - Synthetic drone frame events and telemetry.
    - Webcam images captured through the browser.

    **2. AI image analysis**
    - Ollama runs the local Moondream vision model.
    - The model generates a natural-language description
      of each captured webcam image.
    - The prototype requests analysis approximately every
      15 seconds while this tab is active and the camera is running.

    **3. Observation and alert layer**
    - Webcam descriptions are checked for selected keywords.
    - Preliminary observations are saved separately from
      simulated drone security alerts.
    - Human verification is required before treating an
      observation as a real security incident.

    **4. Storage layer**
    - SQLite stores simulated frames and drone alerts.
    - Separate tables store webcam observations and webcam alerts.

    **5. Analyst layer**
    - The analyst answers questions using the indexed
      simulated drone events.
    """)

    st.warning(
        "Important limitation: this is a prototype. Webcam images do not "
        "contain drone GPS, altitude, or dwell-time telemetry. "
        "The webcam analysis does not establish identity, intent, "
        "or a verified security threat."
    )

    st.subheader("Current prototype capabilities")

    st.markdown("""
    - Simulated drone event ingestion.
    - SQLite frame indexing and search.
    - Deterministic rule-based drone alerts.
    - Local Moondream webcam image captioning.
    - Periodic webcam image capture and analysis.
    - Persistent preliminary webcam observation alerts.
    - Basic analyst question answering over indexed drone events.
    """)


# -----------------------------
# Tab 5: Live Camera and Moondream
# -----------------------------

with tab5:
    st.subheader("Live webcam monitoring")

    st.write(
        "Start the camera below. When it is running, the app will "
        "capture an image and ask the local Moondream model to describe "
        "it approximately every 15 seconds."
    )

    st.warning(
        "This is a webcam demonstration, not a live drone video feed. "
        "Moondream descriptions and keyword-based alerts are preliminary "
        "and must be checked by a human."
    )

    ctx = webrtc_streamer(
        key="drone-security-camera",
        video_processor_factory=WebcamProcessor,
        media_stream_constraints={
            "video": True,
            "audio": False
        },
        async_processing=True
    )

    st.divider()

    # Run this fragment periodically while the tab is active.
    @st.fragment(run_every="15s")
    def periodic_webcam_analysis():
        st.subheader("Automatic Moondream analysis")

        if not ctx.state.playing:
            st.info(
                "Start the webcam above to begin periodic image analysis."
            )
            return

        processor = ctx.video_processor

        if processor is None:
            st.info("Waiting for the webcam to provide a frame...")
            return

        image = processor.get_latest_frame()

        if image is None:
            st.info("Waiting for the first webcam frame...")
            return

        captures_dir = PROJECT_DIR / "data" / "captures"
        captures_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

        filename = (
            "auto_webcam_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".jpg"
        )

        image_path = captures_dir / filename

        saved = cv2.imwrite(str(image_path), image)

        if not saved:
            st.error("Could not save the webcam image.")
            return

        st.image(
            str(image_path),
            caption="Image captured for Moondream analysis",
            use_container_width=True
        )

        try:
            with st.spinner("Moondream is analyzing the webcam image..."):
                description = caption_image(
                    str(image_path),
                    model="moondream"
                )

            if not description:
                description = "The vision model returned an empty description."

            description_lower = description.lower()

            keyword_list = [
                "person",
                "people",
                "car",
                "truck",
                "vehicle",
                "van",
                "motorcycle",
                "bicycle",
                "dog",
                "cat"
            ]

            detected_objects = [
                word for word in keyword_list
                if word in description_lower
            ]

            generated_webcam_alerts = evaluate_webcam_observation(
                description,
                detected_objects
            )

            # Persist the observation and its preliminary alerts.
            store.add_webcam_observation(
                timestamp,
                filename,
                description,
                detected_objects,
                generated_webcam_alerts
            )

            st.success("Webcam observation saved to the database.")

            st.markdown("**Moondream observation:**")
            st.write(description)

            st.markdown("**Keyword matches:**")
            if detected_objects:
                st.write(", ".join(detected_objects))
            else:
                st.write("No configured object keywords matched.")

            st.markdown("**Alerts from this observation:**")

            if generated_webcam_alerts:
                for alert in generated_webcam_alerts:
                    alert_text = (
                        f"**{alert['severity']} · "
                        f"{alert['alert_type']}**\n\n"
                        f"{alert['message']}"
                    )

                    if alert["severity"] == "HIGH":
                        st.error(alert_text)
                    else:
                        st.info(alert_text)
            else:
                st.success("No configured webcam observation alerts.")

            st.caption(
                "Analysis is based on the model's image description. "
                "It is not a verified detection."
            )

        except Exception as exc:
            st.error(f"Webcam analysis failed: {exc}")
            st.caption(
                "Check that Ollama is running and that the "
                "moondream model is available."
            )

    periodic_webcam_analysis()

    st.divider()
    st.subheader("Saved webcam observations")

    saved_observations = store.list_webcam_observations()

    if saved_observations:
        observation_df = pd.DataFrame([
            {
                "Timestamp": row["timestamp"],
                "Image": row["image_filename"],
                "Objects": ", ".join(row["objects"]),
                "Description": row["description"]
            }
            for row in saved_observations
        ])

        st.dataframe(
            observation_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No webcam observations have been saved yet.")
