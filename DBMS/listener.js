// listener.js
// Auto-join a voice channel and listen for audio when started

const { Client, GatewayIntentBits } = require('discord.js');
const { joinVoiceChannel, EndBehaviorType } = require('@discordjs/voice');
require('dotenv').config();

const TOKEN = process.env.DISCORD_TOKEN;
const GUILD_ID = process.env.GUILD_ID;
const VOICE_CHANNEL_ID = process.argv[2]; // Passed from Python command

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

    const audioStream = receiver.subscribe(userId, {
      end: {
        behavior: EndBehaviorType.AfterSilence,
        duration: 100
      }
    });

    audioStream.on('data', (chunk) => {
      console.log(`Received audio chunk from ${user ? user.username : userId}: ${chunk.length} bytes`);
    });

    audioStream.on('end', () => {
      console.log(`Stopped listening to ${user ? user.username : userId}`);
    });
  });

  console.log('👂 Joined voice channel and listening!');
});

client.login(TOKEN);
