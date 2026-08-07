import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

BASE_URL = "https://api.igdb.com/v4"

@dataclass
class IGDBAPIStuff:
    client_id: str
    client_secret: str
    _access_token: str | None = None
    _access_token_valid_for: int = 0
    _access_token_minted_time: int = 0

    @property
    def access_token(self):
        if not self._is_access_token_valid():
            self._mint_new_token()
        return self._access_token

    def _mint_new_token(self) -> None:
        req_url = (
            "https://id.twitch.tv/oauth2/token?"
            + f"client_id={self.client_id}"
            + f"&client_secret={self.client_secret}"
            + "&grant_type=client_credentials"
        )
        res = requests.post(req_url).json()
        try:
            self._access_token = res["access_token"]
            self._access_token_valid_for = res["expires_in"]
            self._access_token_minted_time = int(time.monotonic())
        except KeyError:
            raise RuntimeError(
                "Unable to retrieve access token."
                + " Please check if you IGDB client ID and secret are valid."
            )
        if not self._is_access_token_valid():
            raise RuntimeError(
                "Newly minted access token not valid."
                + " Please check if you IGDB client ID and secret are valid."
            )

    def _is_access_token_valid(self) -> bool:
        time_passed_since_minted = (
            time.monotonic() - self._access_token_minted_time
        )
        return self._access_token is not None and time_passed_since_minted > 0

    def post_request(
        self,
        endpoint: str,
        *,
        request_url: str = BASE_URL
    ) -> dict[str, Any] | list[Any]:
        if not request_url.endswith("/"):
            request_url = request_url + "/"
        res = requests.post(
            url=request_url + endpoint,
            headers={
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.access_token}"
            },
            json={"fields": "*;"}
        ).json()
        return res
    

def main():
    try:
        endpoint = sys.argv[1]
    except IndexError:
        endpoint = "games"
    env_pth = Path.cwd() / ".env"
    assert env_pth.exists() and env_pth.is_file()
    env_loaded = load_dotenv(env_pth)
    if not env_loaded:
        raise RuntimeError(
            f"Unable to load .env at {env_pth}"
        )
    api_manager = IGDBAPIStuff(
        client_id=os.environ["igdb_client_id"],
        client_secret=os.environ["igdb_client_secret"],
    )
    print(json.dumps(api_manager.post_request(endpoint),
                     indent=4))


if __name__ == '__main__':
    main()
