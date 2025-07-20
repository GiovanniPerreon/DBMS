import os
import soundfile as sf
from vosk import Model, KaldiRecognizer
import json

MODEL_PATH = os.path.abspath("model")
AUDIO_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio")
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']

def stt_file(audio_path, model):
    data, samplerate = sf.read(audio_path, dtype='int16')
    # Convert stereo to mono if needed
    if len(data.shape) == 2:
        print("Converting stereo to mono...")
        data = data.mean(axis=1).astype(data.dtype)
    print("--- AUDIO RECEIVED ---")
    print(f"File: {audio_path}")
    print(f"Sample rate: {samplerate}")
    print(f"Shape: {data.shape}")
    print(f"Dtype: {data.dtype}")
    print(f"First 10 samples: {data[:10]}")
    # Show summary of bytes before passing to the model
    data_bytes = data.tobytes()
    print(f"First 100 bytes before model: {list(data_bytes[:100])}")
    nonzero_count = sum(1 for b in data_bytes if b != 0)
    print(f"Nonzero byte count: {nonzero_count}")
    if nonzero_count == 0:
        print("Warning: All bytes are zero (silent audio)")
    if not audio_path.lower().endswith('.wav'):
        print("Warning: File is not WAV. Consider converting to WAV for best results.")
    rec = KaldiRecognizer(model, samplerate)
    # Progress: process in chunks and show bytes processed
    chunk_size = 4096
    total_bytes = len(data_bytes)
    bytes_processed = 0
    for i in range(0, total_bytes, chunk_size):
        rec.AcceptWaveform(data_bytes[i:i+chunk_size])
        bytes_processed += min(chunk_size, total_bytes - bytes_processed)
        print(f"Progress: {bytes_processed}/{total_bytes} bytes processed")
    result = rec.Result()
    text = json.loads(result).get('text', '')
    print(f"STT Result: {text}")
    print("-----------------------\n")

if __name__ == "__main__":
    try:
        model = Model(MODEL_PATH)
    except Exception as e:
        print(f"Vosk model not found at '{MODEL_PATH}'. Download a model from https://alphacephei.com/vosk/models and extract to './model'.")
        exit(1)

    audio_files = [file for file in os.listdir(AUDIO_DIR) if any(file.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)]
    print(f"Testing {len(audio_files)} audio files in: {AUDIO_DIR}\n")
    for idx, file in enumerate(audio_files, 1):
        audio_path = os.path.join(AUDIO_DIR, file)
        print(f"\nProcessing file {idx}/{len(audio_files)}: {file}")
        stt_file(audio_path, model)
