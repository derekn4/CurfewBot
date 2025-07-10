# CurfewBot Project Structure

This document outlines the organized file structure of the CurfewBot project.

## 📁 Directory Structure

```
CurfewBot/
├── src/                          # Source code
│   └── curfewbot.py              # Main bot application
├── docs/                         # Documentation
│   ├── DEPLOYMENT_GUIDE.md       # Deployment instructions
│   └── IMPROVEMENTS_SUMMARY.md   # Summary of improvements made
├── config/                       # Configuration files
│   ├── .env.example             # Environment variables template
│   └── requirements.txt         # Python dependencies
├── tests/                        # Test files (future use)
├── .env                         # Environment variables (not in git)
├── .gitignore                   # Git ignore rules
├── .gitattributes              # Git attributes
├── Procfile                    # Deployment configuration
├── README.md                   # Project overview
├── PROJECT_STRUCTURE.md        # This file
├── curfew.png                  # Bot logo/icon
├── curfewbot_original.py      # Original bot (legacy)
├── requirements.txt           # Original requirements (legacy)
└── kicked_users.csv          # Legacy data file
```

## 📂 Directory Purposes

### `/src/` - Source Code
Contains the main application code:
- `curfewbot.py` - The enhanced Discord bot with SQLite database, error handling, and new features

### `/docs/` - Documentation
Contains all project documentation:
- `DEPLOYMENT_GUIDE.md` - Step-by-step deployment instructions for various platforms
- `IMPROVEMENTS_SUMMARY.md` - Detailed summary of Phase 1 improvements

### `/config/` - Configuration
Contains configuration files and templates:
- `.env.example` - Template showing required environment variables
- `requirements.txt` - Updated Python dependencies for the improved bot

### `/tests/` - Testing
Reserved for future test files:
- Unit tests
- Integration tests
- Database tests

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   cp config/.env.example .env
   # Edit .env with your Discord bot token and guild ID
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r config/requirements.txt
   ```

3. **Run Locally**:
   ```bash
   python src/curfewbot.py
   ```

4. **Deploy**:
   Follow the instructions in `docs/DEPLOYMENT_GUIDE.md`

## 📋 File Descriptions

### Core Files
- **`src/curfewbot.py`** - Main bot application with all improvements
- **`Procfile`** - Tells hosting platforms how to run the bot
- **`.env`** - Your private environment variables (never commit this)

### Configuration
- **`config/.env.example`** - Template for environment variables
- **`config/requirements.txt`** - Modern Python dependencies

### Documentation
- **`docs/DEPLOYMENT_GUIDE.md`** - Complete deployment instructions
- **`docs/IMPROVEMENTS_SUMMARY.md`** - What was improved in Phase 1
- **`README.md`** - Original project overview
- **`PROJECT_STRUCTURE.md`** - This file

### Legacy Files (Keep for Reference)
- **`curfewbot_original.py`** - Original bot code
- **`requirements.txt`** - Original dependencies
- **`kicked_users.csv`** - Old CSV data storage

## 🔧 Development Workflow

1. **Make Changes**: Edit files in `src/`
2. **Test Locally**: Run `python src/curfewbot.py`
3. **Update Docs**: Update relevant files in `docs/`
4. **Deploy**: Push to your hosting platform

## 🌟 Benefits of This Structure

- **Organized**: Clear separation of code, docs, and config
- **Professional**: Follows standard project layout conventions
- **Scalable**: Easy to add new features and tests
- **Maintainable**: Easy to find and update specific components
- **Deployment-Ready**: Works with all major hosting platforms

## 📝 Notes

- The `tests/` directory is prepared for future testing implementation
- Legacy files are kept for reference but not used in deployment
- All new development should use files in the organized structure
- The Procfile has been updated to use `src/curfewbot.py`
