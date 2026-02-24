import discord
import asyncio
import os
import random
import json
from discord.ext import commands, tasks
import logging

# === CONFIGURATION ===
TOKEN = "YOUR_BOT_TOKEN_HERE"  # Replace with your actual token

# Your channels and messages from the JSON you sent
CHANNELS = [
    {"channel_id": "790439605655699456", "message": "Lonely :("},
    {"channel_id": "790439743397560361", "message": "Meowwww"},
    {"channel_id": "790440385289388083", "message": "Haiiii"},
    {"channel_id": "862668376106205224", "message": "୨୧┇Name: Emilly ୨୧┇Gender: Female ୨୧┇Pronounce: She/her ୨୧┇Age:19 ୨୧┇Location: Europe ୨୧┇Sexuality: straight ୨୧┇Dms:open Only 18 and + ୨୧┇Interest: Gymmmm, watching anime in free time thats it :heart: ୨୧┇+my dog too"},
    {"channel_id": "990736816632102922", "message": "Dms opennnnn"},
    {"channel_id": "1431019158849720502", "message": "Dm LOOSERSSSS"},
    {"channel_id": "1431014605093732474", "message": "Dms opennn for now <3"},
    {"channel_id": "1411679869225406566", "message": "so hornyyyyyyyyyyyyy"},
    {"channel_id": "731254148678549595", "message": "Haiiiii againn"},
    {"channel_id": "701906138563870840", "message": "Meowwww..."},
    {"channel_id": "1457746011597439018", "message": "GRRRRRRRRRRR angryy"},
    {"channel_id": "1396545118684712990", "message": "୨୧┇Name: Emilly ୨୧┇Gender: Female ୨୧┇Pronounce: She/her ୨୧┇Age:19 ୨୧┇Location: Europe ୨୧┇Sexuality: straight ୨୧┇Dms:open Only 18 and + ୨୧┇Interest: Gymmmm, watching anime in free time thats it :heart: ୨୧┇+my dog too"},
    {"channel_id": "1455617646195114065", "message": "Dms opennnn :heart: for nowwwww"},
    {"channel_id": "1455996727390900297", "message": "୨୧┇Name: Emilly ୨୧┇Gender: Female ୨୧┇Pronounce: She/her ୨୧┇Age:19"},
    {"channel_id": "1271825597555019847", "message": "୨୧┇Name: Emilly ୨୧┇Gender: Female ୨୧┇Pronounce: She/her ୨୧┇Age:19 ୨୧┇Location: Europe ୨୧┇Sexuality: straight ୨୧┇Dms:open Only 18 and + ୨୧┇Interest: Gymmmm, watching anime in free time thats it :heart: ୨୧┇+my dog too"},
    {"channel_id": "1437599197577613312", "message": "୨୧┇Name: Emilly ୨୧┇Gender: Female ୨୧┇Pronounce: She/her ୨୧┇Age:19 ୨୧┇Location: Europe ୨୧┇Sexuality: straight ୨୧┇Dms:open Only 18 and + ୨୧┇Interest: Gymmmm, watching anime in free time thats it :heart: ୨୧┇+my dog too"},
    {"channel_id": "1471183318866198608", "message": "Im angry"},
    {"channel_id": "1463239385712558367", "message": "Dms opennn "},
    {"channel_id": "1457727461793206305", "message": "୨୧┇Name: Emilly ୨୧┇Gender: Female ୨୧┇Pronounce: She/her ୨୧┇Age:19 ୨୧┇Location: Europe ୨୧┇Sexuality: straight ୨୧┇Dms:open Only 18 and + ୨୧┇Interest: Gymmmm, watching anime in free time thats it :heart: ୨୧┇+my dog too"},
    {"channel_id": "931386111840907364", "message": "Meowwwwww"}
]

# === BOT SETUP ===
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === FUNCTIONS ===

