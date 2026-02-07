# CurfewBot Project Structure

This document outlines the file structure of the CurfewBot project.

## Directory Structure

```
CurfewBot/
├── src/                              # Source code
│   └── curfewbot.py                  # Main bot application
├── config/                           # Configuration files
│   ├── .env.example                  # Environment variables template
│   └── requirements.txt              # Python dependencies
├── deploy/                           # Deployment files
│   ├── setup-ec2.sh                  # First-time EC2 setup script
│   └── curfewbot.service             # systemd service (non-Docker alternative)
├── docs/                             # Documentation
│   ├── IMPROVEMENT_AND_DEPLOYMENT_PLAN.md  # Full improvement and deployment plan
│   ├── DEPLOYMENT_GUIDE.md           # Deployment instructions
│   ├── IMPROVEMENTS_SUMMARY.md       # Summary of code improvements
│   └── SETUP_GUIDE.md                # Setup guide
├── tests/                            # Test files (future use)
├── .github/
│   └── workflows/
│       └── deploy.yml                # CI/CD: auto-deploy on push to main
├── .env                              # Environment variables (not in git)
├── .gitignore                        # Git ignore rules
├── .gitattributes                    # Git attributes
├── .dockerignore                     # Excludes files from Docker build context
├── Dockerfile                        # Docker image definition
├── docker-compose.yml                # Docker Compose for local/EC2 deployment
├── Procfile                          # Tells hosting platforms how to run the bot
├── README.md                         # Project overview
├── PROJECT_STRUCTURE.md              # This file
└── curfew.png                        # Bot logo/icon
```

## Directory Purposes

### `/src/` - Source Code
Contains the main application code:
- `curfewbot.py` - The Discord bot with SQLite database, health check server, graceful shutdown, and curfew enforcement

### `/config/` - Configuration
Contains configuration files and templates:
- `.env.example` - Template showing all available environment variables
- `requirements.txt` - Python dependencies

### `/deploy/` - Deployment
Contains files for deploying to AWS EC2:
- `setup-ec2.sh` - Bash script for first-time EC2 instance setup (installs Docker, Docker Compose, clones repo)
- `curfewbot.service` - systemd unit file for running the bot without Docker

### `/docs/` - Documentation
Contains all project documentation:
- `IMPROVEMENT_AND_DEPLOYMENT_PLAN.md` - Full plan covering code improvements and AWS deployment
- `DEPLOYMENT_GUIDE.md` - Step-by-step deployment instructions
- `IMPROVEMENTS_SUMMARY.md` - Summary of Part 1 code improvements
- `SETUP_GUIDE.md` - Setup guide

### `/tests/` - Testing
Reserved for future test files.

### `/.github/workflows/` - CI/CD
Contains GitHub Actions workflows:
- `deploy.yml` - Automatically deploys to EC2 via SSH on every push to `main`

## Quick Start

1. **Setup environment**:
   ```sh
   cp config/.env.example .env
   # Edit .env with your Discord bot token and guild ID
   ```

2. **Install dependencies**:
   ```sh
   pip install -r config/requirements.txt
   ```

3. **Run locally**:
   ```sh
   python src/curfewbot.py
   ```

4. **Run with Docker**:
   ```sh
   docker compose up -d
   ```

5. **Deploy to EC2**:
   Follow the instructions in `docs/IMPROVEMENT_AND_DEPLOYMENT_PLAN.md`

## Core Files

- **`src/curfewbot.py`** - Main bot application with all logic in a single file
- **`Dockerfile`** - Builds the Docker image (python:3.11-slim, non-root user, health check)
- **`docker-compose.yml`** - Runs the bot with a persistent volume for the SQLite database
- **`Procfile`** - Tells hosting platforms how to run the bot (`worker: python src/curfewbot.py`)
- **`.env`** - Your private environment variables (never committed to git)

## Notes

- The `tests/` directory is prepared for future testing
- All new development should use the organized structure under `src/`, `config/`, and `deploy/`
- The Procfile uses `src/curfewbot.py` as the entry point
- The SQLite database file (`curfew_bot.db`) is created at runtime and excluded from git via `.gitignore`
