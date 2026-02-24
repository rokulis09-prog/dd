# bot.py - Optimized for Railway hosting
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
        self.config = self.load_config()
        self.running = True
        
    def load_config(self):
        """Load configuration from environment or file"""
        # You can store your config in Railway variables
        # For now, we'll use a simple structure
        return {
            "channels": [
                # Add your channels here or use environment variables
                # Example format:
                # {"channel_id": "123456789", "message": "Hello!"}
            ],
            "interval_hours": float(os.environ.get('INTERVAL_HOURS', '2')),
            "min_delay": int(os.environ.get('MIN_DELAY', '60')),
            "max_delay": int(os.environ.get('MAX_DELAY', '300'))
        }
    
    async def on_ready(self):
        logger.info(f"✅ Bot logged in as {self.user}")
        logger.info(f"📊 Monitoring {len(self.config['channels'])} channels")
        logger.info(f"⏰ Interval: {self.config['interval_hours']} hours")
        
        # Start the sending loop
        self.loop.create_task(self.send_loop())
    
    async def send_loop(self):
        """Main sending loop"""
        while True:
            try:
                now = datetime.now()
                
                for channel_config in self.config["channels"]:
                    channel_id = channel_config["channel_id"]
                    message = channel_config["message"]
                    
                    # Random delay between channels
                    delay = random.randint(
                        self.config['min_delay'], 
                        self.config['max_delay']
                    )
                    logger.info(f"⏱️ Waiting {delay}s before next channel...")
                    await asyncio.sleep(delay)
                    
                    try:
                        channel = self.get_channel(int(channel_id))
                        if channel:
                            await channel.send(message)
                            logger.info(f"✅ Sent to {channel_id[:8]}...")
                        else:
                            logger.error(f"❌ Channel not found: {channel_id[:8]}...")
                    except Exception as e:
                        logger.error(f"❌ Error sending to {channel_id[:8]}...: {e}")
                
                # Next run
                next_run = now + timedelta(hours=self.config['interval_hours'])
                logger.info(f"🕒 Next batch at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"💤 Sleeping for {self.config['interval_hours']} hours...")
                
                await asyncio.sleep(self.config['interval_hours'] * 3600)
                
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