import requests
import time
import random
import json
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MessageBot:
    def __init__(self):
        self.token = os.environ.get('DISCORD_TOKEN')
        if not self.token:
            logger.error("❌ NĖRA TOKEN! Pridėk DISCORD_TOKEN į variables")
            return
            
        self.interval_hours = float(os.environ.get('INTERVAL_HOURS', '2'))
        self.min_delay = int(os.environ.get('MIN_DELAY', '60'))
        self.max_delay = int(os.environ.get('MAX_DELAY', '180'))
        
        # Load channels
        channels_json = os.environ.get('CHANNELS', '[]')
        try:
            self.channels = json.loads(channels_json)
            logger.info(f"✅ Užkrauta {len(self.channels)} kanalų")
        except:
            logger.error("❌ KLAIDA skaitant CHANNELS")
            self.channels = []
        
        self.last_sent = {}
        self.headers = {'Authorization': self.token}
        self.base_url = "https://discord.com/api/v9"
    
    def send_message(self, channel_id, message):
        """Siunčia žinutę - jei klaida, skipina"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        data = {'content': message}
        
        try:
            response = requests.post(url, headers=self.headers, json=data)
            
            if response.status_code == 200:
                logger.info(f"✅ Išsiųsta į {channel_id[:8]}...")
                return True
            elif response.status_code == 403:
                logger.warning(f"⚠️ Negaliu rašyti į {channel_id[:8]}... (403) - skip")
                return False
            elif response.status_code == 429:
                logger.warning(f"⚠️ Rate limit {channel_id[:8]}... - skip")
                return False
            else:
                logger.warning(f"⚠️ Klaida {response.status_code} į {channel_id[:8]}... - skip")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Exception siunčiant į {channel_id[:8]}...: {e} - skip")
            return False
    
    def run(self):
        logger.info("🚀 BOT STARTED - TIK ŽINUTĖS, JOKIŲ NUOTRAUKŲ")
        logger.info(f"📊 Monitoring {len(self.channels)} kanalų")
        
        while True:
            now = datetime.now()
            
            # Randomize channel order
            random.shuffle(self.channels)
            
            for channel in self.channels:
                channel_id = channel['channel_id']
                message = channel['message']
                
                # Check if we already sent recently
                if channel_id in self.last_sent:
                    last = self.last_sent[channel_id]
                    hours_since = (now - last).total_seconds() / 3600
                    if hours_since < self.interval_hours:
                        continue
                
                # Random delay between channels
                delay = random.randint(self.min_delay, self.max_delay)
                logger.info(f"⏱️ Laukiam {delay}s prieš {channel_id[:8]}...")
                time.sleep(delay)
                
                # Send message (skip if fails)
                success = self.send_message(channel_id, message)
                
                # Mark as sent regardless (so we don't retry same channel in this cycle)
                self.last_sent[channel_id] = now
            
            # Next batch
            next_run = now + timedelta(hours=self.interval_hours)
            logger.info(f"🕒 Kitas ciklas: {next_run.strftime('%H:%M:%S')}")
            logger.info(f"💤 Miegam {self.interval_hours} val...")
            time.sleep(self.interval_hours * 3600)

if __name__ == "__main__":
    bot = MessageBot()
    bot.run()
