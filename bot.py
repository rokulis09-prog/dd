# bot.py - Improved version with environment variable support
import discord
import asyncio
import json
import os
import random
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RailwayBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.token = os.environ.get('DISCORD_TOKEN')
        self.load_config()
        self.running = True
        
    def load_config(self):
        """Load configuration from environment variables"""
        # Get interval settings
        self.interval_hours = float(os.environ.get('INTERVAL_HOURS', '2'))
        self.min_delay = int(os.environ.get('MIN_DELAY', '60'))
        self.max_delay = int(os.environ.get('MAX_DELAY', '300'))
        
        # Get channels from JSON environment variable
        channels_json = os.environ.get('CHANNELS', '[]')
        try:
            self.channels = json.loads(channels_json)
            logger.info(f"✅ Loaded {len(self.channels)} channels from environment")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse CHANNELS JSON: {e}")
            self.channels = []
        
        # Track last sent times (in memory only)
        self.last_sent = {}
    
    async def on_ready(self):
        logger.info(f"✅ Bot logged in as {self.user}")
        logger.info(f"📊 Monitoring {len(self.channels)} channels")
        logger.info(f"⏰ Interval: {self.interval_hours} hours")
        
        if len(self.channels) == 0:
            logger.warning("⚠️ No channels configured! Add CHANNELS environment variable.")
        
        # Start the sending loop
        self.loop.create_task(self.send_loop())
    
    async def send_loop(self):
        """Main sending loop"""
        while True:
            try:
                now = datetime.now()
                channels_to_send = []
                
                # Check which channels need sending
                for channel_config in self.channels:
                    channel_id = channel_config["channel_id"]
                    
                    # Check if we should send
                    should_send = True
                    if channel_id in self.last_sent:
                        last = self.last_sent[channel_id]
                        hours_since = (now - last).total_seconds() / 3600
                        if hours_since < self.interval_hours:
                            should_send = False
                    
                    if should_send:
                        channels_to_send.append(channel_config)
                
                if channels_to_send:
                    logger.info(f"📨 Sending to {len(channels_to_send)} channels")
                    
                    # Randomize order
                    random.shuffle(channels_to_send)
                    
                    for i, channel_config in enumerate(channels_to_send, 1):
                        channel_id = channel_config["channel_id"]
                        message = channel_config["message"]
                        
                        # Random delay between channels
                        delay = random.randint(self.min_delay, self.max_delay)
                        logger.info(f"⏱️ Waiting {delay}s before next channel...")
                        await asyncio.sleep(delay)
                        
                        try:
                            channel = self.get_channel(int(channel_id))
                            if channel:
                                await channel.send(message)
                                logger.info(f"✅ Sent to {channel_id[:8]}...: {message[:30]}...")
                                self.last_sent[channel_id] = now
                            else:
                                logger.error(f"❌ Channel not found: {channel_id[:8]}...")
                        except Exception as e:
                            logger.error(f"❌ Error sending to {channel_id[:8]}...: {e}")
                
                # Calculate next run
                next_run = now + timedelta(hours=self.interval_hours)
                logger.info(f"🕒 Next batch at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"💤 Sleeping for {self.interval_hours} hours...")
                
                await asyncio.sleep(self.interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"❌ Error in send loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
    
    async def on_error(self, event, *args, **kwargs):
        logger.error(f"❌ Error in {event}: {args} {kwargs}")

def main():
    # Get token from environment variable
    token = os.environ.get('DISCORD_TOKEN')
    if not token:
        logger.error("❌ DISCORD_TOKEN environment variable not set!")
        return
    
    # Create and run bot
    bot = RailwayBot()
    bot.run(token)

if __name__ == "__main__":
    main()
