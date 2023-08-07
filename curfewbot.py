import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta  # Add this import
import pytz

intents = discord.Intents.default()
intents.voice_states = True

TOKEN = 'MTEzODIyOTcxNDE4ODc3MTM0OA.G5wA5h.P7eVniwUcUOeKOLWkCVH-cMHPuxE5dAtUM97NQ'
GUILD_ID = 848474364562243615  # Replace with your Guild ID

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await bot.change_presence(status=discord.Status.offline)

@bot.command()
async def curfew(ctx, time_str: str, member: discord.Member):
    try:
        curfew_time = datetime.strptime(time_str, '%I:%M%p').time()
    except ValueError:
        await ctx.send("Invalid time format. Please use the format '1:00AM'.")
        return
    
    # Define the Pacific Time Zone
    pacific_timezone = pytz.timezone('US/Pacific')
    
    current_time = datetime.now(pacific_timezone).time()  # Get the current time in PST
    curfew_datetime = pacific_timezone.localize(datetime.combine(datetime.now(pacific_timezone).date(), curfew_time))
    
    if current_time > curfew_time:
        curfew_datetime += timedelta(days=1)
    
    time_diff = (curfew_datetime - datetime.now(pacific_timezone)).total_seconds()
    
    await ctx.send(f"Curfew set for {curfew_time.strftime('%I:%M%p')} PST for {member.display_name}. I will disconnect them at that time.")
    
    await asyncio.sleep(time_diff)
    await member.move_to(None)

bot.run(TOKEN)