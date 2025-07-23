# Voice commands module

import discord
from discord.ext.voice_recv import VoiceRecvClient

def register_voice_commands(client, GUILD_ID):
    @client.tree.command(name="join_voice", description="Join your current voice channel", guild=GUILD_ID)
    async def join_voice(interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        voice_channel = interaction.user.voice.channel
        try:
            voice_client = await voice_channel.connect(cls=VoiceRecvClient)
            await interaction.response.send_message(f"✅ Joined **{voice_channel.name}**!", ephemeral=True)
        except discord.ClientException:
            await interaction.response.send_message("❌ I'm already connected to a voice channel!", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ I don't have permission to join that voice channel!", ephemeral=True)

    @client.tree.command(name="leave_voice", description="Leave the current voice channel", guild=GUILD_ID)
    async def leave_voice(interaction: discord.Interaction):
        if interaction.guild.voice_client is not None:
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("✅ Left the voice channel!", ephemeral=True)

    @client.tree.command(name="listen", description="Start Python voice listener in your voice channel", guild=GUILD_ID)
    async def listen(interaction: discord.Interaction):
        if interaction.user.voice is None:
            await interaction.response.send_message("❌ You need to be in a voice channel first!", ephemeral=True)
            return
        from voice_listener import MyAudioSink
        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect(cls=VoiceRecvClient)
        sink = MyAudioSink()
        voice_client.listen(sink)
        await interaction.response.send_message(f"🔊 Listening to voice channel: {voice_channel.name}", ephemeral=True)
