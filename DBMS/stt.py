import sys
import soundfile as sf
import os

# Usage: python stt.py <audio_file>
audio_path = sys.argv[1]
data, samplerate = sf.read(audio_path, dtype='int16')
# Convert stereo to mono if needed
if len(data.shape) == 2:
    print("Converting stereo to mono...")
    data = data.mean(axis=1).astype(data.dtype)

# Speech-to-text with Vosk
from vosk import Model, KaldiRecognizer, SetLogLevel
import json
import os
SetLogLevel(-1)
# Use relative path for model directory
model_path = os.path.join(os.path.dirname(__file__), "model1")
try:
    model = Model(model_path)
except Exception as e:
    print(f"Vosk model not found at '{model_path}'. Download a model from https://alphacephei.com/vosk/models and extract to './model1'.")
    sys.exit(1)

rec = KaldiRecognizer(model, samplerate)
rec.AcceptWaveform(data.tobytes())
result = rec.Result()
text = json.loads(result).get('text', '')
print("STT: ", text)
