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
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
model_path = os.path.join(project_root, "model")
try:
    model = Model(model_path)
except Exception as e:
    print(f"Vosk model not found at '{model_path}'. Download a model from https://alphacephei.com/vosk/models and extract to './model'.")
    sys.exit(1)

rec = KaldiRecognizer(model, samplerate)
rec.AcceptWaveform(data.tobytes())
result = rec.Result()
text = json.loads(result).get('text', '')
print("STT: ", text)
# Write STT result to file for bot integration
result_file = os.path.join(os.path.dirname(__file__), "stt_result.txt")
try:
    with open(result_file, "w", encoding="utf-8") as f:
        f.write(text)
    # Delete the processed audio file
    try:
        os.remove(audio_path)
        print(f"Deleted processed audio file: {audio_path}")
    except Exception as e:
        print(f"Error deleting audio file {audio_path}: {e}")
except Exception as e:
    print(f"Error writing STT result: {e}")
