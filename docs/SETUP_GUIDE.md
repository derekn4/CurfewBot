# CurfewBot Setup Guide for New Users

This guide will help you set up CurfewBot on your own Discord server from scratch.

## 📋 Prerequisites

- A Discord account with server administrator permissions
- Python 3.8+ installed on your computer (or access to a hosting platform)
- Basic familiarity with Discord server management

## 🤖 Step 1: Create Your Discord Bot

### 1.1 Go to Discord Developer Portal
1. Visit [https://discord.com/developers/applications](https://discord.com/developers/applications)
2. Click "New Application"
3. Give your bot a name (e.g., "MyCurfewBot")
4. Click "Create"

### 1.2 Create the Bot User
1. In your application, click "Bot" in the left sidebar
2. Click "Add Bot"
3. Confirm by clicking "Yes, do it!"
4. **Copy the Bot Token** - you'll need this later
   - Click "Copy" under the Token section
   - ⚠️ **Keep this token secret!** Never share it publicly

### 1.3 Configure Bot Permissions
1. Still in the "Bot" section, scroll down to "Privileged Gateway Intents"
2. Enable "Server Members Intent" (if you want member-related features)
3. Enable "Message Content Intent" (for command processing)

### 1.4 Generate Invite Link
1. Click "OAuth2" → "URL Generator" in the left sidebar
2. Under "Scopes", check:
   - `bot`
   - `applications.commands` (for future slash commands)
3. Under "Bot Permissions", check:
   - `Send Messages`
   - `Use Slash Commands`
   - `Move Members` (essential for kicking from voice channels)
   - `View Channels`
   - `Read Message History`
4. Copy the generated URL at the bottom

## 🏠 Step 2: Add Bot to Your Server

### 2.1 Invite the Bot
1. Paste the invite URL from Step 1.4 into your browser
2. Select your Discord server from the dropdown
3. Click "Authorize"
4. Complete any CAPTCHA if prompted

### 2.2 Get Your Guild (Server) ID
1. In Discord, go to User Settings (gear icon)
2. Go to "Advanced" and enable "Developer Mode"
3. Right-click on your server name in the server list
4. Click "Copy Server ID"
5. **Save this ID** - you'll need it for configuration

## 💻 Step 3: Set Up the Bot Code

### 3.1 Download/Clone the CurfewBot
```bash
git clone https://github.com/derekn4/CurfewBot.git
cd CurfewBot
```

### 3.2 Install Dependencies
```bash
pip install -r config/requirements.txt
```

### 3.3 Configure Environment Variables
1. Copy the environment template:
   ```bash
   cp config/.env.example .env
   ```

2. Edit the `.env` file with your credentials:
   ```env
   BOT_TOKEN=your_bot_token_from_step_1.2
   GUILD_ID=your_server_id_from_step_2.2
   ```

### 3.4 Test the Setup
```bash
python setup.py
```
This will validate your configuration and dependencies.

## 🚀 Step 4: Run the Bot

### 4.1 Run Locally (Testing)
```bash
python src/curfewbot.py
```

You should see:
```
Bot logged in as YourBotName#1234
Connected to guild: YourServerName
```

### 4.2 Test Bot Commands
In your Discord server, try:
```
!list_curfews
```
You should get a response showing "No active curfews."

## ☁️ Step 5: Deploy to Cloud (Optional)

For 24/7 operation, deploy to a hosting platform:

### Option A: Railway (Recommended)
1. Push your code to GitHub
2. Go to [railway.app](https://railway.app)
3. Create new project from GitHub repo
4. Add environment variables in Railway dashboard:
   - `BOT_TOKEN`: Your bot token
   - `GUILD_ID`: Your server ID
5. Deploy!

### Option B: Heroku
1. Install Heroku CLI
2. Create Heroku app: `heroku create your-bot-name`
3. Set environment variables:
   ```bash
   heroku config:set BOT_TOKEN=your_token_here
   heroku config:set GUILD_ID=your_guild_id_here
   ```
4. Deploy: `git push heroku main`
5. Scale worker: `heroku ps:scale worker=1`

## 🎮 Step 6: Using CurfewBot

### Available Commands (Admin Only):
- `!curfew 11:30PM @username` - Set a curfew for a user
- `!list_curfews` - Show all active curfews
- `!remove_curfew @username` - Remove a user's curfew
- `!reset` - Clear all curfews

### How It Works:
1. **Set Curfew**: Bot schedules automatic voice channel kick at specified time
2. **Enforcement**: If user tries to join voice before curfew ends, they get kicked
3. **Shame Message**: Public message when someone violates curfew
4. **Auto-cleanup**: Expired curfews are automatically removed

## 🔧 Troubleshooting

### Bot Won't Start
- ✅ Check that `BOT_TOKEN` is correct (no extra spaces)
- ✅ Verify `GUILD_ID` matches your server
- ✅ Ensure bot has proper permissions in Discord

### Commands Don't Work
- ✅ Make sure you have Administrator permissions
- ✅ Check that bot can see the channel you're typing in
- ✅ Verify bot has "Send Messages" permission

### Can't Kick Users from Voice
- ✅ Bot needs "Move Members" permission
- ✅ Bot's role must be higher than target user's highest role
- ✅ Can't kick server owner or other admins

### Bot Goes Offline
- ✅ If running locally, your computer must stay on
- ✅ Consider deploying to cloud hosting for 24/7 operation
- ✅ Check hosting platform logs for errors

## 🔒 Security Best Practices

### Protect Your Bot Token
- ❌ **Never** commit `.env` file to git
- ❌ **Never** share your bot token publicly
- ❌ **Never** post screenshots showing your token
- ✅ Use environment variables on hosting platforms
- ✅ Regenerate token if accidentally exposed

### Server Permissions
- ✅ Only give bot necessary permissions
- ✅ Restrict admin commands to trusted users
- ✅ Monitor bot activity regularly

## 📞 Support

If you need help:
1. Check this guide first
2. Review the troubleshooting section
3. Check the deployment guide: `docs/DEPLOYMENT_GUIDE.md`
4. Verify your setup with: `python setup.py`

## 🎉 You're All Set!

Your CurfewBot should now be running and ready to enforce curfews on your Discord server. Remember to test it with a friend before using it for real curfews!

### Quick Test Checklist:
- [ ] Bot appears online in your server
- [ ] `!list_curfews` command works
- [ ] Can set a test curfew: `!curfew 11:59PM @friend`
- [ ] Bot kicks user from voice at curfew time
- [ ] Shame message appears when user tries to rejoin early
- [ ] Can remove curfew: `!remove_curfew @friend`

Welcome to the CurfewBot community! 🎮⏰
