# CurfewBot: Improvements + AWS Free Tier Deployment Plan

## Context

CurfewBot is a Python Discord bot that enforces curfews on voice channel users. It currently works but has several code quality issues and no cloud deployment. The goal is to improve the codebase and deploy to **AWS EC2 Free Tier** (t2.micro — free for 12 months, then ~$3-5/mo).

---

## Part 1: Code Improvements

### 1.1 Remove Unused Dependencies

**File**: `config/requirements.txt`

| Dependency | Why Remove |
|-----------|------------|
| `pandas` | Legacy CSV dependency — no longer imported or used |
| `async-timeout` | Not imported anywhere in the codebase |
| `dnspython` | Not used directly by bot code |

### 1.2 Fix Database Connection Handling

**File**: `src/curfewbot.py`

**Problem**: Every DB function opens/closes connections manually without `try/finally` or context managers. If an exception occurs between `connect()` and `close()`, the connection leaks.

**Fix**: Refactor all DB functions to use Python's `with` context manager:

```python
def get_connection():
    return sqlite3.connect(DB_NAME)

# Usage in every DB function:
def get_all_curfews():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM curfews')
        return cursor.fetchall()
```

### 1.3 Fix Curfew Logic Bugs

**File**: `src/curfewbot.py`

| Bug | Description | Fix |
|-----|-------------|-----|
| Midnight crossing | `on_voice_state_update` compares `current_time.time() < allow_time` — breaks when curfew is 11:30 PM and allow is 11:35 PM but current time is 12:01 AM (next day). The comparison says 12:01 AM < 11:35 PM = True, so user gets kicked even though curfew is over. | Store full datetime (including date) in DB instead of just time string. Compare full datetimes. |
| Display name keys | Scheduled tasks dict uses `member.display_name` as key. Users can change their display name to escape curfew. | Use `member.id` (immutable integer) as the key instead. |
| Relative DB path | `DB_NAME = "curfew_bot.db"` — the file is created wherever the script is launched from, not next to the script. | Use `os.path.join(os.path.dirname(os.path.abspath(__file__)), "curfew_bot.db")` |

### 1.4 Add Graceful Shutdown

**File**: `src/curfewbot.py`

**Why**: When deployed, systemd and Docker send `SIGTERM` to stop the process. Without handling it, the bot drops connections abruptly.

**Fix**: Add signal handlers that cleanly close the Discord connection and database before exiting.

### 1.5 Add Health Check Endpoint

**File**: `src/curfewbot.py`

**Why**: AWS load balancers and monitoring tools need a way to check if the bot is alive.

