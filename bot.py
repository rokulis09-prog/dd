import requests
import time
import random
import json
import os
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DirectAPIBot:
    def __init__(self):
        self.token = os.environ.get('DISCORD_TOKEN')
        self.interval_hours = float(os.environ.get('INTERVAL_HOURS', '2'))
        self.min_delay = int(os.environ.get('MIN_DELAY', '60'))
        self.max_delay = int(os.environ.get('MAX_DELAY', '300'))
        
        # Load channels
        channels_json = os.environ.get('CHANNELS', '[]')
        self.channels = json.loads(channels_json)
        logger.info(f"✅ Loaded {len(self.channels)} channels")
        
        self.last_sent = {}
        self.headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }
        self.base_url = "https://discord.com/api/v9"
    
    def send_message(self, channel_id, content):
        """Send message - NO AUTO RETRY, returns immediately"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        data = {'content': content}
        
        response = requests.post(url, headers=self.headers, json=data)
        
        if response.status_code == 200:
            logger.info(f"✅ Sent to {channel_id[:8]}...")
            return True
        elif response.status_code == 429:
            logger.warning(f"⚠️ Rate limited on {channel_id[:8]}... SKIPPING")
            return False  # We return immediately, don't wait!
        else:
            logger.error(f"❌ Error {response.status_code} on {channel_id[:8]}...")
            return False
    
    def run_forever(self):
        """Main loop - runs forever"""
        logger.info("🚀 Bot started - NO AUTO RETRIES")
        
        while True:
            now = datetime.now()
            
            # Randomize channel order
            channels_copy = self.channels.copy()
            random.shuffle(channels_copy)
            
            for channel in channels_copy:
                channel_id = channel['channel_id']
                
                # Check if we should send
                if channel_id in self.last_sent:
                    last = self.last_sent[channel_id]
                    hours_since = (now - last).total_seconds() / 3600
                    if hours_since < self.interval_hours:
                        continue
                
                # Delay between channels
                delay = random.randint(self.min_delay, self.max_delay)
                logger.info(f"⏱️ Waiting {delay}s...")
                time.sleep(delay)
                
                # Send message based on type
                msg_type = channel.get("type", "text")
                
                if msg_type == "text":
                    success = self.send_message(channel_id, channel['message'])
                elif msg_type == "image":
                    logger.info(f"🖼️ Image channel {channel_id[:8]}... - would send image here")
                    success = True  # Placeholder for now
                else:
                    success = self.send_message(channel_id, channel['message'])
                
                # Mark as sent regardless of outcome (so we don't retry same channel)
                self.last_sent[channel_id] = now
            
            # Next batch
            next_run = now + timedelta(hours=self.interval_hours)
            logger.info(f"🕒 Next batch at: {next_run.strftime('%H:%M:%S')}")
            logger.info(f"💤 Sleeping {self.interval_hours} hours...")
            time.sleep(self.interval_hours * 3600)

if __name__ == "__main__":
    bot = DirectAPIBot()
    bot.run_forever()
