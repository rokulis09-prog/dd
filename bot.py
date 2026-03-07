import requests
import time
import random
import json
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DirectAPIBot:
    def __init__(self):
        self.token = os.environ.get('DISCORD_TOKEN')
        self.interval_hours = float(os.environ.get('INTERVAL_HOURS', '2'))
        self.min_delay = int(os.environ.get('MIN_DELAY', '30'))
        self.max_delay = int(os.environ.get('MAX_DELAY', '90'))
        
        # Load channels
        channels_json = os.environ.get('CHANNELS', '[]')
        self.channels = json.loads(channels_json)
        logger.info(f"✅ Loaded {len(self.channels)} channels")
        
        # Image handling
        self.images_path = "/app/images"
        self.available_images = self.scan_images()
        
        self.last_sent = {}
        self.base_url = "https://discord.com/api/v9"
    
    def scan_images(self):
        """Scan the images folder and return list of available images"""
        image_dir = Path(self.images_path)
        
        logger.info(f"🔍 Looking for images in: {image_dir.absolute()}")
        
        if not image_dir.exists():
            logger.warning(f"⚠️ Image directory {self.images_path} not found!")
            return []
        
        # Get all image files
        extensions = ['*.jpg', '*.jpeg', '*.png', '*.gif', '*.webp']
        images = []
        for ext in extensions:
            images.extend(image_dir.glob(ext))
        
        logger.info(f"✅ Found {len(images)} images in volume")
        if images:
            logger.info(f"📸 Images: {[img.name for img in images]}")
        
        return list(images)
    
    def send_image(self, channel_id, image_name):
        """TIKSRAI siunčia nuotrauką"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        
        # Find image
        image_path = None
        for img in self.available_images:
            if image_name == img.name or image_name in img.name:
                image_path = img
                break
        
        if not image_path:
            logger.error(f"❌ Nerastas failas: {image_name}")
            return False
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, 'image/webp')}
                headers = {'Authorization': self.token}
                
                response = requests.post(url, headers=headers, files=files)
                
                if response.status_code == 200:
                    logger.info(f"🖼️✅ PAVEIKSLĖLIS IŠSIŲSTAS į {channel_id[:8]}... ({image_path.name})")
                    return True
                elif response.status_code == 429:
                    logger.warning(f"⚠️ Rate limit {channel_id[:8]}... skip")
                    return False
                else:
                    logger.error(f"❌ Klaida {response.status_code}")
                    return False
        except Exception as e:
            logger.error(f"❌ Klaida siunčiant: {e}")
            return False
    
    def run_forever(self):
        """Pagrindinis ciklas"""
        logger.info("🚀 Bot paleistas - SIIUNČIA NUOTRAUKAS")
        
        while True:
            now = datetime.now()
            
            for channel in self.channels:
                channel_id = channel['channel_id']
                
                # Check if we should send
                if channel_id in self.last_sent:
                    last = self.last_sent[channel_id]
                    hours_since = (now - last).total_seconds() / 3600
                    if hours_since < self.interval_hours:
                        continue
                
                # Random delay
                delay = random.randint(self.min_delay, self.max_delay)
                logger.info(f"⏱️ Laukiam {delay}s...")
                time.sleep(delay)
                
                # Send based on type
                msg_type = channel.get("type", "text")
                
                if msg_type == "image":
                    image_name = channel.get("image", "")
                    if image_name:
                        self.send_image(channel_id, image_name)
                    else:
                        logger.error(f"❌ Nenurodytas paveikslėlis kanalui {channel_id[:8]}...")
                else:
                    logger.info(f"💬 Tekstinis kanalas {channel_id[:8]}... - praleidžiam")
                
                self.last_sent[channel_id] = now
            
            # Next batch
            next_run = now + timedelta(hours=self.interval_hours)
            logger.info(f"🕒 Kitas ciklas: {next_run.strftime('%H:%M:%S')}")
            logger.info(f"💤 Miegam {self.interval_hours} val...")
            time.sleep(self.interval_hours * 3600)

if __name__ == "__main__":
    bot = DirectAPIBot()
    bot.run_forever()
