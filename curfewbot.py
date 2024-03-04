import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
from datetime import datetime, timedelta  # Add this import
import pytz
import pandas as pd
import csv
from decouple import config

intents = discord.Intents.default()
intents.voice_states = True

csv_filename = "kicked_users.csv"
kicked_usernames = []  # Define kicked_usernames as a global list

# Define a dictionary to store the scheduled tasks for each user
scheduled_tasks = {}

# Create the CSV file with header if it doesn't exist
with open(csv_filename, "w", newline="") as csvfile:
    csv_writer = csv.writer(csvfile)
    csv_writer.writerow(["User", "Allow"])

TOKEN = config('BOT_TOKEN')
GUILD_ID = 848474364562243615  # Replace with your Guild ID

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    await bot.change_presence(status=discord.Status.offline)
    
    # Fetch the guild by its ID
    global guild
    guild = bot.get_guild(GUILD_ID)
    
    with open(csv_filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["User", "Allow"])

@bot.command()
@commands.has_permissions(administrator=True)
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
    # Check if the user is already in the CSV file and update their curfew time
    df = pd.read_csv(csv_filename)
    if member.display_name in df['User'].values:
        df.loc[df['User'] == member.display_name, 'Allow'] = (curfew_datetime + timedelta(minutes=5)).strftime('%I:%M %p')
        df.to_csv(csv_filename, mode='w', header=True, index=False)
        await ctx.send(f"Updated curfew time for {member.display_name}.")
    else:
        await ctx.send(f"Curfew set for {curfew_time.strftime('%I:%M %p')} PST for {member.display_name}. I will disconnect them at that time.")
        # Add user info to the CSV file using pandas
        allow_time_str = (curfew_datetime + timedelta(minutes=5)).strftime('%I:%M %p')
        df = pd.DataFrame({"User": [member.display_name], "Allow": [allow_time_str]})
        
    # Update the global kicked_usernames list
    global kicked_usernames
    kicked_usernames.append(member.display_name)
    
    # Schedule the task to kick the user and store it in the dictionary
    scheduled_task = asyncio.create_task(kick_after_delay(member, time_diff))
    scheduled_tasks[member.display_name] = scheduled_task
    
    # Call the reminder function for 5 minutes before curfew
    await schedule_reminder(member, curfew_datetime - timedelta(minutes=5))

async def kick_after_delay(member, delay):
    await asyncio.sleep(delay)
    await member.move_to(None)

# Reminder function to send a message and mention the user before curfew
async def schedule_reminder(member, remind_time):
    await asyncio.sleep((remind_time - datetime.now()).total_seconds())
    curfew_channel = discord.utils.get(member.guild.channels, name="curfew")
    if curfew_channel:
        await curfew_channel.send(f"{member.mention}, your curfew is in 5 minutes!")

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):

    # Cancel scheduled tasks and clear the dictionary
    for task in scheduled_tasks.values():
        task.cancel()
    scheduled_tasks.clear()
    
    # Clear the CSV file
    with open(csv_filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["User", "Allow"])
        
    await ctx.send("Reset completed.")

    
@bot.event
async def on_voice_state_update(member, before, after):
    # Load the CSV file into a pandas DataFrame
    df = pd.read_csv(csv_filename)
    
    # Define the Pacific Time Zone
    pacific_timezone = pytz.timezone('US/Pacific')
    if after.channel and after.channel != before.channel:
        if member.display_name in kicked_usernames:
            with open(csv_filename, "r", newline="") as csvfile:
                csv_reader = csv.reader(csvfile)
                header = next(csv_reader)  # Read and store the header row

                updated_rows = []
                now = datetime.now(pacific_timezone)
                should_update_csv = False
                
                for row in csv_reader:
                    user, allow_time_str = row
                    if allow_time_str != 'Allow':  # Skip the header row
                        allow_time = datetime.strptime(allow_time_str, '%I:%M %p').time()
                        if member.display_name == user and now.time() < allow_time:
                            # Kick user and send "SHAME" message
                            await asyncio.gather(
                                member.move_to(None),
                                send_shame_message(member)
                            )
                            should_update_csv = False
                        else:
                            print("Here 2")
                            if member.display_name != user:
                                updated_rows.append(row) 
                            should_update_csv = True
                            
            if should_update_csv:                
                # Update the DataFrame with updated rows
                df_updated = pd.DataFrame(updated_rows, columns=df.columns)
                print("DataFrame:", df_updated)
                
                # Rewrite the CSV file with updated DataFrame
                df_updated.to_csv(csv_filename, mode='w', index=False)

async def send_shame_message(member):
    general_channel = discord.utils.get(member.guild.channels, name="general")
    if general_channel:
        await general_channel.send(f"SHAME {member.mention}")

bot.run(TOKEN)