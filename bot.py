async def send_loop(self):
    """Main sending loop with smart rate limit handling"""
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
                    
                    # Normal delay between channels
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
                        
                    except discord.Forbidden:
                        logger.error(f"❌ Missing permissions in {channel_id[:8]}... - skipping")
                        self.last_sent[channel_id] = now
                        
                    except discord.HTTPException as e:
                        if e.code == 429:  # Rate limited
                            logger.warning(f"⚠️ Rate limited on {channel_id[:8]}... - skipping for now")
                            # DON'T wait - just skip and move on!
                            self.last_sent[channel_id] = now
                        elif e.code == 200000:  # Content blocked
                            logger.warning(f"⚠️ Content blocked in {channel_id[:8]}... - skipping")
                            self.last_sent[channel_id] = now
                        else:
                            logger.error(f"❌ Discord error {e.code} in {channel_id[:8]}... - skipping")
                            self.last_sent[channel_id] = now
                            
                    except Exception as e:
                        logger.error(f"❌ Unexpected error in {channel_id[:8]}...: {e} - skipping")
                        self.last_sent[channel_id] = now
                
                # Next run
                next_run = now + timedelta(hours=self.interval_hours)
                logger.info(f"🕒 Next batch at: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"💤 Sleeping for {self.interval_hours} hours...")
                await asyncio.sleep(self.interval_hours * 3600)
            else:
                # No channels to send, just wait
                logger.info(f"💤 No channels ready, sleeping {self.interval_hours} hours...")
                await asyncio.sleep(self.interval_hours * 3600)
                
        except Exception as e:
            logger.error(f"❌ Error in send loop: {e}")
            await asyncio.sleep(60)
