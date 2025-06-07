import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import asyncio
import os
from dotenv import load_dotenv

# === Load Environment Variables ===
load_dotenv()
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID"))
PATCH_CHANNEL_ID = int(os.getenv("PATCH_CHANNEL_ID"))

intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents)
last_server_status = None
last_patch_title = None

@bot.event
async def on_ready():
    print(f"{bot.user} is now online and monitoring.")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Error syncing commands: {e}")
    check_fortnite_status.start()
    check_patch_notes.start()

@tasks.loop(minutes=15)
async def check_fortnite_status():
    global last_server_status
    async with aiohttp.ClientSession() as session:
        async with session.get('https://status.epicgames.com/api/v2/components.json') as resp:
            data = await resp.json()
            for component in data['components']:
                if component['name'] == "Fortnite":
                    current_status = component['status']
                    if current_status != last_server_status:
                        last_server_status = current_status
                        channel = bot.get_channel(STATUS_CHANNEL_ID)
                        if channel:
                            await channel.send(f"🔔 Fortnite server status changed: **{current_status.upper()}**")
                    break

@tasks.loop(minutes=15)
async def check_patch_notes():
    global last_patch_title
    async with aiohttp.ClientSession() as session:
        async with session.get('https://fortnite-api.com/v2/news/br') as resp:
            data = await resp.json()
            if data['status'] == 200:
                title = data['data']['motds'][0]['title']
                body = data['data']['motds'][0]['body']
                image = data['data']['motds'][0].get('image', '')

                if title != last_patch_title:
                    last_patch_title = title
                    embed = discord.Embed(title=title, description=body, color=0x1DA1F2)
                    if image:
                        embed.set_image(url=image)
                    channel = bot.get_channel(PATCH_CHANNEL_ID)
                    if channel:
                        await channel.send(embed=embed)

@bot.tree.command(name="serverstatus", description="Check the current Fortnite server status.")
async def server_status(interaction: discord.Interaction):
    async with aiohttp.ClientSession() as session:
        async with session.get('https://status.epicgames.com/api/v2/components.json') as resp:
            data = await resp.json()
            for component in data['components']:
                if component['name'] == "Fortnite":
                    status = component['status']
                    await interaction.response.send_message(f"🔍 Current Fortnite server status: **{status.upper()}**")
                    return

bot.run(DISCORD_BOT_TOKEN)
