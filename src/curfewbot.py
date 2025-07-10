import discord
from discord.ext import commands, tasks
from discord.utils import get
import asyncio
from datetime import datetime, timedelta
import pytz
import sqlite3
import logging
from decouple import config
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.voice_states = True

# Database setup
DB_NAME = "curfew_bot.db"

# Define a dictionary to store the scheduled tasks for each user
scheduled_tasks = {}

TOKEN = config('BOT_TOKEN')
GUILD_ID = int(config('GUILD_ID', default='848474364562243615'))

bot = commands.Bot(command_prefix='!', intents=intents)

def init_database():
    """Initialize the SQLite database with required tables"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # Create curfews table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS curfews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                curfew_time TEXT NOT NULL,
                allow_time TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_name)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")

def add_or_update_curfew(user_name, user_id, curfew_time, allow_time):
    """Add or update a curfew in the database"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO curfews (user_name, user_id, curfew_time, allow_time)
            VALUES (?, ?, ?, ?)
        ''', (user_name, user_id, curfew_time, allow_time))
        
        conn.commit()
        conn.close()
        logger.info(f"Curfew updated for {user_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating curfew for {user_name}: {e}")
        return False

def get_user_curfew(user_name):
    """Get a user's curfew information"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM curfews WHERE user_name = ?', (user_name,))
        result = cursor.fetchone()
        
        conn.close()
        return result
    except Exception as e:
        logger.error(f"Error getting curfew for {user_name}: {e}")
        return None

def remove_user_curfew(user_name):
    """Remove a user's curfew from the database"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM curfews WHERE user_name = ?', (user_name,))
        
        conn.commit()
        conn.close()
        logger.info(f"Curfew removed for {user_name}")
        return True
    except Exception as e:
        logger.error(f"Error removing curfew for {user_name}: {e}")
        return False

def get_all_curfews():
    """Get all active curfews"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM curfews')
        results = cursor.fetchall()
        
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error getting all curfews: {e}")
        return []

def clear_all_curfews():
    """Clear all curfews from the database"""
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM curfews')
        
        conn.commit()
        conn.close()
        logger.info("All curfews cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing curfews: {e}")
        return False

@bot.event
async def on_ready():
    logger.info(f'Bot logged in as {bot.user}')
    await bot.change_presence(status=discord.Status.online)
    
    # Initialize database
    init_database()
    
    # Fetch the guild by its ID
    global guild
    guild = bot.get_guild(GUILD_ID)
    if guild:
        logger.info(f'Connected to guild: {guild.name}')
    else:
        logger.error(f'Could not find guild with ID: {GUILD_ID}')

@bot.command()
@commands.has_permissions(administrator=True)
async def curfew(ctx, time_str: str, member: discord.Member):
    """Set a curfew for a user"""
    try:
        # Parse the time string
        try:
            curfew_time = datetime.strptime(time_str, '%I:%M%p').time()
        except ValueError:
            try:
                curfew_time = datetime.strptime(time_str, '%I:%M %p').time()
            except ValueError:
                await ctx.send("Invalid time format. Please use '1:00AM' or '1:00 AM'.")
                return
        
        # Define the Pacific Time Zone
        pacific_timezone = pytz.timezone('US/Pacific')
        
        current_time = datetime.now(pacific_timezone).time()
        curfew_datetime = pacific_timezone.localize(
            datetime.combine(datetime.now(pacific_timezone).date(), curfew_time)
        )
        
        # If the curfew time has already passed today, set it for tomorrow
        if current_time > curfew_time:
            curfew_datetime += timedelta(days=1)
        
        time_diff = (curfew_datetime - datetime.now(pacific_timezone)).total_seconds()
        
        # Calculate allow time (5 minutes after curfew)
        allow_datetime = curfew_datetime + timedelta(minutes=5)
        allow_time_str = allow_datetime.strftime('%I:%M %p')
        curfew_time_str = curfew_datetime.strftime('%I:%M %p')
        
        # Cancel existing task if user already has a curfew
        if member.display_name in scheduled_tasks:
            scheduled_tasks[member.display_name].cancel()
            logger.info(f"Cancelled existing curfew task for {member.display_name}")
        
        # Add or update curfew in database
        success = add_or_update_curfew(
            member.display_name, 
            member.id, 
            curfew_time_str, 
            allow_time_str
        )
        
        if not success:
            await ctx.send("Error setting curfew. Please try again.")
            return
        
        # Schedule the task to kick the user
        scheduled_task = asyncio.create_task(kick_after_delay(member, time_diff))
        scheduled_tasks[member.display_name] = scheduled_task
        
        # Schedule reminder (5 minutes before curfew)
        reminder_delay = max(0, time_diff - 300)  # 300 seconds = 5 minutes
        if reminder_delay > 0:
            asyncio.create_task(schedule_reminder(member, reminder_delay))
        
        await ctx.send(f"✅ Curfew set for {member.display_name} at {curfew_time_str} PST. "
                      f"They can rejoin voice channels at {allow_time_str}.")
        
        logger.info(f"Curfew set for {member.display_name} at {curfew_time_str}")
        
    except Exception as e:
        logger.error(f"Error in curfew command: {e}")
        await ctx.send("An error occurred while setting the curfew. Please try again.")

async def kick_after_delay(member, delay):
    """Kick user from voice channel after delay"""
    try:
        await asyncio.sleep(delay)
        if member.voice and member.voice.channel:
            await member.move_to(None)
            logger.info(f"Kicked {member.display_name} from voice channel")
        
        # Remove from scheduled tasks
        if member.display_name in scheduled_tasks:
            del scheduled_tasks[member.display_name]
            
    except Exception as e:
        logger.error(f"Error kicking {member.display_name}: {e}")

async def schedule_reminder(member, delay):
    """Send reminder before curfew"""
    try:
        await asyncio.sleep(delay)
        
        # Find curfew channel or use general
        curfew_channel = discord.utils.get(member.guild.channels, name="curfew")
        if not curfew_channel:
            curfew_channel = discord.utils.get(member.guild.channels, name="general")
        
        if curfew_channel:
            embed = discord.Embed(
                title="⏰ Curfew Reminder",
                description=f"{member.mention}, your curfew is in 5 minutes!",
                color=discord.Color.orange()
            )
            await curfew_channel.send(embed=embed)
            logger.info(f"Sent curfew reminder to {member.display_name}")
            
    except Exception as e:
        logger.error(f"Error sending reminder to {member.display_name}: {e}")

@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    """Reset all curfews"""
    try:
        # Cancel all scheduled tasks
        for task in scheduled_tasks.values():
            task.cancel()
        scheduled_tasks.clear()
        
        # Clear database
        success = clear_all_curfews()
        
        if success:
            await ctx.send("✅ All curfews have been reset.")
            logger.info("All curfews reset by admin")
        else:
            await ctx.send("❌ Error resetting curfews. Please try again.")
            
    except Exception as e:
        logger.error(f"Error in reset command: {e}")
        await ctx.send("An error occurred while resetting curfews.")

@bot.command()
@commands.has_permissions(administrator=True)
async def list_curfews(ctx):
    """List all active curfews"""
    try:
        curfews = get_all_curfews()
        
        if not curfews:
            await ctx.send("No active curfews.")
            return
        
        embed = discord.Embed(
            title="📋 Active Curfews",
            color=discord.Color.blue()
        )
        
        for curfew in curfews:
            user_name, curfew_time, allow_time = curfew[1], curfew[3], curfew[4]
            embed.add_field(
                name=user_name,
                value=f"Curfew: {curfew_time}\nAllow: {allow_time}",
                inline=True
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        logger.error(f"Error in list_curfews command: {e}")
        await ctx.send("An error occurred while listing curfews.")

@bot.command()
@commands.has_permissions(administrator=True)
async def remove_curfew(ctx, member: discord.Member):
    """Remove a specific user's curfew"""
    try:
        # Cancel scheduled task if exists
        if member.display_name in scheduled_tasks:
            scheduled_tasks[member.display_name].cancel()
            del scheduled_tasks[member.display_name]
        
        # Remove from database
        success = remove_user_curfew(member.display_name)
        
        if success:
            await ctx.send(f"✅ Curfew removed for {member.display_name}.")
            logger.info(f"Curfew removed for {member.display_name}")
        else:
            await ctx.send(f"❌ No curfew found for {member.display_name}.")
            
    except Exception as e:
        logger.error(f"Error in remove_curfew command: {e}")
        await ctx.send("An error occurred while removing the curfew.")

@bot.event
async def on_voice_state_update(member, before, after):
    """Handle voice state updates to enforce curfews"""
    try:
        # Only process if user joined a voice channel
        if not (after.channel and after.channel != before.channel):
            return
        
        # Get user's curfew info
        curfew_info = get_user_curfew(member.display_name)
        if not curfew_info:
            return
        
        # Parse allow time
        allow_time_str = curfew_info[4]  # allow_time column
        pacific_timezone = pytz.timezone('US/Pacific')
        current_time = datetime.now(pacific_timezone)
        
        try:
            allow_time = datetime.strptime(allow_time_str, '%I:%M %p').time()
            
            # Check if current time is before allow time
            if current_time.time() < allow_time:
                # Kick user and send shame message
                await member.move_to(None)
                await send_shame_message(member)
                logger.info(f"Kicked {member.display_name} for violating curfew")
            else:
                # Curfew period is over, remove from database
                remove_user_curfew(member.display_name)
                logger.info(f"Curfew expired for {member.display_name}, removed from database")
                
        except ValueError as e:
            logger.error(f"Error parsing allow time for {member.display_name}: {e}")
            
    except Exception as e:
        logger.error(f"Error in voice state update for {member.display_name}: {e}")

async def send_shame_message(member):
    """Send shame message when user violates curfew"""
    try:
        general_channel = discord.utils.get(member.guild.channels, name="general")
        if general_channel:
            embed = discord.Embed(
                title="🔔 SHAME",
                description=f"{member.mention} tried to join voice chat during their curfew!",
                color=discord.Color.red()
            )
            await general_channel.send(embed=embed)
            
    except Exception as e:
        logger.error(f"Error sending shame message for {member.display_name}: {e}")

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle bot errors"""
    logger.error(f"Bot error in {event}: {args}")

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors"""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ User not found. Please mention a valid user.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Missing required arguments. Use `!help` for command usage.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send("❌ An error occurred while processing the command.")

if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
