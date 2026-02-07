import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from aiohttp import web
import pytz
import sqlite3
import signal
import traceback
import logging
from decouple import config
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.voice_states = True
intents.message_content = True  # Required for prefix commands in discord.py 2.x

# Database setup — DB_DIR env var for Docker volume mount, falls back to script directory
DB_DIR = config('DB_DIR', default=os.path.dirname(os.path.abspath(__file__)))
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "curfew_bot.db")

PACIFIC_TZ = pytz.timezone('US/Pacific')

# Scheduled tasks keyed by member ID (int).
# Each value is a dict: {"kick": Task, "reminder": Task | None}
scheduled_tasks = {}

TOKEN = config('BOT_TOKEN')
GUILD_ID = int(config('GUILD_ID', default='848474364562243615'))
HEALTH_PORT = int(config('HEALTH_PORT', default='8080'))
HEALTH_HOST = config('HEALTH_HOST', default='127.0.0.1')

# Users exempt from curfews (by Discord user ID)
EXCLUDED_USERS = {427696914880790538}

bot = commands.Bot(command_prefix='!', intents=intents)

# Guard to prevent duplicate health server starts on reconnect
_health_server_started = False
_health_runner = None

# ---------------------------------------------------------------------------
# Database helpers — all use context managers to prevent connection leaks
# ---------------------------------------------------------------------------

def get_connection():
    """Get a SQLite connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize the SQLite database with required tables."""
    try:
        with get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS curfews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT NOT NULL,
                    user_id INTEGER NOT NULL UNIQUE,
                    curfew_time TEXT NOT NULL,
                    allow_time TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")


def add_or_update_curfew(user_name: str, user_id: int, curfew_time: str, allow_time: str) -> bool:
    """Add or update a curfew in the database. Keyed by user_id (immutable)."""
    try:
        with get_connection() as conn:
            conn.execute('''
                INSERT INTO curfews (user_name, user_id, curfew_time, allow_time)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    user_name = excluded.user_name,
                    curfew_time = excluded.curfew_time,
                    allow_time = excluded.allow_time
            ''', (user_name, user_id, curfew_time, allow_time))
        logger.info(f"Curfew updated for {user_name}")
        return True
    except Exception as e:
        logger.error(f"Error updating curfew for {user_name}: {e}")
        return False


def get_user_curfew(user_id: int):
    """Get a user's curfew information by their immutable user ID."""
    try:
        with get_connection() as conn:
            cursor = conn.execute('SELECT * FROM curfews WHERE user_id = ?', (user_id,))
            return cursor.fetchone()
    except Exception as e:
        logger.error(f"Error getting curfew for user {user_id}: {e}")
        return None


def remove_user_curfew(user_id: int) -> bool:
    """Remove a user's curfew from the database. Returns True only if a row was deleted."""
    try:
        with get_connection() as conn:
            cursor = conn.execute('DELETE FROM curfews WHERE user_id = ?', (user_id,))
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error removing curfew for user {user_id}: {e}")
        return False


def get_all_curfews():
    """Get all active curfews."""
    try:
        with get_connection() as conn:
            cursor = conn.execute('SELECT * FROM curfews')
            return cursor.fetchall()
    except Exception as e:
        logger.error(f"Error getting all curfews: {e}")
        return []


def clear_all_curfews() -> bool:
    """Clear all curfews from the database."""
    try:
        with get_connection() as conn:
            conn.execute('DELETE FROM curfews')
        logger.info("All curfews cleared")
        return True
    except Exception as e:
        logger.error(f"Error clearing curfews: {e}")
        return False

# ---------------------------------------------------------------------------
# Health check HTTP server
# ---------------------------------------------------------------------------

async def health_handler(request):
    """Return 200 if bot is connected to Discord, 503 otherwise."""
    if bot.is_ready():
        return web.Response(text="OK", status=200)
    return web.Response(text="Bot not ready", status=503)


async def start_health_server():
    """Start a lightweight HTTP health check server."""
    global _health_runner
    app = web.Application()
    app.router.add_get('/health', health_handler)
    _health_runner = web.AppRunner(app)
    await _health_runner.setup()
    site = web.TCPSite(_health_runner, HEALTH_HOST, HEALTH_PORT)
    await site.start()
    logger.info(f"Health check server started on {HEALTH_HOST}:{HEALTH_PORT}")

