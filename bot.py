import discord
import os
import random
import json
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom HTTP handler that doesn't retry on rate limits
from discord.http import HTTPClient

class NoRetryHTTPClient(HTTPClient):
    async def request(self, route, **kwargs):
        try:
            return await super().request(route, **kwargs)
        except discord.HTTPException as e:
            if e.code == 429:  # Rate limited
                logger.warning(f"⚠️ Rate limit hit - skipping")
                raise  # Re-raise so we catch it in our code
            raise

class RailwayBot(discord.Client):
    def __init__(self):
        # Use custom HTTP client
        super().__init__()
        self.http = NoRetryHTTPClient()
        self.token = os.environ.get('DISCORD_TOKEN')
        self.images_path = "/app/images"
        self.available_images = self.scan_images()
        self.load_config()
        self.last_sent = {}
        self.running = True
        self.rate_limited_channels = {}  # Track rate limited channels
        
    def scan_images(self):
        """Scan the images folder and return list of available images"""
        image_dir = Path(self.images_path)
        if not image_dir.exists():
            logger.warning(f"⚠️ Image directory {self.images_path} not found!")
            return []
        
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
        images = []
        for ext in extensions:
            images.extend(image_dir.glob(ext))
            images.extend(image_dir.rglob(ext))
        
        logger.info(f"✅ Found {len(images)} images in volume")
        return [str(img) for img in images]
    
    def load_config(self):
        """Load configuration from environment variables"""
        self.interval_hours = float(os.environ.get('INTERVAL_HOURS', '2'))
        self.min_delay = int(os.environ.get('MIN_DELAY', '60'))
        self.max_delay = int(os.environ.get('MAX_DELAY', '300'))
        
        channels_json = os.environ.get('CHANNELS', '[]')
        try:
            self.channels = json.loads(channels_json)
            logger.info(f"✅ Loaded {len(self.channels)} channels from environment")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse CHANNELS JSON: {e}")
            self.channels = []
    
    async def send_message_without_retry(self, channel, content=None, file=None):
        """Send a message but catch rate limits immediately"""
        try:
            if file:
                await channel.send(file=file)
            else:
                await channel.send(content)
            return True
        except discord.HTTPException as e:
            if e.code == 429:  # Rate limited
                logger.warning(f"⚠️ Rate limit hit for {channel.id} - skipping")
                return False
            else:
                logger.error(f"❌ Discord error {e.code}: {e}")
                return False
    
    async def on_ready(self):
        logger.info(f"✅ Bot logged in as {self.user}")
        logger.info(f"📊 Monitoring {len(self.channels)} channels")
        logger.info(f"🖼️ {len(self.available_images)} images available")
        logger.info(f"⏰ Interval: {self.interval_hours} hours")
        logger.info(f"⏱️ Delays: {self.min_delay}-{self.max_delay} seconds")
        
        self.loop.create_task(self.send_loop())
    
    async def send_loop(self):
        """Simple loop that never waits on rate limits"""
        while self.running:
            try:
                now = datetime.now()
                
                # Shuffle channels for randomness
                channels_copy = self.channels.copy()
                random.shuffle(channels_copy)
                
                for channel_config in channels_copy:
                    channel_id = channel_config["channel_id"]
                    
                    # Check if we already sent to this channel recently
                    if channel_id in self.last_sent:
                        last = self.last_sent[channel_id]
                        hours_since = (now - last).total_seconds() / 3600
                        if hours_since < self.interval_hours:
                            continue
                    
                    # Random delay between channels
                    delay = random.randint(self.min_delay, self.max_delay)
                    logger.info(f"⏱️ Waiting {delay}s before next channel...")
                    await asyncio.sleep(delay)
                    
                    try:
                        channel = self.get_channel(int(channel_id))
                        if not channel:
                            logger.error(f"❌ Channel not found: {channel_id[:8]}...")
                            self.last_sent[channel_id] = now
                            continue
                        
                        msg_type = channel_config.get("type", "text")
                        
                        success = False
                        if msg_type == "text":
                            success = await self.send_message_without_retry(
                                channel, 
                                content=channel_config["message"]
                            )
                            
                        elif msg_type == "image":
                            image_name = channel_config.get("image", None)
                            # Find image
                            if image_name and self.available_images:
                                for img_path in self.available_images:
                                    if image_name in img_path:
                                        with open(img_path, 'rb') as f:
                                            file = discord.File(f, filename=image_name)
                                            success = await self.send_message_without_retry(
                                                channel, 
                                                file=file
                                            )
                                        break
                        
                        if success:
                            logger.info(f"✅ Sent to {channel_id[:8]}...")
                            self.last_sent[channel_id] = now
                        else:
                            logger.warning(f"⚠️ Failed to send to {channel_id[:8]}... - skipping")
                            self.last_sent[channel_id] = now
                            
                    except Exception as e:
                        logger.error(f"❌ Error: {e}")
                        self.last_sent[channel_id] = now
                
                # Next run
                next_run = now + timedelta(hours=self.interval_hours)
                logger.info(f"🕒 Next batch at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"💤 Sleeping for {self.interval_hours} hours...")
                await asyncio.sleep(self.interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"❌ Loop error: {e}")
                await asyncio.sleep(60)
    
    def stop(self):
        self.running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
    
    def run_bot(self):
        try:
            self.run(self.token)
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")

def main():
    bot = RailwayBot()
    bot.run_bot()

if __name__ == "__main__":
    main()
