import discord
from discord.ext import commands
from discord import app_commands
import os
import threading
from keep_alive import keep_alive
from commands import setup_commands
# Watchdog for file events
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Custom bot client class
class Client(commands.Bot):
    # Called when bot is readyc
    async def on_ready(self):
        print(f'Logged in as {self.user}! (ID: {self.user.id})')
        try:
            guild_id = os.getenv('GUILD_ID')
            if guild_id:
                guild = discord.Object(id=int(guild_id))
                synced = await self.tree.sync(guild=guild)
                print(f'Synced {len(synced)} commands to the guild: {guild.id}')
            else:
                print('Warning: GUILD_ID not found, commands may not sync properly')
        except Exception as e:
            print(f'Error syncing commands: {e}')
    
    async def on_message(self, message):
        # Don't respond to own messages
        if message.author == self.user:
            return
        
        # Log all messages the bot can see
        print(f"[{message.channel.name}] {message.author.display_name}: {message.content}")
        
        # Respond to specific messages
        if message.content.startswith('Michael'):
            await message.channel.send('<a:jd:1395904586317041794>')
        # On Reaction Add
        if message.content.startswith('M'):
            await message.add_reaction('<a:jd:1395904586317041794>')


# --- Watchdog event handler ---
class STTFileHandler(FileSystemEventHandler):
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.last_text = None

    def on_modified(self, event):
        if event.is_directory:
            return
        if os.path.basename(event.src_path) == "stt_result.txt":
            from utils import is_js_mode
            if not is_js_mode():
                print("STT watcher: JS bot not active, skipping STT result processing.")
                return
            try:
                if not os.path.exists(event.src_path):
                    print(f"STT error: File does not exist: {event.src_path}")
                    return
                with open(event.src_path, "r", encoding="utf-8") as f:
                    text = f.read().strip().lower()
                if text and text != self.last_text:
                    self.last_text = text
                    # Check for trigger words
                    if "michael" in text or "saves" in text or "mike" in text:
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
async def play_song_in_voice(client, song_filename):
    pass  # Logic moved to play_mito command

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

    client = Client(command_prefix="!", intents=intents)

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