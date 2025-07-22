import discord
from discord.ext import commands
from discord import app_commands
import os
from discord import SelectOption
import subprocess
from utils import signal_js_leave, is_js_mode

class JSListener:
    def __init__(self, js_path=None):
        if js_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
            js_path = os.path.join(project_root, "bot", "listener.js")
        self.js_path = js_path

    def listen(self, voice_channel_id):
        try:
            subprocess.Popen([
                "node", self.js_path, str(voice_channel_id)
            ])
        except Exception as e:
            print(f"Error running JS listen: {e}")

def setup_commands(client, GUILD_ID):
    # signal_js_leave is now imported at the top of the file
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
        # Signal listener.js to leave by writing a leave signal file
        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        leave_signal_path = os.path.join(project_root, "bot", "leave_signal.txt")
        try:
            with open(leave_signal_path, "w", encoding="utf-8") as f:
                f.write("leave")
            print("Leave signal written for listener.js")
        except Exception as e:
            print(f"Error writing leave signal: {e}")

        # Try to disconnect Python bot if connected
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("✅ Left the voice channel! (Python & JS bots signaled)", ephemeral=True)
        else:
            await interaction.response.send_message("✅ Requested all bots to leave the voice channel! (JS bot signaled)", ephemeral=True)

    @client.tree.command(name="play_song", description="Choose and play a song from the available list", guild=GUILD_ID)
    async def play_song(interaction: discord.Interaction):
        # Always signal JS bot to leave before playing soundboard
        if is_js_mode():
            signal_js_leave()
        
        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        
        # Get available audio files
        # Always use the audio directory at the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        audio_dir = os.path.join(project_root, "audio")
        
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
                # Use the audio directory at the project root
                project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
                sound_path = os.path.join(project_root, "audio", selected_file)
                
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

    @client.tree.command(name="quick_sound", description="Quick access to popular soundboard sounds", guild=GUILD_ID)
    async def quick_sound(interaction: discord.Interaction):
        # Only signal JS bot to leave and disconnect if in JS mode
        if is_js_mode():
            signal_js_leave()
        
        """Quick dropdown menu for popular soundboard sounds"""
        # Check if user is in a voice channel
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        
        try:
            # Get soundboard sounds from the guild
            sounds = await interaction.guild.fetch_soundboard_sounds()
            
            if not sounds:
                await interaction.response.send_message("❌ No soundboard sounds found in this server!", ephemeral=True)
                return
            
            # Create dropdown menu for soundboard sounds
            class SoundboardSelect(discord.ui.Select):
                def __init__(self, available_sounds, voice_channel):
                    self.available_sounds = available_sounds
                    self.voice_channel = voice_channel
                    options = []
                    for sound in available_sounds[:25]:  # Discord limit is 25 options
                        options.append(SelectOption(
                            label=sound.name[:100],  # Discord label limit
                            description=f"Play {sound.name}"[:100],  # Discord description limit
                            value=str(sound.id),
                            emoji="🔊"
                        ))
                    super().__init__(placeholder="Choose a soundboard sound...", options=options)
                
                async def callback(self, interaction: discord.Interaction):
                    sound_id = int(self.values[0])
                    
                    # Check if bot is connected to voice, if not, connect
                    voice_client = interaction.guild.voice_client
                    if voice_client is None:
                        try:
                            voice_client = await self.voice_channel.connect()
                        except discord.Forbidden:
                            await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
                            return
                    
                    try:
                        # Find the sound object
                        sound = next((s for s in self.available_sounds if s.id == sound_id), None)
                        if sound is None:
                            await interaction.response.send_message("❌ Sound not found!", ephemeral=True)
                            return
                        
                        # Send the soundboard sound to the voice channel
                        await self.voice_channel.send_sound(sound)
                        await interaction.response.send_message(f"🔊 Playing: **{sound.name}**", ephemeral=True)
                        
                    except discord.HTTPException as e:
                        await interaction.response.send_message(f"❌ Failed to play soundboard: {str(e)}", ephemeral=True)
                    except Exception as e:
                        await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)
            
            class SoundboardView(discord.ui.View):
                def __init__(self, available_sounds, voice_channel):
                    super().__init__(timeout=60)
                    self.add_item(SoundboardSelect(available_sounds, voice_channel))
                
                async def on_timeout(self):
                    for item in self.children:
                        item.disabled = True
            
            voice_channel = interaction.user.voice.channel
            view = SoundboardView(sounds, voice_channel)
            await interaction.response.send_message("🔊 **Choose a soundboard sound:**", view=view, ephemeral=True)
            
        except discord.HTTPException as e:
            await interaction.response.send_message(f"❌ Failed to fetch soundboard sounds: {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error: {str(e)}", ephemeral=True)

    @client.tree.command(name="dm_user", description="Send a direct message to a user", guild=GUILD_ID)
    async def dm_user(interaction: discord.Interaction, user: discord.Member, message: str):
        """Send a DM to a specific user"""
        try:
            await user.send(f"{message}")
            await interaction.response.send_message(f"✅ Message sent!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message(f"❌ Cannot send DM to {user.display_name}. They may have DMs disabled.", ephemeral=True)
            print(f"❌ DM failed - {user.display_name} has DMs disabled")
        except Exception as e:
            await interaction.response.send_message(f"❌ Error sending message: {str(e)}", ephemeral=True)
            print(f"❌ DM failed with error: {str(e)}")

    # --- Add listen command at the end of setup_commands ---
    @client.tree.command(name="listen", description="Start Python voice listener in your voice channel", guild=GUILD_ID)
    async def listen(interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        # Connect to voice with VoiceRecvClient and start listening
        from discord.ext.voice_recv import VoiceRecvClient
        from voice_listener import MyAudioSink
        voice_channel = interaction.user.voice.channel
        voice_client = await voice_channel.connect(cls=VoiceRecvClient)
        sink = MyAudioSink()
        voice_client.listen(sink)
        await interaction.response.send_message(f"🔊 Listening to voice channel: {voice_channel.name}", ephemeral=True)

    @client.tree.command(name="loop_song", description="Choose a song to play in a loop", guild=GUILD_ID)
    async def loop_song(interaction: discord.Interaction):
        # Signal JS bot to leave before looping song
        if is_js_mode():
            signal_js_leave()
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
        audio_dir = os.path.join(project_root, "audio")
        if not os.path.exists(audio_dir):
            await interaction.response.send_message("❌ Audio directory not found!", ephemeral=True)
            return

        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        audio_files = [f for f in os.listdir(audio_dir) if any(f.lower().endswith(ext) for ext in audio_extensions)]
        if not audio_files:
            await interaction.response.send_message("❌ No audio files found in the audio directory!", ephemeral=True)
            return

        class LoopSongSelect(discord.ui.Select):
            def __init__(self):
                options = []
                for i, file in enumerate(audio_files[:25]):
                    display_name = os.path.splitext(file)[0]
                    options.append(SelectOption(
                        label=display_name,
                        description=f"Loop {display_name}",
                        value=file
                    ))
                super().__init__(placeholder="Choose a song to loop...", options=options)

            async def callback(self, interaction: discord.Interaction):
                selected_file = self.values[0]
                voice_client = interaction.guild.voice_client
                if voice_client is None:
                    try:
                        voice_client = await interaction.user.voice.channel.connect()
                    except discord.Forbidden:
                        await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
                        return

                sound_path = os.path.join(project_root, "audio", selected_file)

                def after_play(e=None):
                    if e:
                        print(f'Error: {e}')
                    if voice_client and voice_client.is_connected():
                        source = discord.FFmpegOpusAudio(sound_path)
                        voice_client.play(source, after=after_play)

                if voice_client.is_playing():
                    voice_client.stop()

                try:
                    source = discord.FFmpegOpusAudio(sound_path)
                    voice_client.play(source, after=after_play)
                    display_name = os.path.splitext(selected_file)[0]
                    await interaction.response.send_message(f"🔁 Now looping: **{display_name}**", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error playing audio: {str(e)}", ephemeral=True)

        class LoopSongView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.add_item(LoopSongSelect())
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True

        view = LoopSongView()
        await interaction.response.send_message("🔁 **Choose a song to loop:**", view=view, ephemeral=True)
