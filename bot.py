const { Client } = require('discord.js-selfbot-v13');
const fs = require('fs');
const path = require('path');

// Load config
const configPath = path.join(__dirname, 'config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));

console.log(`🚀 Loaded ${config.accounts.length} accounts`);

// Create clients for each account
const clients = [];

config.accounts.forEach((account, index) => {
    const client = new Client();
    client.accountIndex = index;
    client.accountData = account;
    
    client.on('ready', async () => {
        console.log(`✅ [Account ${index + 1}] Logged in as ${client.user.tag}`);
        
        // Start bump loops for each bot
        account.bots.forEach(botConfig => {
            botConfig.commands.forEach(cmd => {
                startBumpLoop(client, botConfig, cmd);
            });
        });
    });
    
    client.on('error', (error) => {
        console.log(`⚠️ [Account ${index + 1}] Error:`, error.message);
    });
    
    clients.push(client);
});

function startBumpLoop(client, botConfig, cmd) {
    const channelId = cmd.channelId;
    const commandName = cmd.command;
    const botId = botConfig.botId;
    const minInterval = (cmd.intervalMinutes - (cmd.intervalMinutes * (cmd.randomVariationPercent / 100))) * 60000;
    const maxInterval = (cmd.intervalMinutes + (cmd.intervalMinutes * (cmd.randomVariationPercent / 100))) * 60000;
    
    async function bump() {
        try {
            const channel = await client.channels.fetch(channelId).catch(() => null);
            if (!channel) {
                console.log(`❌ [${client.user?.tag}] Channel ${channelId} not found - skipping`);
                return;
            }
            
            await channel.sendSlash(botId, commandName);
            console.log(`✅ [${client.user?.tag}] Bumped in ${channelId}`);
        } catch (error) {
            // Skip on error - don't crash
            console.log(`⚠️ [${client.user?.tag}] Failed to bump ${channelId}: ${error.message} - skipping`);
        }
    }
    
    async function loop() {
        while (true) {
            await bump();
            
            // Random interval
            const interval = Math.floor(Math.random() * (maxInterval - minInterval + 1)) + minInterval;
            const nextBump = new Date(Date.now() + interval);
            console.log(`⏱️ [${client.user?.tag}] Next bump for ${channelId} at ${nextBump.toLocaleTimeString()}`);
            
            await new Promise(resolve => setTimeout(resolve, interval));
        }
    }
    
    loop();
}

// Login all accounts
config.accounts.forEach((account, index) => {
    clients[index].login(account.token).catch(error => {
        console.log(`❌ [Account ${index + 1}] Login failed:`, error.message);
    });
});

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n👋 Shutting down...');
    clients.forEach(client => client.destroy());
    process.exit();
});
