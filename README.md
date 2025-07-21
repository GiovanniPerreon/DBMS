# # Discord Bot - Michael Saves

A Discord bot that responds to messages and plays audio in voice channels.

## Features

- Responds to messages starting with "Michael" 
- Adds reactions to messages starting with "M"
- Voice channel commands: join, leave, play audio
- Slash commands for interaction

## Setup

1. **Install Dependencies**
   ```bash
   pip install discord.py flask pynacl ffmpeg-python
   ```

2. **Environment Variables**
   - Copy `.env.example` to `.env`
   - Fill in your Discord bot token and Guild ID:
   ```
   DISCORD_TOKEN=your_actual_bot_token
   GUILD_ID=your_actual_server_id
   ```

3. **Get Your Bot Token**
   - Go to https://discord.com/developers/applications
   - Create a new application or select existing one
   - Go to "Bot" section
   - Copy the token

4. **Get Your Guild ID**
   - Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
   - Right-click your server name
   - Click "Copy Server ID"

## Running the Bot

```bash
python main.py
```

## Commands

- `/michael_saves` - Michael Saves the Day!
- `/join_voice` - Join your current voice channel
- `/leave_voice` - Leave the current voice channel  
- `/play_michael` - Play the Michael Saves audio file

## Requirements

- Python 3.7+
- FFmpeg (for audio playback)
- Discord.py
- Flask (for keep-alive server)