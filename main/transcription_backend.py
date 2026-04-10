import os
import requests


def transcribe_via_http(audio_bytes, filename):
    endpoint = os.getenv("INFERENCE_HTTP_ENDPOINT", "").strip()
    if not endpoint:
        raise ValueError("INFERENCE_HTTP_ENDPOINT is not configured.")

    files = {
        "file": (filename, audio_bytes, "audio/wav"),
    }
    response = requests.post(endpoint, files=files, timeout=600)
    response.raise_for_status()

    payload = response.json()
    text = payload.get("text")
    if not text:
        raise ValueError("Inference response does not include 'text'.")
    return text
