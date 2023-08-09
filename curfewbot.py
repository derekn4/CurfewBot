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
    
    await ctx.send(f"Curfew set for {curfew_time.strftime('%I:%M %p')} PST for {member.display_name}. I will disconnect them at that time.")
    
    # Format the allow_time using the specified format
    allow_time_str = (curfew_datetime + timedelta(minutes=5)).strftime('%I:%M %p')
    
    # Add user info to the CSV file using pandas
    df = pd.DataFrame({"User": [member.display_name], "Allow": [allow_time_str]})
    df.to_csv(csv_filename, mode='a', header=False, index=False)
        
    # Update the global kicked_usernames list
    global kicked_usernames
    kicked_usernames.append(member.display_name)
    
    await asyncio.sleep(time_diff)
    await member.move_to(None)
    
@bot.command()
async def allcurfew(ctx, time_str: str):
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
    
    await ctx.send(f"Curfew set for {curfew_time.strftime('%I:%M %p')} PST for the regulars. I will disconnect them at that time.")
    
    # Format the allow_time using the specified format
    allow_time_str = (curfew_datetime + timedelta(minutes=5)).strftime('%I:%M %p')
    
    usernames = ["totallyhweee", "jucotastic", "brbhungry", "darrents", "sapphirearabian", "teberp", "weselton", "henrythekoala"]
    members = []
    # Loop through the username strings and convert them to discord.Member objects
    for username in usernames:
        member = get(guild.members, display_name=username)
        if member:
            members.append(member)
    
    # Create a list of dictionaries for each member and their allow time
    data = [{"User": member.display_name, "Allow": allow_time_str} for member in members]
    
    # Create a DataFrame from the list of dictionaries
    df = pd.DataFrame(data)
    
    # Append the DataFrame to the CSV file
    df.to_csv(csv_filename, mode='a', header=False, index=False)
            
            
    # Update the global kicked_usernames list
    global kicked_usernames
    kicked_usernames.extend(member.display_name for member in members)
    
    await asyncio.sleep(time_diff)
    
    # Loop through the members list and kick them from the voice channel
    for member in members:
        await member.move_to(None)
    
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
                                #send_shame_message(member)
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