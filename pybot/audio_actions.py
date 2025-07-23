async def play_audio_in_voice(client, filename, delay=1):
    """Play any audio file in the first voice channel with a non-bot user."""
    import asyncio
    await asyncio.sleep(delay)
    print(f"[play_audio_in_voice] Looking for a voice channel with a non-bot user...")
    for guild in client.guilds:
        for vc in guild.voice_channels:
            members = [m for m in vc.members if not m.bot]
            if members:
                try:
                    print(f"[play_audio_in_voice] Connecting to voice channel: {vc.name}")
                    voice_client = discord.utils.get(client.voice_clients, guild=guild)
                    if voice_client is None or not voice_client.is_connected():
                        voice_client = await vc.connect()
                        print(f"[play_audio_in_voice] Connected to {vc.name}")
                    else:
                        print(f"[play_audio_in_voice] Already connected to {vc.name}")
                    if voice_client.is_playing():
                        print(f"[play_audio_in_voice] Skipping {filename}, something else is already playing in {vc.name}.")
                        return
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                    sound_path = os.path.join(project_root, "audio", filename)
                    print(f"[play_audio_in_voice] Attempting to play: {sound_path}")
                    if not os.path.exists(sound_path):
                        print(f"[play_audio_in_voice] ERROR: File not found: {sound_path}")
                        return
                    source = discord.FFmpegOpusAudio(sound_path)
                    voice_client.play(source, after=lambda e: print(f'Error: {e}') if e else None)
                    print(f"[play_audio_in_voice] Playing {filename} in {vc.name}")
                except Exception as e:
                    print(f"[play_audio_in_voice] Error playing {filename}: {e}")
                return
import discord
import os
async def play_gambling_audio(client):
    """Play Gambling.wav in the first voice channel with a non-bot user."""
    await play_audio_in_voice(client, "Gambling.mp3", delay=1)

async def play_mito_in_voice(client):
    await play_audio_in_voice(client, "Il_mio_mito.mp3", delay=4)

async def play_dang_it_audio(client):
    """Play dang_it.wav in the first voice channel with a non-bot user."""
    await play_audio_in_voice(client, "dang_it.mp3", delay=1)