# ---------------------------------------------------------------------------
# Task scheduling helpers
# ---------------------------------------------------------------------------

def cancel_user_tasks(user_id: int):
    """Cancel all scheduled tasks (kick + reminder) for a user."""
    tasks = scheduled_tasks.pop(user_id, None)
    if tasks:
        for task in tasks.values():
            if task is not None:
                task.cancel()

# ---------------------------------------------------------------------------
# Bot events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    global _health_server_started

    logger.info(f'Bot logged in as {bot.user}')
    await bot.change_presence(status=discord.Status.online)

    init_database()

    target_guild = bot.get_guild(GUILD_ID)
    if target_guild:
        logger.info(f'Connected to guild: {target_guild.name}')
    else:
        logger.error(f'Could not find guild with ID: {GUILD_ID}')

    # Start health check server only once (on_ready fires on every reconnect)
    if not _health_server_started:
        await start_health_server()
        _health_server_started = True

    # Restore scheduled tasks from database for curfews that haven't expired
    await restore_curfews_from_db()


async def restore_curfews_from_db():
    """Re-schedule kick tasks for curfews persisted in the database."""
    curfews = get_all_curfews()
    now = datetime.now(PACIFIC_TZ)

    target_guild = bot.get_guild(GUILD_ID)
    if not target_guild:
        return

    for row in curfews:
        user_id = row['user_id']
        try:
            curfew_dt = datetime.fromisoformat(row['curfew_time'])
            allow_dt = datetime.fromisoformat(row['allow_time'])

            if curfew_dt.tzinfo is None:
                curfew_dt = PACIFIC_TZ.localize(curfew_dt)
            if allow_dt.tzinfo is None:
                allow_dt = PACIFIC_TZ.localize(allow_dt)

            # If the allow time has passed, curfew is expired — clean it up
            if now >= allow_dt:
                remove_user_curfew(user_id)
                logger.info(f"Cleaned up expired curfew for user {user_id}")
                continue

            member = target_guild.get_member(user_id)
            if not member:
                continue

            # If curfew is currently active, kick them if they're in voice
            if now >= curfew_dt and now < allow_dt:
                if member.voice and member.voice.channel:
                    await member.move_to(None)
                    logger.info(f"Kicked {member.display_name} from voice on startup (active curfew)")
                continue

            # If curfew time hasn't hit yet, schedule the kick
            if now < curfew_dt:
                time_diff = (curfew_dt - now).total_seconds()
                kick_task = asyncio.create_task(kick_after_delay(member, time_diff))

                reminder_delay = max(0, time_diff - 300)
                reminder_task = None
                if reminder_delay > 0:
                    reminder_task = asyncio.create_task(schedule_reminder(member, reminder_delay))

                scheduled_tasks[user_id] = {"kick": kick_task, "reminder": reminder_task}
                logger.info(f"Restored curfew schedule for {member.display_name}")

        except (ValueError, TypeError) as e:
            logger.error(f"Error restoring curfew for user {user_id}: {e}")

# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

