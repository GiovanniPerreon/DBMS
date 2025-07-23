# Music commands module

import discord
from discord.ext.voice_recv import VoiceRecvClient
import os
from discord import SelectOption

def register_music_commands(client, GUILD_ID):
    @client.tree.command(name="play_song", description="Choose and play a song from the available list", guild=GUILD_ID)
    async def play_song(interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
        audio_dir = os.path.join(project_root, "audio")
        if not os.path.exists(audio_dir):
            await interaction.response.send_message("❌ Audio directory not found!", ephemeral=True)
            return
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a', '.flac']
        audio_files = [f for f in os.listdir(audio_dir) if any(f.lower().endswith(ext) for ext in audio_extensions)]
        if not audio_files:
            await interaction.response.send_message("❌ No audio files found in the audio directory!", ephemeral=True)
            return
        class SongSelect(discord.ui.Select):
            def __init__(self):
                options = []
                for i, file in enumerate(audio_files[:25]):
                    display_name = os.path.splitext(file)[0]
                    options.append(SelectOption(
                        label=display_name,
                        description=f"Play {display_name}",
                        value=file
                    ))
                super().__init__(placeholder="Choose a song to play...", options=options)
            async def callback(self, interaction: discord.Interaction):
                selected_file = self.values[0]
                voice_client = interaction.guild.voice_client
                if voice_client is None:
                    try:
                        voice_client = await interaction.user.voice.channel.connect(cls=VoiceRecvClient)
                    except discord.Forbidden:
                        await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
                        return
                sound_path = os.path.join(audio_dir, selected_file)
                if voice_client.is_playing():
                    voice_client.stop()
                try:
                    source = discord.FFmpegOpusAudio(sound_path)
                    voice_client.play(source, after=lambda e: print(f'Error: {e}') if e else None)
                    display_name = os.path.splitext(selected_file)[0]
                    await interaction.response.send_message(f"🎵 Now playing: **{display_name}**", ephemeral=True)
                except Exception as e:
                    await interaction.response.send_message(f"❌ Error playing audio: {str(e)}", ephemeral=True)
        class SongView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.add_item(SongSelect())
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
        view = SongView()
        await interaction.response.send_message("🎵 **Choose a song to play:**", view=view, ephemeral=True)

    @client.tree.command(name="loop_song", description="Choose a song to play in a loop", guild=GUILD_ID)
    async def loop_song(interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
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
                        voice_client = await interaction.user.voice.channel.connect(cls=VoiceRecvClient)
                    except discord.Forbidden:
                        await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
                        return
                sound_path = os.path.join(audio_dir, selected_file)
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

    @client.tree.command(name="soundboard", description="Quick access to popular soundboard sounds", guild=GUILD_ID)
    async def soundboard(interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        try:
            sounds = await interaction.guild.fetch_soundboard_sounds()
            if not sounds:
                await interaction.response.send_message("❌ No soundboard sounds found in this server!", ephemeral=True)
                return
            class SoundboardSelect(discord.ui.Select):
                def __init__(self, available_sounds, voice_channel):
                    self.available_sounds = available_sounds
                    self.voice_channel = voice_channel
                    options = []
                    for sound in available_sounds[:25]:
                        options.append(SelectOption(
                            label=sound.name[:100],
                            description=f"Play {sound.name}"[:100],
                            value=str(sound.id),
                            emoji="🔊"
                        ))
                    super().__init__(placeholder="Choose a soundboard sound...", options=options)
                async def callback(self, interaction: discord.Interaction):
                    sound_id = int(self.values[0])
                    voice_client = interaction.guild.voice_client
                    if voice_client is None:
                        try:
                            voice_client = await self.voice_channel.connect(cls=VoiceRecvClient)
                        except discord.Forbidden:
                            await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)
                            return
                    try:
                        sound = next((s for s in self.available_sounds if s.id == sound_id), None)
                        if sound is None:
                            await interaction.response.send_message("❌ Sound not found!", ephemeral=True)
                            return
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
