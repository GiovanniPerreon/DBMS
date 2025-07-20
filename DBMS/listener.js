// Discord voice listener: minimal version

const { Client, GatewayIntentBits } = require('discord.js');
const { joinVoiceChannel, EndBehaviorType } = require('@discordjs/voice');
const prism = require('prism-media');
require('dotenv').config();
const fs = require('fs');
const path = require('path');
const wav = require('wav');

const TOKEN = process.env.DISCORD_TOKEN;
const GUILD_ID = process.env.GUILD_ID;
const VOICE_CHANNEL_ID = process.argv[2];

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildVoiceStates,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent
  ]
});

client.on('ready', async () => {
  // Bot is ready
  const guild = client.guilds.cache.get(GUILD_ID);
  if (!guild) {
    console.error('Guild not found!');
    return;
  }
  let voiceChannel;
  try {
    voiceChannel = await guild.channels.fetch(VOICE_CHANNEL_ID);
  } catch (err) {
    console.error('Voice channel not found!', err);
    return;
  }
  const connection = joinVoiceChannel({
    channelId: voiceChannel.id,
    guildId: guild.id,
    adapterCreator: guild.voiceAdapterCreator,
    selfMute: false,
    selfDeaf: false
  });

  const receiver = connection.receiver;
  receiver.speaking.on('start', (userId) => {
    const user = client.users.cache.get(userId);
    // Start listening to user

    const opusStream = receiver.subscribe(userId, {
      end: {
        behavior: EndBehaviorType.AfterInactivity,
        duration: 100 // ms of silence before ending
      }
    });

    // Decode Opus to PCM using prism-media
    const pcmStream = new prism.opus.Decoder({
      rate: 48000,
      channels: 1,
      frameSize: 960
    });
    opusStream.pipe(pcmStream);

    // Buffer PCM chunks
    const audioChunks = [];
    pcmStream.on('data', (chunk) => {
      audioChunks.push(chunk);
    });

    pcmStream.on('end', async () => {
      // Stop listening to user
      if (audioChunks.length === 0) {
        // No audio received
        return;
      }
      const audioDir = path.join(__dirname, 'audio');
      if (!fs.existsSync(audioDir)) {
        fs.mkdirSync(audioDir);
      }
      const outFile = path.join(audioDir, `voice_${userId}_${Date.now()}.wav`);

      // Save PCM chunks as WAV file
      const writer = new wav.FileWriter(outFile, {
        channels: 1,
        sampleRate: 48000,
        bitDepth: 16
      });
      for (const chunk of audioChunks) {
        writer.write(chunk);
      }
      writer.end();

      writer.on('finish', async () => {
        // Call Python STT script
        const { spawn } = require('child_process');
        const py = spawn('python', [path.join(__dirname, 'stt.py'), outFile]);
        py.stdout.on('data', (data) => {
          console.log(data.toString().trim());
        });
        py.stderr.on('data', (data) => {
          console.error(data.toString().trim());
        });
        py.on('close', (code) => {
          // Delete all temp files starting with 'voice_' after STT completes
          const audioDir = path.join(__dirname, 'audio');
          fs.readdir(audioDir, (err, files) => {
            if (err) return console.error(`Error reading audio dir: ${audioDir}`);
            files.forEach(file => {
              if (file.startsWith('voice_')) {
                fs.unlink(path.join(audioDir, file), (err) => {
                  if (err) console.error(`Error deleting file: ${file}`);
                  else console.log(`Deleted temp file: ${file}`);
                });
              }
            });
          });
        });
      });
    });
  });

  // Joined voice channel
});

client.login(TOKEN);