@bot.command()
@commands.has_permissions(administrator=True)
async def curfew(ctx, time_str: str, member: discord.Member):
    """Set a curfew for a user."""
    try:
        if member.id in EXCLUDED_USERS:
            await ctx.send(f"{member.display_name} is excluded from curfews.")
            return

        # Parse the time string (supports "11:30PM" and "11:30 PM")
        parsed_time = None
        for fmt in ('%I:%M%p', '%I:%M %p'):
            try:
                parsed_time = datetime.strptime(time_str, fmt).time()
                break
            except ValueError:
                continue

        if parsed_time is None:
            await ctx.send("Invalid time format. Please use '11:30PM' or '11:30 PM'.")
            return

        now = datetime.now(PACIFIC_TZ)
        curfew_dt = PACIFIC_TZ.localize(datetime.combine(now.date(), parsed_time))

        # If the curfew time already passed today, schedule for tomorrow
        if curfew_dt <= now:
            curfew_dt += timedelta(days=1)

        time_diff = (curfew_dt - now).total_seconds()

        # Allow time = 5 minutes after curfew
        allow_dt = curfew_dt + timedelta(minutes=5)

        # Store full ISO datetimes so midnight-crossing comparisons work
        curfew_time_str = curfew_dt.isoformat()
        allow_time_str = allow_dt.isoformat()

        # Cancel existing tasks if user already has a curfew
        cancel_user_tasks(member.id)

        success = add_or_update_curfew(
            member.display_name,
            member.id,
            curfew_time_str,
            allow_time_str,
        )

        if not success:
            await ctx.send("Error setting curfew. Please try again.")
            return

        # Schedule the kick
        kick_task = asyncio.create_task(kick_after_delay(member, time_diff))

        # Schedule 5-minute reminder
        reminder_task = None
        reminder_delay = max(0, time_diff - 300)
        if reminder_delay > 0:
            reminder_task = asyncio.create_task(schedule_reminder(member, reminder_delay))

        scheduled_tasks[member.id] = {"kick": kick_task, "reminder": reminder_task}

        display_curfew = curfew_dt.strftime('%I:%M %p')
        display_allow = allow_dt.strftime('%I:%M %p')
        await ctx.send(
            f"Curfew set for {member.display_name} at {display_curfew} PST. "
            f"They can rejoin voice channels at {display_allow}."
        )
        logger.info(f"Curfew set for {member.display_name} at {display_curfew}")

    except Exception as e:
        logger.error(f"Error in curfew command: {e}")
        await ctx.send("An error occurred while setting the curfew. Please try again.")


async def kick_after_delay(member, delay):
    """Kick user from voice channel after delay."""
    try:
        await asyncio.sleep(delay)
        if member.voice and member.voice.channel:
            await member.move_to(None)
            logger.info(f"Kicked {member.display_name} from voice channel")

        scheduled_tasks.pop(member.id, None)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error kicking {member.display_name}: {e}")


async def schedule_reminder(member, delay):
    """Send reminder before curfew."""
    try:
        await asyncio.sleep(delay)

        curfew_channel = discord.utils.get(member.guild.channels, name="curfew")
        if not curfew_channel:
            curfew_channel = discord.utils.get(member.guild.channels, name="general")

        if curfew_channel:
            embed = discord.Embed(
                title="Curfew Reminder",
                description=f"{member.mention}, your curfew is in 5 minutes!",
                color=discord.Color.orange(),
            )
            await curfew_channel.send(embed=embed)
            logger.info(f"Sent curfew reminder to {member.display_name}")

    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.error(f"Error sending reminder to {member.display_name}: {e}")


@bot.command()
@commands.has_permissions(administrator=True)
async def reset(ctx):
    """Reset all curfews."""
    try:
        for tasks in scheduled_tasks.values():
            for task in tasks.values():
                if task is not None:
                    task.cancel()
        scheduled_tasks.clear()

        success = clear_all_curfews()

        if success:
            await ctx.send("All curfews have been reset.")
            logger.info("All curfews reset by admin")
        else:
            await ctx.send("Error resetting curfews. Please try again.")

    except Exception as e:
        logger.error(f"Error in reset command: {e}")
        await ctx.send("An error occurred while resetting curfews.")


@bot.command()
@commands.has_permissions(administrator=True)
async def list_curfews(ctx):
    """List all active curfews."""
    try:
        curfews = get_all_curfews()

        if not curfews:
            await ctx.send("No active curfews.")
            return

        embed = discord.Embed(title="Active Curfews", color=discord.Color.blue())

        for row in curfews:
            user_name = row['user_name']
            try:
                curfew_dt = datetime.fromisoformat(row['curfew_time'])
                allow_dt = datetime.fromisoformat(row['allow_time'])
                curfew_display = curfew_dt.strftime('%I:%M %p')
                allow_display = allow_dt.strftime('%I:%M %p')
            except (ValueError, TypeError):
                curfew_display = row['curfew_time']
                allow_display = row['allow_time']

            embed.add_field(
                name=user_name,
                value=f"Curfew: {curfew_display}\nAllow: {allow_display}",
                inline=True,
            )

        await ctx.send(embed=embed)

    except Exception as e:
        logger.error(f"Error in list_curfews command: {e}")
        await ctx.send("An error occurred while listing curfews.")


