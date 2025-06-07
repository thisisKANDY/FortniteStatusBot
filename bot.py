import discord
import os
import asyncio
import aiohttp
from discord.ext import tasks
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID"))
PATCH_CHANNEL_ID = int(os.getenv("PATCH_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

last_sent_patch_timestamp = None
last_server_status = None
last_status_sent_time = datetime.utcnow() - timedelta(minutes=31)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    check_fortnite_status.start()
    check_patch_notes.start()

@tasks.loop(minutes=5)
async def check_fortnite_status():
    global last_server_status, last_status_sent_time

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://status.epicgames.com/api/v2/status.json") as response:
                data = await response.json()
                current_status = data['status']['description']

        now = datetime.utcnow()
        if current_status != last_server_status and now - last_status_sent_time > timedelta(minutes=30):
            channel = bot.get_channel(STATUS_CHANNEL_ID)
            await channel.send(f"🔔 Fortnite server status changed: **{current_status.upper()}**")
            last_server_status = current_status
            last_status_sent_time = now

    except Exception as e:
        print(f"[ERROR] Fortnite status check failed: {e}")

@tasks.loop(minutes=10)
async def check_patch_notes():
    global last_sent_patch_timestamp

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://fortnite-api.com/v2/news/br") as response:
                data = await response.json()
                news = data.get("data", {}).get("image", None)
                timestamp = data.get("data", {}).get("lastModified", None)

                if news and timestamp:
                    patch_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

                    if not last_sent_patch_timestamp or patch_time > last_sent_patch_timestamp:
                        channel = bot.get_channel(PATCH_CHANNEL_ID)
                        embed = discord.Embed(
                            title="📢 New Fortnite Patch Note!",
                            description="New Battle Royale news has been released.",
                            color=0x00ff00,
                            timestamp=datetime.utcnow()
                        )
                        embed.set_image(url=news)
                        await channel.send(embed=embed)
                        last_sent_patch_timestamp = patch_time

    except Exception as e:
        print(f"[ERROR] Patch notes check failed: {e}")

bot.run(TOKEN)
