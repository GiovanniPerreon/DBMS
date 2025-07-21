import os

def is_js_mode():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    js_active_path = os.path.join(project_root, "bot", "js_active.txt")
    return os.path.exists(js_active_path)

def delete_all_audio_files(audio_dir):
    if os.path.exists(audio_dir):
        for file in os.listdir(audio_dir):
            file_path = os.path.join(audio_dir, file)
            # Only delete files that start with 'voice_'
            if os.path.isfile(file_path) and file.startswith("voice_"):
                try:
                    os.remove(file_path)
                    print(f"Deleted audio file: {file_path}")
                except Exception as e:
                    print(f"Error deleting audio file {file_path}: {e}")

def signal_js_leave():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    leave_signal_path = os.path.join(project_root, "bot", "leave_signal.txt")
    audio_dir = os.path.join(project_root, "audio")
    try:
        with open(leave_signal_path, "w", encoding="utf-8") as f:
            f.write("leave")
        print("Leave signal written for listener.js (from utils.py)")
        # Wait for JS bot to quit (wait for leave_signal.txt to be deleted)
        import time
        max_wait = 10  # seconds
        waited = 0
        while os.path.exists(leave_signal_path) and waited < max_wait:
            time.sleep(0.5)
            waited += 0.5
    except Exception as e:
        print(f"Error writing leave signal: {e}")
    import time
    delete_all_audio_files(audio_dir)
    time.sleep(3)  # Extra 3 seconds delay after everything else
