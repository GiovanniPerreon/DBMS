import discord
from discord.ext.voice_recv import VoiceRecvClient
from discord import app_commands
import os
import threading
from keep_alive import keep_alive
from commands import setup_commands
# Watchdog for file events
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

    # Removed custom Client class. Use VoiceRecvClient directly.


# --- Watchdog event handler ---
class STTFileHandler(FileSystemEventHandler):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.last_text = None
        self.last_play_time = 0   # For cooldown
        self.cooldown_seconds = 30  # Change as needed

    def on_modified(self, event):
        if event.is_directory:
            return
        if os.path.basename(event.src_path) == "stt_result.txt":
            try:
                if not os.path.exists(event.src_path):
                    print(f"ScTT error: File does not exist: {event.src_path}")
                    return
                with open(event.src_path, "r", encoding="utf-8") as f:
                    text = f.read().strip().lower()
                import time
                now = time.time()
                if text and text != self.last_text:
                    self.last_text = text
                    # Check for trigger words
                    if ("michael" in text or "saves" in text or "mike" in text):
                        # Cooldown check
                        if now - self.last_play_time < self.cooldown_seconds:
                            print(f"Song cooldown active. Try again later.")
                            return
                        self.last_play_time = now
                        # Call the play_mito_in_voice function directly
                        from audio_actions import play_mito_in_voice
                        loop = getattr(self.client, 'loop', None)
                        if loop and loop.is_running():
                            future = asyncio.run_coroutine_threadsafe(
                                play_mito_in_voice(self.client), loop)
                        else:   
                            print("Discord event loop not running, cannot play song.")
                        return
            except Exception as e:
                print(f"Error reading stt_result.txt: {e}")

# --- Play song in voice channel ---
import asyncio
# async def play_song_in_voice(client, song_filename):
#     pass  # Logic moved to play_mito command

def main():
    """Main function to start the bot and keep-alive server"""
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    print("Keep-alive server started")

    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        print("ERROR: DISCORD_TOKEN environment variable not found!")
        print("Please set your Discord bot token in the environment variables.")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    intents.members = True
    intents.presences = True

    from discord.ext import commands
    client = commands.Bot(command_prefix="!", intents=intents)

    @client.event
    async def on_ready():
        print(f'Logged in as {client.user}! (ID: {client.user.id})')
        try:
            guild_id = os.getenv('GUILD_ID')
            if guild_id:
                guild = discord.Object(id=int(guild_id))
                synced = await client.tree.sync(guild=guild)
                print(f'Synced {len(synced)} commands to the guild: {guild.id}')
            else:
                print('Warning: GUILD_ID not found, commands may not sync properly')
        except Exception as e:
            print(f'Error syncing commands: {e}')

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return
        print(f"[{message.channel.name}] {message.author.display_name}: {message.content}")
        if message.content.startswith('Michael'):
            await message.channel.send('<a:jd:1395904586317041794>')
        if message.content.startswith('M'):
            await message.add_reaction('<a:jd:1395904586317041794>')

    guild_id = os.getenv('GUILD_ID')
    if not guild_id:
        print("ERROR: GUILD_ID environment variable not found!")
        print("Please set your Discord server ID in the environment variables.")
        return

    try:
        GUILD_ID = discord.Object(id=int(guild_id))
    except ValueError:
        print("ERROR: GUILD_ID must be a valid number!")
        return
    setup_commands(client, GUILD_ID)

    # Start watchdog observer for stt_result.txt
    stt_file = os.path.join(os.path.dirname(__file__), "stt_result.txt")
    event_handler = STTFileHandler(client)
    observer = Observer()
    observer.schedule(event_handler, os.path.dirname(stt_file), recursive=False)
    observer.start()
    print("STT file watcher started")

    try:
        print("Starting Discord bot...")
        client.run(discord_token)
    except Exception as e:
        print(f"Error starting bot: {e}")
    finally:
        observer.stop()
        observer.join()

if __name__ == "__main__":
    main()