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

class RailwayBot(discord.Client):
    def __init__(self):
        super().__init__()
        self.token = os.environ.get('DISCORD_TOKEN')
        self.images_path = "/app/images"
        self.available_images = self.scan_images()
        self.load_config()
        self.last_sent = {}
        self.running = True
        
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
    
    async def send_image_to_channel(self, channel_id, specific_image=None):
        """Send an image to a specific channel"""
        try:
            channel = self.get_channel(int(channel_id))
            if not channel:
                logger.error(f"❌ Channel not found: {channel_id[:8]}...")
                return False
            
            if not self.available_images:
                logger.error("❌ No images found in volume!")
                return False
            
            image_path = None
            if specific_image:
                for img in self.available_images:
                    if specific_image in img or img.endswith(specific_image):
                        image_path = img
                        break
                
                if not image_path:
                    logger.error(f"❌ Image '{specific_image}' not found")
                    return False
            else:
                image_path = random.choice(self.available_images)
            
            filename = os.path.basename(image_path)
            with open(image_path, 'rb') as f:
                await channel.send(file=discord.File(f, filename=filename))
            
            logger.info(f"✅ Image sent to {channel_id[:8]}... ({filename})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error sending image: {e}")
            return False
    
    async def on_ready(self):
        logger.info(f"✅ Bot logged in as {self.user}")
        logger.info(f"📊 Monitoring {len(self.channels)} channels")
        logger.info(f"🖼️ {len(self.available_images)} images available")
        logger.info(f"⏰ Interval: {self.interval_hours} hours")
        logger.info(f"⏱️ Delays: {self.min_delay}-{self.max_delay} seconds")
        
        self.loop.create_task(self.send_loop())
    
    async def send_loop(self):
        """Main sending loop with image support - FIXED VERSION"""
        while self.running:
            try:
                now = datetime.now()
                channels_to_send = []
                
                # Check which channels need sending
                for channel_config in self.channels:
                    channel_id = channel_config["channel_id"]
                    
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
                    random.shuffle(channels_to_send)
                    
                    for channel_config in channels_to_send:
                        channel_id = channel_config["channel_id"]
                        
                        delay = random.randint(self.min_delay, self.max_delay)
                        logger.info(f"⏱️ Waiting {delay}s before next channel...")
                        await asyncio.sleep(delay)
                        
                        try:
                            channel = self.get_channel(int(channel_id))
                            if not channel:
                                logger.error(f"❌ Channel not found: {channel_id[:8]}...")
                                continue
                            
                            msg_type = channel_config.get("type", "text")
                            
                            if msg_type == "text":
                                await channel.send(channel_config["message"])
                                logger.info(f"✅ Text sent to {channel_id[:8]}...")
                                
                            elif msg_type == "image":
                                image_name = channel_config.get("image", None)
                                await self.send_image_to_channel(channel_id, image_name)
                                
                            elif msg_type == "mixed":
                                await channel.send(channel_config["message"])
                                await self.send_image_to_channel(channel_id)
                            
                            self.last_sent[channel_id] = now
                            
                        except discord.Forbidden as e:
                            logger.error(f"❌ Missing permissions in {channel_id[:8]}...: {e}")
                            # Still mark as sent to avoid constant retries
                            self.last_sent[channel_id] = now
                            
                        except discord.HTTPException as e:
                            logger.error(f"❌ Discord error in {channel_id[:8]}...: {e.code} - {e.text}")
                            # Mark as sent to avoid getting stuck
                            self.last_sent[channel_id] = now
                            
                        except Exception as e:
                            logger.error(f"❌ Unexpected error in {channel_id[:8]}...: {e}")
                            # Still mark as sent to avoid infinite loop
                            self.last_sent[channel_id] = now
                
                # Next run
                next_run = now + timedelta(hours=self.interval_hours)
                logger.info(f"🕒 Next batch at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"💤 Sleeping for {self.interval_hours} hours...")
                await asyncio.sleep(self.interval_hours * 3600)
                
            except Exception as e:
                logger.error(f"❌ Error in send loop: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(60)  # Wait a minute before restarting loop
    
    def stop(self):
        self.running = False
        self.loop.call_soon_threadsafe(self.loop.stop)
    
    def run_bot(self):
        try:
            self.run(self.token)
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            logger.error(traceback.format_exc())

def main():
    bot = RailwayBot()
    bot.run_bot()

if __name__ == "__main__":
    main()
