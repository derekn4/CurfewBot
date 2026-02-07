<!-- Improved compatibility of back to top link: See: https://github.com/othneildrew/Best-README-Template/pull/73 -->
<a name="readme-top"></a>


<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/derekn4/CurfewBot">
    <img src="curfew.png" alt="Logo" width="300" height="300">
  </a>

<h3 align="center">CurfewBot: The Solution to Chronic Late Night Gamers</h3>

  <p align="center">
    This is exactly what it sounds like. It's a Discord bot that forces a curfew on members in your Discord group.
    The bot removes a user from any (and every) voice channel at a specified time and will not allow them to rejoin until their curfew is up.
    <br />
    <a href="https://github.com/derekn4/CurfewBot"><strong>Explore the docs</strong></a>
    <br />
    <br />
    <a href="https://github.com/derekn4/CurfewBot">View Demo</a>
    ·
    <a href="https://github.com/derekn4/CurfewBot/issues">Report Bug</a>
    ·
    <a href="https://github.com/derekn4/CurfewBot/issues">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#deployment">Deployment</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#contact">Contact</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

This is exactly what it sounds like. It's a Discord bot that forces a curfew on members in your Discord group.
The bot removes a user from any (and every) voice channel at a specified time and will not allow them to rejoin until their curfew is up.

All times are in US/Pacific timezone.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Python][Python.org]][Python-url]

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

Since it's all in Python, we are going to need pip.

### Prerequisites

* pip
  ```sh
  pip install --upgrade pip
  ```

### Installation

1. To get started with the Discord API: [https://discord.com/developers/docs/intro](https://discord.com/developers/docs/intro)
2. Clone the repo
   ```sh
   git clone https://github.com/derekn4/CurfewBot.git
   cd CurfewBot
   ```
3. Install Python packages
   ```sh
   pip install -r config/requirements.txt
   ```
4. Copy the example environment file and enter your credentials
   ```sh
   cp config/.env.example .env
   ```
   Then edit `.env` and fill in your values:
   ```
   BOT_TOKEN=your_bot_token_here
   GUILD_ID=your_guild_id_here
   ```
5. Make sure your bot has the required intents enabled in the [Discord Developer Portal](https://discord.com/developers/applications):
   - `voice_states` -- monitor voice channel joins
   - `message_content` -- receive prefix command messages
6. Run the bot
   ```sh
   python src/curfewbot.py
   ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

First, make sure that your bot is enabled for the Discord server of intended use.
Second, enable access to voice chat and text chats, as well as admin privileges.

All commands require admin permissions.

| Command | Description | Example |
|---------|-------------|---------|
| `!curfew <time> @user` | Set a curfew for a user | `!curfew 11:30PM @user` |
| `!list_curfews` | Show all active curfews | `!list_curfews` |
| `!remove_curfew @user` | Remove a specific user's curfew | `!remove_curfew @user` |
| `!reset` | Clear all curfews | `!reset` |

When a curfew is set, the bot will:
- Send a reminder 5 minutes before the curfew
- Kick the user from voice at the curfew time
- Block them from rejoining any voice channel for 5 minutes
- Shame them in the general channel if they try to rejoin early

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- DEPLOYMENT -->
## Deployment

CurfewBot is set up for deployment on AWS EC2 (free tier) using Docker.

### With Docker (recommended)

```sh
# Build and start
docker compose up -d

# Check logs
docker compose logs -f

# Verify the bot is running
curl http://localhost:8080/health
```

### Without Docker

A systemd service file is provided at `deploy/curfewbot.service` for running directly on Linux.

### CI/CD

The project includes a GitHub Actions workflow (`.github/workflows/deploy.yml`) that automatically deploys to EC2 on every push to `main`. See `docs/IMPROVEMENT_AND_DEPLOYMENT_PLAN.md` for full setup instructions.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [X] Responds to command
- [X] Adds user to database with cutoff time
- [X] Kicks user out of voice call
    - [X] Continues to kick user out of voice channels until curfew is up
    - [X] Mentions and shames user in General chat if they try to join before curfew is over
- [X] Health check endpoint for monitoring
- [X] Graceful shutdown handling
- [X] Docker containerization
- [X] CI/CD pipeline for auto-deploy
- [X] Push CurfewBot to server to run remotely and not local

See the [open issues](https://github.com/derekn4/CurfewBot/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Derek Nguyen
- [LinkedIn](https://www.linkedin.com/in/derekhuynguyen/)
- [Email](mailto:derek.nguyen99@gmail.com)

Project Link: [https://github.com/derekn4/CurfewBot](https://github.com/derekn4/CurfewBot)

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[Python.org]: https://www.python.org/static/img/python-logo.png
[Python-url]: https://www.python.org/about/website/
