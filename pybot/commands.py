from discord_commands import music_commands
from discord_commands import voice_commands
from discord_commands import admin_commands
from discord_commands import fun_commands
from discord_commands import gacha_commands
from discord_commands import battle_commands
def setup_commands(client, GUILD_ID):
    """Set up all slash commands for the bot by calling modular registration functions"""
    music_commands.register_music_commands(client, GUILD_ID)
    voice_commands.register_voice_commands(client, GUILD_ID)
    admin_commands.register_admin_commands(client, GUILD_ID)
    fun_commands.register_fun_commands(client, GUILD_ID)
    gacha_commands.register_gacha_commands(client, GUILD_ID)
    battle_commands.register_battle_commands(client, GUILD_ID)
