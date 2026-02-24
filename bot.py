import discord
import asyncio
import random
import logging
from discord.ext import commands

# === KONFIGURACIJA ===
TOKEN = "YOUR_TOKEN_HERE"  # Įvesk savo token

# Tavo kanalai ir žinutės
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

# === LOG NUSTATYMAI ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === BOT SETUP - discrd.py-self ===
intents = discord.Intents.all()  # Self-bot reikia visų intentų
bot = commands.Bot(command_prefix='!', intents=intents, self_bot=True)  # self_bot=True svarbu!

# === FUNKCIJOS ===

async def send_to_channel(channel_id, message_text):
    """Siunčia žinutę į kanalą"""
    try:
        channel = bot.get_channel(int(channel_id))
        
        if not channel:
            # Bandome gauti kanalą per fetch
            try:
                channel = await bot.fetch_channel(int(channel_id))
            except:
                logger.error(f"❌ Nerastas kanalas: {channel_id}")
                return False
        
        # Siunčiam žinutę
        await channel.send(message_text)
        logger.info(f"✅ Išsiųsta į {channel_id}")
        return True
        
    except discord.Forbidden:
        logger.error(f"❌ Nėra leidimo siųsti į {channel_id}")
        return False
    except discord.NotFound:
        logger.error(f"❌ Kanalas neegzistuoja: {channel_id}")
        return False
    except discord.HTTPException as e:
        if e.status == 429:  # Rate limit
            retry_after = e.retry_after
            logger.warning(f"⚠️ Rate limit {channel_id}. Laukiu {retry_after}s")
            await asyncio.sleep(retry_after + 2)
        else:
            logger.error(f"❌ Klaida {channel_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Netikėta klaida {channel_id}: {e}")
        return False

async def send_all_messages():
    """Siunčia žinutes į visus kanalus"""
    logger.info("📨 Pradedu siųsti žinutes")
    
    # Sumaišom kanalus
    channels_copy = CHANNELS.copy()
    random.shuffle(channels_copy)
    
    successful = 0
    failed = 0
    
    for i, channel_data in enumerate(channels_copy):
        channel_id = channel_data["channel_id"]
        message_text = channel_data["message"]
        
        logger.info(f"📤 [{i+1}/{len(channels_copy)}] Siunčiu į {channel_id}")
        
        if await send_to_channel(channel_id, message_text):
            successful += 1
        else:
            failed += 1
        
        # Laukiam prieš kitą kanalą
        if i < len(channels_copy) - 1:
            wait_time = random.randint(240, 480)  # 4-8 min
            logger.info(f"⏱️ Laukiu {wait_time}s prieš kitą kanalą...")
            
            # Laukim mažais gabaliukais
            for _ in range(wait_time // 10):
                await asyncio.sleep(10)
    
    logger.info(f"📊 Rezultatai: {successful} sėkmingi, {failed} nepavyko")
    return successful, failed

# === TASKS ===

@tasks.loop(hours=2)
async def scheduled_messages():
    """Kas 2 valandas"""
    logger.info("🕐 Pradedu ciklą")
    await send_all_messages()
    logger.info("✅ Ciklas baigtas")

# === EVENTS ===

@bot.event
async def on_ready():
    logger.info(f"✅ Bot prisijungė kaip {bot.user.name}")
    logger.info(f"📊 Stebiu {len(CHANNELS)} kanalų")
    logger.info(f"⏰ Intervalas: 2 valandos")
    
    # Paleidžiam scheduler
    if not scheduled_messages.is_running():
        scheduled_messages.start()
        logger.info("✅ Scheduler paleistas")

@bot.event
async def on_message(message):
    # Atsako tik į komandas
    if message.content.startswith('!status'):
        await message.channel.send(f"✅ Bot veikia!\n📊 Kanalų: {len(CHANNELS)}\n⏰ Intervalas: 2 val.")
    
    if message.content.startswith('!sendnow'):
        await message.channel.send("🔄 Pradedu rankinį siuntimą...")
        await send_all_messages()
        await message.channel.send("✅ Baigta!")
    
    # Important for self-bots: process commands
    await bot.process_commands(message)

# === MAIN ===

async def main():
    async with bot:
        await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot sustabdytas")
    except Exception as e:
        logger.error(f"💥 Klaida: {e}")
