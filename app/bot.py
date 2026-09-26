import logging

import discord
from discord import app_commands

from .agent import Agent
from .config import Settings
from .memory import MemoryStore

logger = logging.getLogger(__name__)


def chunk(text: str, size: int = 1900) -> list[str]:
    return [text[i:i + size] for i in range(0, len(text), size)] or [""]


class AgentBot(discord.Client):
    def __init__(self, settings: Settings, agent: Agent) -> None:
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.settings = settings
        self.agent = agent
        self.tree = app_commands.CommandTree(self)

    def user_allowed(self, user_id: int) -> bool:
        # Empty allow-list means "allow any user who can invoke the command".
        # For a private bot, set ALLOWED_USER_IDS to your Discord user ID.
        return not self.settings.allowed_user_ids or user_id in self.settings.allowed_user_ids

    async def setup_hook(self) -> None:
        if self.settings.discord_guild_id:
            guild = discord.Object(id=self.settings.discord_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
            logger.info("Synced slash commands to guild %s", self.settings.discord_guild_id)
        else:
            await self.tree.sync()
            logger.info("Synced global slash commands")

    async def on_ready(self) -> None:
        logger.info("Logged in as %s (%s)", self.user, self.user.id if self.user else "unknown")

    async def respond(self, interaction: discord.Interaction, text: str) -> None:
        parts = chunk(text)

        await interaction.followup.send(parts[0])

        for part in parts[1:]:
            await interaction.followup.send(part)


settings = Settings.from_env()
memory = MemoryStore()
agent = Agent(settings, memory)
bot = AgentBot(settings, agent)


@bot.tree.command(name="ask", description="Ask the AI agent a question or give it a task.")
@app_commands.describe(prompt="Your question or task")
async def ask(interaction: discord.Interaction, prompt: str):
    if not bot.user_allowed(interaction.user.id):
        await interaction.response.send_message(
            "You are not authorised to use this agent.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(thinking=True)
    try:
        answer = await bot.agent.ask(str(interaction.user.id), prompt)
        await bot.respond(interaction, answer)
    except Exception:
        logger.exception("Agent request failed")
        await interaction.followup.send(
            "The agent encountered an error. Check the container logs.",
            ephemeral=True,
        )


@bot.tree.command(name="reset", description="Reset your conversation memory.")
async def reset(interaction: discord.Interaction):
    if not bot.user_allowed(interaction.user.id):
        await interaction.response.send_message(
            "You are not authorised to use this agent.",
            ephemeral=True,
        )
        return

    bot.memory.reset(str(interaction.user.id))
    await interaction.response.send_message("Your agent conversation memory has been reset.")


@bot.tree.command(name="status", description="Check whether the agent is online.")
async def status(interaction: discord.Interaction):
    if not bot.user_allowed(interaction.user.id):
        await interaction.response.send_message(
            "You are not authorised to use this agent.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        f"Online. Model: `{bot.settings.openai_model}`"
    )


def main() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    bot.run(settings.discord_bot_token)


if __name__ == "__main__":
    main()
