
"""Real-image captioning using a locally running Ollama vision model."""
import base64
import requests


def caption_image(
    image_path: str,
    model: str = "moondream",
    host: str = "http://localhost:11434",
) -> str:
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    response = requests.post(
        f"{host}/api/generate",
        json={
            "model": model,
            "prompt": (
                "Describe only what is visibly present in this image. "
                "Mention visible people, vehicles, objects, and potentially "
                "notable security activity. Do not guess identities, "
                "intentions, or details that cannot be verified."
            ),
            "images": [encoded],
            "stream": False,
        },
        timeout=180,
    )

    response.raise_for_status()
    return response.json().get("response", "").strip()