**How**: Add a lightweight HTTP server (using `aiohttp` or Python's built-in `http.server`) on a configurable port (default 8080) that returns:
- `200 OK` when bot is connected to Discord
- `503 Service Unavailable` when disconnected

### 1.6 Clean Up Legacy Files

| File | Action | Reason |
|------|--------|--------|
| `curfewbot_original.py` | Delete | Superseded by `src/curfewbot.py` |
| `kicked_users.csv` | Delete | Legacy CSV storage, no longer used |

### 1.7 Improve .gitignore

**File**: `.gitignore`

Add these missing entries:
```
*.db
__pycache__/
*.pyc
venv/
.venv/
*.egg-info/
dist/
build/
```

---

## Part 2: AWS Free Tier Deployment

### Architecture Overview

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────────────────────┐
│  GitHub      │      │  GitHub Actions   │      │  AWS EC2 t2.micro (Free)    │
│  Repository  │─────►│  CI/CD Pipeline   │─────►│  ┌─────────────────────┐    │
│              │ push │                   │ SSH  │  │  Docker Container    │    │
│  main branch │      │  - Build          │      │  │  ┌─────────────┐    │    │
│              │      │  - Test           │      │  │  │ curfewbot.py│    │    │
└─────────────┘      │  - Deploy         │      │  │  └─────────────┘    │    │
                     └──────────────────┘      │  │  ┌─────────────┐    │    │
                                               │  │  │ curfew_bot.db│   │    │
                                               │  │  └─────────────┘    │    │
                                               │  └─────────────────────┘    │
                                               └─────────────────────────────┘
```

### 2.1 Create Dockerfile

**New file**: `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY config/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

# Health check port
EXPOSE 8080

CMD ["python", "src/curfewbot.py"]
```

### 2.2 Create docker-compose.yml

**New file**: `docker-compose.yml`

```yaml
version: "3.8"
services:
  curfewbot:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - bot-data:/app/data    # Persist SQLite DB across container restarts
    ports:
      - "8080:8080"           # Health check endpoint

volumes:
  bot-data:
```

### 2.3 Create EC2 Setup Script

**New file**: `deploy/setup-ec2.sh`

This script runs once on a fresh EC2 instance to install everything needed:

1. Update system packages
2. Install Docker and Docker Compose
3. Enable Docker to start on boot
4. Clone the repository
5. Create `.env` file with bot token and guild ID
6. Start the bot with `docker-compose up -d`

### 2.4 Create systemd Service (Non-Docker Alternative)

**New file**: `deploy/curfewbot.service`

For running without Docker — a systemd unit file that:
- Starts the bot on boot
- Auto-restarts on crash (10 second delay)
- Runs as a non-root user
- Logs to journald

### 2.5 Create GitHub Actions CI/CD Pipeline

**New file**: `.github/workflows/deploy.yml`

**Trigger**: Push to `main` branch

**Steps**:
1. Checkout code
2. SSH into EC2 instance
3. Pull latest code from GitHub
4. Rebuild Docker image
5. Restart container with zero-downtime

**Required GitHub Secrets**:
| Secret | Description |
|--------|-------------|
| `EC2_HOST` | Public IP or DNS of your EC2 instance |
| `EC2_SSH_KEY` | Private SSH key for EC2 access |
| `BOT_TOKEN` | Discord bot token |
| `GUILD_ID` | Discord server ID |

---

## Part 3: Step-by-Step AWS Setup Guide

### Step 1: Create AWS Account
1. Go to [aws.amazon.com](https://aws.amazon.com) and create an account
2. You'll need a credit card, but won't be charged for free tier usage
3. Enable MFA on your root account (security best practice)

### Step 2: Launch EC2 Instance
1. Go to **EC2 Dashboard** → **Launch Instance**
2. Settings:
   - **Name**: `curfewbot`
   - **AMI**: Amazon Linux 2023 (free tier eligible)
   - **Instance type**: `t2.micro` (free tier — 1 vCPU, 1GB RAM)
   - **Key pair**: Create new → download `.pem` file (keep this safe!)
   - **Storage**: 8 GB gp3 (free tier)
3. Click **Launch Instance**

### Step 3: Configure Security Group
1. Go to **EC2** → **Security Groups** → select your instance's security group
2. **Inbound Rules**:
   - SSH (port 22) — Your IP only
   - Custom TCP (port 8080) — Your IP only (for health checks, optional)
3. **Outbound Rules**: Allow all (default — bot needs to reach Discord API)

### Step 4: Connect and Set Up
```bash
# SSH into your instance
ssh -i your-key.pem ec2-user@<your-ec2-public-ip>

# Clone repo and run setup
git clone https://github.com/YOUR_USERNAME/CurfewBot.git
cd CurfewBot
chmod +x deploy/setup-ec2.sh
./deploy/setup-ec2.sh
```

### Step 5: Configure Environment Variables
```bash
# Create .env file on the server
cat > .env << 'EOF'
BOT_TOKEN=your_discord_bot_token_here
GUILD_ID=your_discord_guild_id_here
EOF
```

### Step 6: Start the Bot
```bash
# Using Docker (recommended)
docker-compose up -d

# Check logs
docker-compose logs -f

# Verify bot is running
curl http://localhost:8080/health
```

### Step 7: Set Up GitHub Actions (Optional CI/CD)
1. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:
   - `EC2_HOST`: Your EC2 public IP
   - `EC2_SSH_KEY`: Contents of your `.pem` file
   - `BOT_TOKEN`: Discord bot token
   - `GUILD_ID`: Discord server ID
3. Now every push to `main` auto-deploys to your EC2 instance

---

## Part 4: Implementation Order

| Phase | Task | Files Modified/Created |
|-------|------|----------------------|
| 1 | Clean up dependencies & .gitignore | `config/requirements.txt`, `.gitignore` |
| 2 | Fix DB connection handling (context managers) | `src/curfewbot.py` |
| 3 | Fix curfew logic bugs (midnight, display_name, DB path) | `src/curfewbot.py` |
| 4 | Add graceful shutdown handling | `src/curfewbot.py` |
| 5 | Add health check endpoint | `src/curfewbot.py` |
| 6 | Delete legacy files | `curfewbot_original.py`, `kicked_users.csv` |
| 7 | Create Dockerfile + docker-compose.yml | `Dockerfile`, `docker-compose.yml` |
| 8 | Create EC2 setup script | `deploy/setup-ec2.sh` |
| 9 | Create systemd service file | `deploy/curfewbot.service` |
| 10 | Create GitHub Actions CI/CD pipeline | `.github/workflows/deploy.yml` |

---

## Part 5: Verification Checklist

After implementation, verify:

- [X] `python src/curfewbot.py` — bot connects to Discord locally
- [X] `docker build -t curfewbot .` — Docker image builds successfully
- [X] `docker-compose up` — bot starts in container and connects to Discord
- [X] `curl http://localhost:8080/health` — returns 200 OK
- [X] `!curfew 11:30PM @user` — sets curfew successfully
- [X] `!list_curfews` — shows active curfews
- [X] `!remove_curfew @user` — removes curfew
- [X] `!reset` — clears all curfews
- [X] Bot auto-restarts after `docker-compose restart`
- [X] SQLite data persists after container restart

---

## Cost Summary

| Resource | Monthly Cost |
|----------|-------------|
| EC2 t2.micro | **FREE** (12 months free tier) |
| EBS 8GB gp3 storage | **FREE** (12 months free tier) |
| Data transfer out | **FREE** (up to 100 GB/mo free tier) |
| GitHub Actions | **FREE** (2,000 min/mo for public repos) |
| **Total (Year 1)** | **$0/month** |
| **Total (After Free Tier)** | **~$3-5/month** (t4g.nano) |
