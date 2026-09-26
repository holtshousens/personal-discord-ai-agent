import os
from dataclasses import dataclass


def _csv_ints(value: str) -> set[int]:
    return {int(x.strip()) for x in value.split(",") if x.strip()}


@dataclass(frozen=True)
class Settings:
    openai_api_key: str
    openai_model: str
    discord_bot_token: str
    discord_guild_id: int | None
    allowed_user_ids: set[int]
    log_level: str
    max_history_messages: int

    @classmethod
    def from_env(cls) -> "Settings":
        required = ["OPENAI_API_KEY", "DISCORD_BOT_TOKEN"]
        missing = [name for name in required if not os.getenv(name)]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        guild_id = os.getenv("DISCORD_GUILD_ID")
        return cls(
            openai_api_key=os.environ["OPENAI_API_KEY"],
            openai_model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
            discord_bot_token=os.environ["DISCORD_BOT_TOKEN"],
            discord_guild_id=int(guild_id) if guild_id else None,
            allowed_user_ids=_csv_ints(os.getenv("ALLOWED_USER_IDS", "")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
            max_history_messages=int(os.getenv("MAX_HISTORY_MESSAGES", "12")),
        )
