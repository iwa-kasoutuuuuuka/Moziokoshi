from faster_whisper import WhisperModel
import os

print("Imported faster-whisper successfully without explicit torch import.")
try:
    # Try to initialize model on CPU to see if it works without torch
    model = WhisperModel("tiny", device="cpu", compute_type="int8")
    print("Model initialized on CPU successfully.")
except Exception as e:
    print(f"Failed to initialize: {e}")
