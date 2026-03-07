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

class ImageBot:
    def __init__(self):
        self.token = os.environ.get('DISCORD_TOKEN')
        self.interval_hours = float(os.environ.get('INTERVAL_HOURS', '2'))
        self.min_delay = int(os.environ.get('MIN_DELAY', '30'))
        self.max_delay = int(os.environ.get('MAX_DELAY', '90'))
        
        # Load channels
        channels_json = os.environ.get('CHANNELS', '[]')
        self.channels = json.loads(channels_json)
        logger.info(f"✅ Loaded {len(self.channels)} channels")
        
        # Image path
        self.images_path = "/app/images"
        self.check_images()
        
        self.last_sent = {}
        self.headers = {'Authorization': self.token}
    
    def check_images(self):
        """Patikrinam ar yra nuotraukų"""
        path = Path(self.images_path)
        if not path.exists():
            logger.error(f"❌ Nerastas folderis: {self.images_path}")
            return
        
        files = list(path.glob("*"))
        logger.info(f"📂 Folderio turinys: {[f.name for f in files]}")
    
    def send_image(self, channel_id, image_name):
        """TIKRAI SIUNČIA NUOTRAUKĄ"""
        url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
        image_path = Path(self.images_path) / image_name
        
        if not image_path.exists():
            logger.error(f"❌ Nerastas failas: {image_path}")
            return False
        
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_name, f, 'image/webp')}
                response = requests.post(url, headers=self.headers, files=files)
                
                if response.status_code == 200:
                    logger.info(f"🖼️✅ NUOTRAUKA IŠSIŲSTA! {image_name} -> {channel_id[:8]}...")
                    return True
                elif response.status_code == 429:
                    logger.warning(f"⚠️ Rate limit {channel_id[:8]}... skip")
                    return False
                else:
                    logger.error(f"❌ Klaida {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"❌ Exception: {e}")
            return False
    
    def run(self):
        logger.info("🚀 BOT STARTED - TIKRAS NUOTRAUKŲ SIUNTIMAS")
        
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
                
                # Send image
                if channel.get("type") == "image":
                    image_name = channel.get("image", "")
                    if image_name:
                        self.send_image(channel_id, image_name)
                    else:
                        logger.error(f"❌ Nenurodytas failo pavadinimas")
                else:
                    logger.info(f"💬 Text channel - skip")
                
                self.last_sent[channel_id] = now
            
            # Next batch
            next_run = now + timedelta(hours=self.interval_hours)
            logger.info(f"🕒 Kitas ciklas: {next_run.strftime('%H:%M:%S')}")
            logger.info(f"💤 Miegam {self.interval_hours} val...")
            time.sleep(self.interval_hours * 3600)

if __name__ == "__main__":
    bot = ImageBot()
    bot.run()
