#!/bin/bash
echo "Installing Discord bot dependencies..."
pip install -r requirements.txt
echo "Setup complete! You can now run the bot with 'python main.py'"
echo "Don't forget to set your DISCORD_TOKEN and GUILD_ID in the Secrets tab!"
