import time
from dataclasses import dataclass
from typing import Any

import requests

BASE_URL = "https://api.igdb.com/v4"

@dataclass
class IGDBAPIManager:
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
        data: dict[str, str],
        *,
        request_url: str = BASE_URL
    ) -> list[dict[str, Any]]:
        if not request_url.endswith("/"):
            request_url = request_url + "/"
        if not data:
            raise ValueError(
                "Empty request body. Please add"
                + " some args to the data object."
            )
        data_ = "; ".join(f"{k} {v}" for k, v in data.items()) + ";"
        res = requests.post(
            url=request_url + endpoint,
            headers={
                "Client-ID": self.client_id,
                "Authorization": f"Bearer {self.access_token}"
            },
            data=data_
        ).json()
        return res