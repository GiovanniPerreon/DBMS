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
  console.log(`Logged in as ${client.user.tag}`);
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
    console.log(`Listening to ${user ? user.username : userId}`);

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
      console.log(`Stopped listening to ${user ? user.username : userId}`);
      if (audioChunks.length === 0) {
        console.log('No audio chunks received.');
        return;
      }
      console.log(`Received ${audioChunks.length} PCM audio chunks.`);
      let totalBytes = 0;
      audioChunks.forEach((chunk, idx) => {
        totalBytes += chunk.length;
      });
      console.log(`Total PCM audio bytes: ${totalBytes}`);
      // Use project root for audio and stt.py
      const projectRoot = path.resolve(__dirname, '..');
      const audioDir = path.join(projectRoot, 'audio');
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
        console.log(`WAV file saved: ${outFile}`);
        // Call Python STT script from pybot folder at project root
        const { spawn } = require('child_process');
        const sttPath = path.join(projectRoot, 'pybot', 'stt.py');
        const py = spawn('python', [sttPath, outFile]);
        py.stdout.on('data', (data) => {
          console.log(`STT: ${data.toString().trim()}`);
        });
        py.stderr.on('data', (data) => {
          console.error(`STT error: ${data.toString().trim()}`);
        });
        py.on('close', (code) => {
          // Delete all files starting with 'voice_' in the audio directory after STT completes
          fs.readdir(audioDir, (err, files) => {
            if (err) return;
            files.forEach(file => {
              if (file.startsWith('voice_')) {
                fs.unlink(path.join(audioDir, file), err => {
                  if (err) console.error(`Error deleting file: ${file}`);
                });
              }
            });
          });
        });
      });
    });
  });

  console.log('👂 Joined voice channel and listening!');
});

client.login(TOKEN);
