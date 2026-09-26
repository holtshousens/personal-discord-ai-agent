import json
import os
from datetime import UTC, datetime as dt
from pathlib import Path
from typing import Any

import aiohttp
from evohomeasync2 import AbstractTokenManager, EvohomeClient


TOKEN_FILE = Path("/app/data/evohome_tokens.json")


class PersistentTokenManager(AbstractTokenManager):
    """Persist Evohome authentication tokens between container restarts."""

    def __init__(
        self,
        username: str,
        password: str,
        websession: aiohttp.ClientSession,
    ) -> None:
        super().__init__(username, password, websession)

    async def load_access_token(self) -> None:
        """Load cached authentication tokens from disk."""

        if not TOKEN_FILE.exists():
            return

        try:
            data = json.loads(TOKEN_FILE.read_text())

            self._import_access_token(data)

        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            # Ignore a corrupt/missing cache and allow normal authentication.
            self.clear_access_token()
            self._refresh_token = ""

    async def save_access_token(self) -> None:
        """Save authentication tokens to disk."""

        TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)

        data = self._export_access_token()

        TOKEN_FILE.write_text(
            json.dumps(data, indent=2),
        )


class EvohomeAdapter:
    def __init__(self) -> None:
        self.username = os.environ["TCC_USERNAME"]
        self.password = os.environ["TCC_PASSWORD"]

        self.session: aiohttp.ClientSession | None = None
        self.token_manager: PersistentTokenManager | None = None
        self.client: EvohomeClient | None = None

    async def _ensure_client(self) -> EvohomeClient:
        """Create the Evohome client once and reuse it."""

        if self.client is not None:
            return self.client

        self.session = aiohttp.ClientSession()

        self.token_manager = PersistentTokenManager(
            self.username,
            self.password,
            self.session,
        )

        # Explicitly restore cached tokens.
        await self.token_manager.load_access_token()

        self.client = EvohomeClient(
            self.token_manager,
        )

        return self.client

    async def get_status(self) -> dict[str, Any]:
        """Retrieve the current Evohome status."""

        client = await self._ensure_client()

        await client.update()

        locations = []

        for location in client.locations:
            systems = []

            for gateway in location.gateways:
                for system in gateway.systems:
                    zones = []

                    for zone in system.zones:
                        zones.append(
                            {
                                "id": zone.id,
                                "name": zone.name,
                                "temperature": zone.temperature,
                                "target_temperature": zone.target_heat_temperature,
                                "mode": str(zone.mode),
                                "type": str(zone.type),
                            }
                        )

                    systems.append(
                        {
                            "id": system.id,
                            "model": str(system.model),
                            "mode": str(system.mode),
                            "zones": zones,
                        }
                    )

            locations.append(
                {
                    "id": location.id,
                    "name": location.name,
                    "country": location.country,
                    "systems": systems,
                }
            )

        return {"locations": locations}

    async def get_zones(self) -> list[dict[str, Any]]:
        """Return all Evohome zones."""

        status = await self.get_status()

        zones = []

        for location in status["locations"]:
            for system in location["systems"]:
                for zone in system["zones"]:
                    zones.append(
                        {
                            **zone,
                            "location": location["name"],
                            "system_id": system["id"],
                        }
                    )

        return zones

    async def close(self) -> None:
        """Close the Evohome HTTP session."""

        if self.session is not None:
            await self.session.close()
            self.session = None
            self.client = None
            self.token_manager = None