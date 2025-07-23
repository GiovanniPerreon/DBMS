import discord
import os
async def play_gambling_audio(client):
    """Play Gambling.wav in the first voice channel with a non-bot user."""
    import asyncio
    await asyncio.sleep(1)
    print("[play_gambling_audio] Looking for a voice channel with a non-bot user...")
    for guild in client.guilds:
        for vc in guild.voice_channels:
            members = [m for m in vc.members if not m.bot]
            if members:
                try:
                    print(f"[play_gambling_audio] Connecting to voice channel: {vc.name}")
                    voice_client = discord.utils.get(client.voice_clients, guild=guild)
                    if voice_client is None or not voice_client.is_connected():
                        voice_client = await vc.connect()
                        print(f"[play_gambling_audio] Connected to {vc.name}")
                    else:
                        print(f"[play_gambling_audio] Already connected to {vc.name}")
                    if voice_client.is_playing():
                        print("[play_gambling_audio] Stopping currently playing audio...")
                        voice_client.stop()
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                    sound_path = os.path.join(project_root, "audio", "Gambling.wav")
                    print(f"[play_gambling_audio] Attempting to play: {sound_path}")
                    if not os.path.exists(sound_path):
                        print(f"[play_gambling_audio] ERROR: File not found: {sound_path}")
                        return
                    source = discord.FFmpegOpusAudio(sound_path)
                    voice_client.play(source, after=lambda e: print(f'Error: {e}') if e else None)
                    print(f"[play_gambling_audio] Playing Gambling.wav in {vc.name}")
                except Exception as e:
                    print(f"[play_gambling_audio] Error playing Gambling.wav: {e}")
                return

async def play_mito_in_voice(client):
    # Add delay to allow Discord to release the channel
    import asyncio
    await asyncio.sleep(4)
    print("[play_mito_in_voice] Looking for a voice channel with a non-bot user...")
    for guild in client.guilds:
        for vc in guild.voice_channels:
            members = [m for m in vc.members if not m.bot]
            if members:
                try:
                    print(f"[play_mito_in_voice] Connecting to voice channel: {vc.name}")
                    voice_client = discord.utils.get(client.voice_clients, guild=guild)
                    if voice_client is None or not voice_client.is_connected():
                        voice_client = await vc.connect()
                        print(f"[play_mito_in_voice] Connected to {vc.name}")
                    else:
                        print(f"[play_mito_in_voice] Already connected to {vc.name}")
                    if voice_client.is_playing():
                        print("[play_mito_in_voice] Stopping currently playing audio...")
                        voice_client.stop()
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
                    sound_path = os.path.join(project_root, "audio", "Il_mio_mito.mp3")
                    print(f"[play_mito_in_voice] Attempting to play: {sound_path}")
                    if not os.path.exists(sound_path):
                        print(f"[play_mito_in_voice] ERROR: File not found: {sound_path}")
                        return
                    source = discord.FFmpegOpusAudio(sound_path)
                    voice_client.play(source, after=lambda e: print(f'Error: {e}') if e else None)
                    print(f"[play_mito_in_voice] Playing Il_mio_mito.mp3 in {vc.name}")
                except Exception as e:
                    print(f"[play_mito_in_voice] Error playing song: {e}")
                return