async def send_to_channel(channel_id, message_text):
    """Send a message to a specific channel with rate limit handling"""
    channel = bot.get_channel(int(channel_id))
    
    if not channel:
        logger.error(f"❌ Channel not found: {channel_id}")
        return False
    
    try:
        await channel.send(message_text)
        logger.info(f"✅ Sent to {channel_id}")
        return True
        
    except discord.Forbidden:
        logger.error(f"❌ No permission to send in {channel_id}")
        return False
        
    except discord.NotFound:
        logger.error(f"❌ Channel not found (404): {channel_id}")
        return False
        
    except discord.HTTPException as e:
        if e.status == 429:  # Rate limited
            retry_after = e.retry_after
            logger.warning(f"⚠️ Rate limited on {channel_id}. Retry after {retry_after:.2f}s")
            
            if retry_after > 300:  # If more than 5 minutes, skip
                logger.warning(f"⏭️ Skipping {channel_id} (retry too long: {retry_after:.2f}s)")
                return False
            else:
                logger.info(f"💤 Waiting {retry_after + 2}s...")
                await asyncio.sleep(retry_after + 2)
                # Try one more time
                try:
                    await channel.send(message_text)
                    logger.info(f"✅ Sent to {channel_id} on retry")
                    return True
                except:
                    logger.error(f"❌ Failed again for {channel_id}")
                    return False
        else:
            logger.error(f"❌ HTTP error for {channel_id}: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Unexpected error for {channel_id}: {e}")
        return False

async def send_all_messages():
    """Send messages to all channels with proper delays between them"""
    logger.info("📨 Starting to send messages to all channels")
    
    # Shuffle channels to avoid always sending in same order
    channels_copy = CHANNELS.copy()
    random.shuffle(channels_copy)
    
    successful = 0
    failed = 0
    
    for i, channel_data in enumerate(channels_copy):
        channel_id = channel_data["channel_id"]
        message_text = channel_data["message"]
        
        logger.info(f"📤 [{i+1}/{len(channels_copy)}] Sending to {channel_id}")
        
        # Send the message
        if await send_to_channel(channel_id, message_text):
            successful += 1
        else:
            failed += 1
        
        # Wait before next channel (except for the last one)
        if i < len(channels_copy) - 1:
            # Random wait between 4-8 minutes (240-480 seconds)
            # This helps avoid rate limiting patterns
            wait_time = random.randint(280, 520)
            logger.info(f"⏱️ Waiting {wait_time}s before next channel...")
            
            # Break the wait into smaller chunks so we can check for bot shutdown
            for _ in range(wait_time // 10):
                await asyncio.sleep(10)
    
    logger.info(f"📊 Complete: {successful} successful, {failed} failed")
    return successful, failed

# === TASKS ===

@tasks.loop(hours=2)
async def scheduled_messages():
    """Run every 2 hours"""
    logger.info("🕐 Starting scheduled message cycle")
    await send_all_messages()
    logger.info("✅ Cycle complete, next run in 2 hours")

@tasks.loop(minutes=30)
async def health_check():
    """Simple health check every 30 minutes"""
    logger.info("💓 Bot is running...")

# === EVENTS ===

@bot.event
async def on_ready():
    logger.info(f"✅ Bot logged in as {bot.user.name}")
    logger.info(f"📊 Monitoring {len(CHANNELS)} channels")
    logger.info(f"⏰ Interval: 2.0 hours")
    
    # Start the scheduled messages if not already running
    if not scheduled_messages.is_running():
        scheduled_messages.start()
        logger.info("✅ Scheduled messages started")
    
    if not health_check.is_running():
        health_check.start()

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Simple commands
    if message.content.startswith('!status'):
        await message.channel.send(f"✅ Bot is running!\n📊 Channels: {len(CHANNELS)}\n⏰ Interval: 2 hours")
    
    if message.content.startswith('!sendnow'):
        await message.channel.send("🔄 Manually starting message cycle...")
        await send_all_messages()
        await message.channel.send("✅ Manual cycle complete!")
    
    await bot.process_commands(message)

# === MAIN ===

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
