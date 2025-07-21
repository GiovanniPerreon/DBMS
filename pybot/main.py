import discord
from discord.ext import commands
from discord import app_commands
import os
import threading
from keep_alive import keep_alive
from commands import setup_commands

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
    # Enable member intents to access user information for messaging
    intents.members = True
    # Enable presence intentons to see user status
    intents.presences = True
    
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
    # Setup all slash commands from the commands module
    setup_commands(client, GUILD_ID)
    
    # Run the bot with the provided token
    try:
        print("Starting Discord bot...")
        client.run(discord_token)
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()