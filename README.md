# Personal Discord AI Agent

A small, Dockerized Python agent designed to run continuously on a Windows PC first and later move to a Linux VPS with minimal changes.

## Architecture

Discord slash command
        |
        v
discord.py bot
        |
        v
Agent service
        |
        +--> SQLite conversational memory
        |
        +--> OpenAI Responses API

The initial agent intentionally has no arbitrary shell/OS tools. New capabilities should be added as explicit, auditable tools.

## Prerequisites

- Windows 10/11
- Docker Desktop with Linux containers
- Git
- A Discord server where you can add an application
- An OpenAI API key
- A Discord bot/application token

## 1. Create the Discord application

Go to the Discord Developer Portal:

https://discord.com/developers/applications

Create a new application.

Under **Bot**, add a bot and copy its token.

Under **Installation** / installation settings, configure a server installation with the minimum permissions required for this bot. The bot only needs to receive slash-command interactions and send messages.

You do NOT need the Message Content privileged intent for this initial version because it uses slash commands.

Create/install the bot into your private development Discord server.

## 2. Find your Discord IDs

Enable Discord Developer Mode:

User Settings -> Advanced -> Developer Mode

Copy:
- your Discord user ID
- your development server ID

Put them into `.env` as `ALLOWED_USER_IDS` and `DISCORD_GUILD_ID`.

## 3. Create the environment file

Copy:

    .env.example

to:

    .env

Then set the real values.

NEVER commit `.env`.

## 4. Build and start

From this directory:

    docker compose up -d --build

Check:

    docker compose ps

View logs:

    docker compose logs -f agent

You should see the bot log in and slash commands sync.

## 5. Use it in Discord

Type `/` in your development server.

You should see:

- `/ask`
- `/reset`
- `/status`

Example:

    /ask Explain how AWS Lake Formation permissions work.

The bot maintains a small rolling conversation history per Discord user in `data/agent.db`.

## 6. Stop/restart

    docker compose stop

    docker compose start

Or:

    docker compose restart

To rebuild after code changes:

    docker compose up -d --build

## 7. Git

Initial repository:

    git init
    git add .
    git commit -m "Initial personal Discord AI agent"

Create an empty private repository on GitHub, then:

    git branch -M main
    git remote add origin YOUR_PRIVATE_REPOSITORY_URL
    git push -u origin main

Do not commit `.env`, API keys, Discord tokens, database files, or logs.

## 8. Windows: keep it running

Configure Docker Desktop to start with Windows.

The compose file uses:

    restart: unless-stopped

So Docker will restart the agent container after a crash or Docker restart.

This means the PC must be powered on and Docker Desktop must be running.

## 9. Later VPS migration

The same repository can be moved to an Ubuntu VPS.

The deployment becomes approximately:

    git clone <repo>
    cd discord-ai-agent
    cp .env.example .env
    nano .env
    docker compose up -d --build

The application code does not need to know whether it is running on your PC or VPS.

## Security notes

1. Keep the Discord bot private.
2. Set `ALLOWED_USER_IDS` to your own Discord user ID.
3. Keep the Discord bot token and OpenAI API key only in `.env` or a proper secret manager.
4. Use a private GitHub repository.
5. Do not add arbitrary shell execution as an agent tool.
6. When tools are added, implement each as an explicit Python function with validation and authorization.
7. Back up `data/agent.db` if the memory becomes valuable.

## Planned extensions

The architecture is intentionally ready for:

- Web search
- Scheduled jobs
- Email
- Calendar
- GitHub
- File access
- Browser automation
- Home automation
- Notifications
- Long-term memory
- Explicit tool/function calling
- Approval workflows for destructive actions
- Admin commands
- Health/metrics endpoint
- Redis/Postgres when the agent outgrows SQLite

## Design principle

The agent should be treated as an application with permissions, not as an unrestricted AI with access to the computer.

Every new capability should be added as a bounded tool with:
- clear input schema
- authorization
- logging
- error handling
- timeout
- safe defaults
- explicit approval where appropriate