@bot.command()
@commands.has_permissions(administrator=True)
async def remove_curfew(ctx, member: discord.Member):
    """Remove a specific user's curfew."""
    try:
        cancel_user_tasks(member.id)

        success = remove_user_curfew(member.id)

        if success:
            await ctx.send(f"Curfew removed for {member.display_name}.")
            logger.info(f"Curfew removed for {member.display_name}")
        else:
            await ctx.send(f"No curfew found for {member.display_name}.")

    except Exception as e:
        logger.error(f"Error in remove_curfew command: {e}")
        await ctx.send("An error occurred while removing the curfew.")

# ---------------------------------------------------------------------------
# Voice state enforcement
# ---------------------------------------------------------------------------

@bot.event
async def on_voice_state_update(member, before, after):
    """Enforce curfews when users join voice channels."""
    try:
        # Only process if user joined a voice channel
        if not (after.channel and after.channel != before.channel):
            return

        curfew_info = get_user_curfew(member.id)
        if not curfew_info:
            return

        now = datetime.now(PACIFIC_TZ)

        try:
            # Parse full ISO datetimes — handles midnight crossing correctly
            curfew_dt = datetime.fromisoformat(curfew_info['curfew_time'])
            allow_dt = datetime.fromisoformat(curfew_info['allow_time'])
            if curfew_dt.tzinfo is None:
                curfew_dt = PACIFIC_TZ.localize(curfew_dt)
            if allow_dt.tzinfo is None:
                allow_dt = PACIFIC_TZ.localize(allow_dt)

            # Only enforce if curfew has started but allow time hasn't passed
            if now >= curfew_dt and now < allow_dt:
                await member.move_to(None)
                await send_shame_message(member)
                logger.info(f"Kicked {member.display_name} for violating curfew")
            else:
                remove_user_curfew(member.id)
                logger.info(f"Curfew expired for {member.display_name}, removed from database")

        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing allow time for {member.display_name}: {e}")

    except Exception as e:
        logger.error(f"Error in voice state update for {member.display_name}: {e}")


async def send_shame_message(member):
    """Send shame message when user violates curfew."""
    try:
        general_channel = discord.utils.get(member.guild.channels, name="general")
        if general_channel:
            embed = discord.Embed(
                title="SHAME",
                description=f"{member.mention} tried to join voice chat during their curfew!",
                color=discord.Color.red(),
            )
            await general_channel.send(embed=embed)

    except Exception as e:
        logger.error(f"Error sending shame message for {member.display_name}: {e}")

# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@bot.event
async def on_error(event, *args, **kwargs):
    """Handle bot errors."""
    logger.error(f"Bot error in {event}:\n{traceback.format_exc()}")


@bot.event
async def on_command_error(ctx, error):
    """Handle command errors."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("User not found. Please mention a valid user.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing required arguments. Use `!help` for command usage.")
    else:
        logger.error(f"Command error: {error}")
        await ctx.send("An error occurred while processing the command.")

# ---------------------------------------------------------------------------
# Graceful shutdown
# ---------------------------------------------------------------------------

async def shutdown():
    """Cleanly shut down the bot."""
    logger.info("Shutting down bot...")
    for tasks in scheduled_tasks.values():
        for task in tasks.values():
            if task is not None:
                task.cancel()
    scheduled_tasks.clear()

    if _health_runner:
        await _health_runner.cleanup()

    await bot.close()
    logger.info("Bot shut down complete")


def handle_signal(sig):
    """Handle OS signals for graceful shutdown (Unix only)."""
    logger.info(f"Received signal {sig.name}, initiating shutdown...")
    asyncio.create_task(shutdown())

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Register signal handlers for graceful shutdown (Unix)
        # On Windows, only SIGINT exists and is handled by KeyboardInterrupt below
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                loop.add_signal_handler(sig, handle_signal, sig)
            except (NotImplementedError, ValueError):
                # Windows: add_signal_handler not supported, SIGTERM doesn't exist
                # Ctrl+C is caught as KeyboardInterrupt instead
                pass

        loop.run_until_complete(bot.start(TOKEN))
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
        loop.run_until_complete(shutdown())
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
    finally:
        loop.close()
