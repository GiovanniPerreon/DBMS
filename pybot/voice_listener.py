import discord
import asyncio
from discord.ext.voice_recv import VoiceRecvClient, AudioSink

# Custom AudioSink to process received audio
class MyAudioSink(AudioSink):
    def __init__(self):
        super().__init__()

    def on_audio(self, user_id, pcm):
        # pcm is raw PCM audio data (bytes)
        print(f"Received audio from user {user_id}, {len(pcm)} bytes")
        # You can process/save the audio here

    def cleanup(self):
        # Called when the sink is stopped/disconnected
        print("AudioSink cleanup called.")

    def wants_opus(self):   
        # Return True if you want Opus frames, False for PCM
        return False  # We want PCM as in on_audio

    def write(self, user_id, data):
        # Called with audio data (PCM or Opus depending on wants_opus)
        if hasattr(data, 'pcm'):
            print(f"Write called for user {user_id}, {len(data.pcm)} bytes")
        else:
            print(f"Write called for user {user_id}, VoiceData object")
        # You can process/save the audio here

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
