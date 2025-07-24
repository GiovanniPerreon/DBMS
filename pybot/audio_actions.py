import discord
from discord.ext.voice_recv import VoiceRecvClient
import os
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
                        voice_client = await vc.connect(cls=VoiceRecvClient)
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

async def play_gambling_audio(client):
    """Play Gambling.wav in the first voice channel with a non-bot user."""
    await play_audio_in_voice(client, "Gambling.mp3", delay=1)

async def play_mito_in_voice(client):
    await play_audio_in_voice(client, "Il_mio_mito.mp3", delay=4)

async def play_dang_it_audio(client):
    """Play dang_it.wav in the first voice channel with a non-bot user."""
    await play_audio_in_voice(client, "dang_it.mp3", delay=1)

# --- Stop audio playback in all voice channels ---
async def stop_audio_in_voice(client):
    """Stop audio playback and disconnect from all voice channels for this client."""
    for voice_client in list(client.voice_clients):
        try:
            if voice_client.is_playing():
                voice_client.stop()
                print(f"[stop_audio_in_voice] Stopped audio in {voice_client.channel.name}")
            await voice_client.disconnect(force=True)
            print(f"[stop_audio_in_voice] Disconnected from {voice_client.channel.name}")
        except Exception as e:
            print(f"[stop_audio_in_voice] Error stopping/disconnecting: {e}")

# --- Play Curse_you_Bayle.mp3 in a voice channel ---
async def play_curse_you_bayle_audio(client):
    """Play Curse_you_Bayle.mp3 in the first voice channel with a non-bot user."""
    await play_audio_in_voice(client, "Curse_you_Bayle.mp3", delay=1)
