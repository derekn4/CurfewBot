# CurfewBot Deployment Guide

This guide will help you deploy your improved CurfewBot to Railway (recommended) or other hosting platforms.

## Phase 1 Improvements Completed ✅

- ✅ Replaced CSV storage with SQLite database
- ✅ Added comprehensive error handling and logging
- ✅ Fixed timezone and scheduling bugs
- ✅ Added new commands: `!list_curfews`, `!remove_curfew`
- ✅ Improved message formatting with Discord embeds
- ✅ Updated dependencies to modern versions

## New Commands Available

- `!curfew [time] [@user]` - Set a curfew (admin only)
- `!reset` - Clear all curfews (admin only)
- `!list_curfews` - Show all active curfews (admin only)
- `!remove_curfew [@user]` - Remove specific user's curfew (admin only)

## Deployment Options

### Option 1: Railway (Recommended) 🚀

Railway offers the best free tier for Discord bots with no sleep mode.

#### Step 1: Prepare Your Repository
1. Make sure your `.env` file is NOT committed to git (it should be in `.gitignore`)
2. Copy `.env.example` to `.env` and fill in your values
3. Commit your changes:
   ```bash
   git add .
   git commit -m "Add improved CurfewBot with SQLite"
   git push origin main
   ```

#### Step 2: Deploy to Railway
1. Go to [railway.app](https://railway.app) and sign up/login
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your CurfewBot repository
4. Railway will automatically detect it's a Python project

#### Step 3: Configure Environment Variables
1. In your Railway project dashboard, go to "Variables"
2. Add these environment variables:
   - `BOT_TOKEN`: Your Discord bot token
   - `GUILD_ID`: Your Discord server ID
3. Click "Deploy" to restart with new variables

#### Step 4: Monitor Deployment
1. Check the "Deployments" tab for build logs
2. Once deployed, check "Logs" tab to see if bot started successfully
3. Look for "Bot logged in as [BotName]" message

### Option 2: Heroku

#### Step 1: Install Heroku CLI
Download from [devcenter.heroku.com/articles/heroku-cli](https://devcenter.heroku.com/articles/heroku-cli)

#### Step 2: Create Heroku App
```bash
heroku create your-curfew-bot-name
```

#### Step 3: Set Environment Variables
```bash
heroku config:set BOT_TOKEN=your_bot_token_here
heroku config:set GUILD_ID=your_guild_id_here
```

#### Step 4: Update Procfile
Make sure your `Procfile` contains:
```
worker: python curfewbot_improved.py
```

#### Step 5: Deploy
```bash
git add .
git commit -m "Deploy improved CurfewBot"
git push heroku main
```

#### Step 6: Scale Worker
```bash
heroku ps:scale worker=1
```

### Option 3: DigitalOcean App Platform

1. Go to [cloud.digitalocean.com](https://cloud.digitalocean.com)
2. Create new App from GitHub repository
3. Select your CurfewBot repo
4. Configure environment variables in the app settings
5. Deploy

## Testing Your Deployment

1. **Check Bot Status**: Your bot should appear online in Discord
2. **Test Basic Command**: Try `!list_curfews` (should show "No active curfews")
3. **Test Curfew Setting**: Try `!curfew 11:30PM @username`
4. **Check Logs**: Monitor your hosting platform's logs for any errors

## Environment Variables Needed

Create a `.env` file (locally) or set these in your hosting platform:

```env
BOT_TOKEN=your_discord_bot_token
GUILD_ID=your_discord_server_id
```

## Database

The improved bot uses SQLite, which creates a local `curfew_bot.db` file. This works on all hosting platforms and persists data between restarts (unlike the old CSV approach).

## Troubleshooting

### Bot Won't Start
- Check that `BOT_TOKEN` is set correctly
- Verify bot has proper permissions in Discord server
- Check deployment logs for specific error messages

### Commands Not Working
- Ensure you have Administrator permissions in Discord
- Check that `GUILD_ID` matches your Discord server
- Verify bot has necessary permissions (Send Messages, Manage Voice)

### Database Issues
- SQLite database is created automatically on first run
- If issues persist, delete `curfew_bot.db` to reset (will lose all curfews)

## Next Steps (Future Phases)

After successful deployment, consider these improvements:
- Upgrade to PostgreSQL for better reliability
- Add slash commands for modern Discord experience
- Implement recurring curfews
- Add timezone support for users
- Create web dashboard for management

## Support

If you encounter issues:
1. Check the deployment logs first
2. Verify all environment variables are set
3. Test locally with `python curfewbot_improved.py`
4. Check Discord bot permissions

## File Structure

```
CurfewBot/
├── curfewbot_improved.py    # Main bot file (use this instead of curfewbot.py)
├── requirements_new.txt     # Updated dependencies
├── .env.example            # Environment variables template
├── .env                    # Your actual environment variables (don't commit)
├── Procfile               # For Heroku deployment
├── curfew_bot.db          # SQLite database (created automatically)
└── DEPLOYMENT_GUIDE.md    # This file
```

Remember to use `curfewbot_improved.py` as your main bot file and `requirements_new.txt` for dependencies!
