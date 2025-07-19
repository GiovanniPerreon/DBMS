import discord
from discord.ext import commands
from discord import app_commands
import os
import threading
from keep_alive import keep_alive

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
    """Main function to start the bot and keep-alive server"""
    # Start the keep-alive server in a separate thread
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    print("Keep-alive server started")
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

    @client.tree.command(name="play_song", description="Choose and play a song from the available list", guild=GUILD_ID)
    async def play_song(interaction: discord.Interaction):
        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        # Get available audio files
        script_dir = os.path.dirname(os.path.abspath(__file__))
        audio_dir = os.path.join(script_dir, "audio")
        if not os.path.exists(audio_dir):
            await interaction.response.send_message("❌ Audio directory not found!", ephemeral=True)
            return
        # Find all audio files
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        audio_files = []
        for file in os.listdir(audio_dir):
            if any(file.lower().endswith(ext) for ext in audio_extensions):
                audio_files.append(file)
        if not audio_files:
            await interaction.response.send_message("❌ No audio files found in the audio directory!", ephemeral=True)
            return
        # Create dropdown menu
        from discord import SelectOption
        
        class SongSelect(discord.ui.Select):
            def __init__(self):
                # Create options for each audio file (limit to 25 options max)
                options = []
                for i, file in enumerate(audio_files[:25]):  # Discord limit is 25 options
                    # Remove file extension for display
                    display_name = os.path.splitext(file)[0]
                    options.append(SelectOption(
                        label=display_name,
                        description=f"Play {display_name}",
                        value=file
                    ))
                super().__init__(placeholder="Choose a song to play...", options=options)
            async def callback(self, interaction: discord.Interaction):
                selected_file = self.values[0]
                # Check if bot is connected to voice
                voice_client = interaction.guild.voice_client
                if voice_client is None:
                    try:
                        voice_client = await interaction.user.voice.channel.connect()
                    except discord.Forbidden:
                        await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
                        return
                # Get full path to selected file
                script_dir = os.path.dirname(os.path.abspath(__file__))
                sound_path = os.path.join(script_dir, "audio", selected_file)
                # Stop any currently playing audio
                if voice_client.is_playing():
                    voice_client.stop()
                # Play the selected audio
                try:
                    source = discord.FFmpegOpusAudio(sound_path)
                    voice_client.play(source, after=lambda e: print(f'Error: {e}') if e else None)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error playing audio: {str(e)}", ephemeral=True)
        
        class SongView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)  # 60 second timeout
                self.add_item(SongSelect())
            
            async def on_timeout(self):
                # Disable the select menu when timeout occurs
                for item in self.children:
                    item.disabled = True
        
        view = SongView()
        await interaction.response.send_message("🎵 **Choose a song to play:**", view=view, ephemeral=True)
    # Run the bot with the provided token
    try:
        print("Starting Discord bot...")
        client.run(discord_token)
    except Exception as e:
        print(f"Error starting bot: {e}")
if __name__ == "__main__":
    main()