import discord
from discord.ext import commands
from discord import app_commands
import os
from discord import SelectOption

def setup_commands(client, GUILD_ID):
    """Set up all slash commands for the bot"""
    
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
            await interaction.response.send_message(f"✅ Joined **{voice_channel.name}**!", ephemeral=True)
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
                    
                    # Remove file extension for display
                    display_name = os.path.splitext(selected_file)[0]
                    await interaction.response.send_message(f"🎵 Now playing: **{display_name}**", ephemeral=True)
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

    @client.tree.command(name="stop_music", description="Stop currently playing music", guild=GUILD_ID)
    async def stop_music(interaction: discord.Interaction):
        # Check if bot is connected to voice
        if interaction.guild.voice_client is None:
            await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)
            return
        
        voice_client = interaction.guild.voice_client
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("⏹️ Stopped the music!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ No music is currently playing!", ephemeral=True)

    @client.tree.command(name="list_songs", description="Show all available songs", guild=GUILD_ID)
    async def list_songs(interaction: discord.Interaction):
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
                display_name = os.path.splitext(file)[0]
                audio_files.append(display_name)
        
        if not audio_files:
            await interaction.response.send_message("❌ No audio files found in the audio directory!", ephemeral=True)
            return
        
        # Create a formatted list
        song_list = "🎵 **Available Songs:**\n\n"
        for i, song in enumerate(audio_files, 1):
            song_list += f"{i}. {song}\n"
        
        # Split into chunks if too long (Discord has a 2000 character limit)
        if len(song_list) > 2000:
            song_list = song_list[:1950] + "\n... and more!"
        
        await interaction.response.send_message(song_list, ephemeral=True)