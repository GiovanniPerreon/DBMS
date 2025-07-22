import discord
import asyncio
import sys
from discord.ext.voice_recv import VoiceRecvClient, AudioSink, WaveSink

# Custom AudioSink to process received audio
class MyAudioSink(AudioSink):
    def __init__(self):
        super().__init__()
        # Use WaveSink per user
        self.wave_sinks = {}
        self.wave_durations = {}  # Track PCM length per user
        self.wave_parts = {}      # Track part number per user

    def on_audio(self, user_id, pcm):
        # pcm is raw PCM audio data (bytes)
        #print(f"Received audio from user {user_id}, {len(pcm)} bytes")
        import os
        audio_dir = os.path.join(os.path.dirname(__file__), "..", "audio_test")
        os.makedirs(audio_dir, exist_ok=True)
        # Track part number per user
        if user_id not in self.wave_parts:
            self.wave_parts[user_id] = 0
        part = self.wave_parts[user_id]
        wav_path = os.path.join(audio_dir, f"user_{user_id}_{part}.wav")
        from discord.ext.voice_recv.opus import VoiceData
        voice_data = VoiceData(pcm=pcm)
        # Use persistent WaveSink per user
        if user_id not in self.wave_sinks:
            self.wave_sinks[user_id] = WaveSink(wav_path)
            self.wave_durations[user_id] = 0
        self.wave_sinks[user_id].write(user_id, voice_data)
        # Track PCM length for duration
        self.wave_durations[user_id] += len(pcm)
        # Automatic refresh after 5 seconds
        seconds = self.wave_durations[user_id] / (48000 * 2)
        if seconds >= 10:
            print(f"[REFRESH] Threshold reached for user {user_id}, refreshing file.")
            self.wave_sinks[user_id].cleanup()
            # Run STT on the just-finished file
            prev_wav_path = os.path.join(audio_dir, f"user_{user_id}_{part}.wav")
            stt_path = os.path.join(os.path.dirname(__file__), "stt.py")
            try:
                import subprocess, sys
                subprocess.run([sys.executable, stt_path, prev_wav_path], check=True)
            except Exception as e:
                print(f"Error running STT for {prev_wav_path}: {e}")
            self.wave_parts[user_id] += 1
            part = self.wave_parts[user_id]
            new_wav_path = os.path.join(audio_dir, f"user_{user_id}_{part}.wav")
            self.wave_sinks[user_id] = WaveSink(new_wav_path)
            self.wave_durations[user_id] = 0

    def cleanup(self):
        # Called when the sink is stopped/disconnected
        print("AudioSink cleanup called.")
        import os, subprocess, sys
        stt_path = os.path.join(os.path.dirname(__file__), "stt.py")
        audio_dir = os.path.join(os.path.dirname(__file__), "..", "audio_test")
        for user_id, sink in self.wave_sinks.items():
            if sink and hasattr(sink, 'cleanup'):
                sink.cleanup()
                wav_path = os.path.join(audio_dir, f"user_{user_id}.wav")
                if os.path.exists(wav_path):
                    print(f"Running STT for {wav_path}")
                    try:
                        subprocess.run([sys.executable, stt_path, wav_path], check=True)
                    except Exception as e:
                        print(f"Error running STT for {wav_path}: {e}")
            self.wave_sinks[user_id] = None

    def _pcm_to_numpy(self, pcm_bytes):
        import numpy as np
        # Convert bytes to numpy array (int16)
        return np.frombuffer(pcm_bytes, dtype=np.int16)

    def wants_opus(self):   
        # Return True if you want Opus frames, False for PCM
        return False  # We want PCM as in on_audio

    def write(self, user_id, data):
        # Called with audio data (PCM or Opus depending on wants_opus)
        import os
        audio_dir = os.path.join(os.path.dirname(__file__), "..", "audio_test")
        os.makedirs(audio_dir, exist_ok=True)
        if user_id not in self.wave_parts:
            self.wave_parts[user_id] = 0
        part = self.wave_parts[user_id]
        wav_path = os.path.join(audio_dir, f"user_{user_id}_{part}.wav")
        if hasattr(data, 'pcm'):
            #print(f"Write called for user {user_id}, {len(data.pcm)} bytes")
            if user_id not in self.wave_sinks:
                self.wave_sinks[user_id] = WaveSink(wav_path)
                self.wave_durations[user_id] = 0
            # Ensure VoiceData has required fields
            from discord.ext.voice_recv.opus import VoiceData
            if not hasattr(data, 'packet') or not hasattr(data, 'source'):
                # Wrap in VoiceData if missing
                data = VoiceData(pcm=data.pcm, packet=None, source=user_id)
            self.wave_sinks[user_id].write(user_id, data)
            # Track PCM length for duration
            self.wave_durations[user_id] += len(data.pcm)
            seconds = self.wave_durations[user_id] / (48000 * 2)
            if seconds >= 10:
                #print(f"[REFRESH] Threshold reached for user {user_id}, refreshing file.")
                self.wave_sinks[user_id].cleanup()
                # Run STT on the just-finished file
                prev_wav_path = os.path.join(audio_dir, f"user_{user_id}_{part}.wav")
                stt_path = os.path.join(os.path.dirname(__file__), "stt.py")
                try:
                    import subprocess, sys
                    subprocess.run([sys.executable, stt_path, prev_wav_path], check=True)
                except Exception as e:
                    print(f"Error running STT for {prev_wav_path}: {e}")
                self.wave_parts[user_id] += 1
                part = self.wave_parts[user_id]
                new_wav_path = os.path.join(audio_dir, f"user_{user_id}_{part}.wav")
                self.wave_sinks[user_id] = WaveSink(new_wav_path)
                self.wave_durations[user_id] = 0
        else:
            print(f"Write called for user {user_id}, VoiceData object")

# This function will be triggered by the /listen command
async def start_voice_listener(interaction: discord.Interaction):
    voice_channel = interaction.user.voice.channel
    try:
        # Connect to the voice channel
        voice_client = await voice_channel.connect()
        print(f"Connected to voice channel: {voice_channel.name}")
        # Start listening for audio
        sink = MyAudioSink()
        voice_client.listen(sink)
        await interaction.response.send_message(f"🔊 Listening to voice channel: {voice_channel.name}", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Error connecting to voice channel: {str(e)}", ephemeral=True)
