from dotenv import load_dotenv
import discord
from discord.ext import commands
import os
import asyncio

# Load environment variables
def configure():
    load_dotenv()

# Bot initialization
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Load all cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f"cogs.{cog_name}")
                print(f"Loaded cog: {cog_name}")
            except Exception as e:
                print(f"Failed to load cog '{cog_name}': {e}")

# Event handler for when the bot is ready
@bot.event
async def on_ready():
    print(f"Bot ist bereit! Eingeloggt als {bot.user}")
    try:
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands.")
    except Exception as error:
        print("Error while syncing commands: ", error)

# Main asynchronous entry point
async def main():
    configure()  # Load environment variables
    await load_cogs()  # Load all cogs
    await bot.start(os.getenv("TOKEN"))  # Get the Discord Bot Token from .env file and start the bot

# Run the bot
if __name__ == "__main__":
    asyncio.run(main())
