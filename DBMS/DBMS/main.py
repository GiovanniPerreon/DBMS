import discord
from discord.ext import commands
from discord import app_commands
import os
#import threading
#from keep_alive import keep_alive

# Custom bot client class
class Client(commands.Bot):
    # Called when bot is ready
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
        # Respond to a specific message
        if message.author == self.user:
            return
        if message.content.startswith('Michael'):
            await message.channel.send('<a:jd:1395904586317041794>')
        # On Reaction Add
        if message.content.startswith('M'):
            await message.add_reaction('<a:jd:1395904586317041794>')
def main():
    # """Main function to start the bot and keep-alive server"""
    # # Start the keep-alive server in a separate thread
    # keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    # keep_alive_thread.start()
    # print("Keep-alive server started")
    
    # Get Discord token from environment variables
    discord_token = os.getenv('DISCORD_TOKEN')
    if not discord_token:
        print("ERROR: DISCORD_TOKEN environment variable not found!")
        print("Please set your Discord bot token in the environment variables.")
        return
    # Set up bot permissions
    intents = discord.Intents.default()
    # Allow reading message text
    intents.message_content = True
    # Enable voice state intents for better voice channel support
    intents.voice_states = True
    # Initialize the bot
    client = Client(command_prefix="!", intents=intents)
    
    # Get Guild ID from environment variables
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

    @client.tree.command(name="michael_saves", description="Michael Saves the Day", guild=GUILD_ID)
    async def michael_saves(interaction: discord.Interaction):
        await interaction.response.send_message("Michael Saves the Day!", ephemeral=True)
        await interaction.followup.send("<a:jd:1395904586317041794>")

    @client.tree.command(name="join_voice", description="Join your current voice channel", guild=GUILD_ID)
    async def join_voice(interaction: discord.Interaction):
        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        # Get the user's voice channel
        voice_channel = interaction.user.voice.channel
        try:
            # Join the voice channel
            voice_client = await voice_channel.connect()
        except discord.ClientException:
            await interaction.response.send_message("❌ I'm already connected to a voice channel!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)

    @client.tree.command(name="leave_voice", description="Leave the current voice channel", guild=GUILD_ID)
    async def leave_voice(interaction: discord.Interaction):
        # Check if bot is connected to voice
        if interaction.guild.voice_client is None:
            await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)
            return
        # Disconnect from voice
        await interaction.guild.voice_client.disconnect()

    @client.tree.command(name="play_michael", description="Play the Michael Saves audio file", guild=GUILD_ID)
    async def play_michael(interaction: discord.Interaction):
        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        # Check if bot is connected to voice
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            try:
                voice_client = await interaction.user.voice.channel.connect()
            except discord.Forbidden:
                await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
                return
        
        # Look for Michael audio files (try WAV first, then MP3)
        possible_files = ["audio/Michael.wav", "audio/Michael.mp3"]
        sound_path = None
        for file_path in possible_files:
            if os.path.exists(file_path):
                sound_path = file_path
                break
        if not sound_path:
            await interaction.response.send_message("❌ Michael audio file not found!", ephemeral=True)
            return
        # Stop any currently playing audio
        if voice_client.is_playing():
            voice_client.stop()
        # Play the Michael audio
        try:
            # Use Opus encoding as required by Discord
            source = discord.FFmpegOpusAudio(sound_path)
            voice_client.play(source, after=lambda e: print(f'Error: {e}') if e else None)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error playing audio: {str(e)}", ephemeral=True)
    # Run the bot with the provided token
    try:
        print("Starting Discord bot...")
        client.run(discord_token)
    except Exception as e:
        print(f"Error starting bot: {e}")
if __name__ == "__main__":
    main()