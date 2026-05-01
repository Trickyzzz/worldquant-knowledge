from __future__ import annotations

import time
from typing import Any

import requests


class BrainClientError(RuntimeError):
    """Raised when WorldQuant BRAIN read-only export fails."""


class InternalBrainClient:
    """Read-only client for the internal endpoints used by the BRAIN web app."""

    def __init__(
        self,
        base_url: str,
        cookie: str,
        delay_seconds: float,
        max_requests_per_run: int,
        region: str = "USA",
        delay: int = 1,
        universe: str = "TOP3000",
        max_rate_limit_retries: int = 12,
        rate_limit_backoff_seconds: float = 60.0,
        max_rate_limit_sleep_seconds: float = 900.0,
        sleep: Any = time.sleep,
        session: requests.Session | Any | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.delay_seconds = delay_seconds
        self.max_requests_per_run = max_requests_per_run
        self.region = region
        self.delay = delay
        self.universe = universe
        self.max_rate_limit_retries = max_rate_limit_retries
        self.rate_limit_backoff_seconds = rate_limit_backoff_seconds
        self.max_rate_limit_sleep_seconds = max_rate_limit_sleep_seconds
        self.sleep = sleep
        self.requests_made = 0
        self.session = session or requests.Session()
        headers = {
            "Cookie": cookie,
            "Accept": "application/json",
            "User-Agent": "worldquant-knowledge/0.1 read-only-export",
        }
        if hasattr(self.session, "headers"):
            self.session.headers.update(headers)
        else:
            self.session.headers = headers

    def get_operators(self) -> list[dict[str, Any]]:
        payload = self._get("/operators")
        if isinstance(payload, list):
            return payload
        return list(payload.get("results", payload.get("operators", [])))

    def get_datasets(self) -> list[dict[str, Any]]:
        return self._get_paginated("/data-sets")

    def get_fields(self) -> list[dict[str, Any]]:
        return self._get_paginated("/data-fields")

    def _get_paginated(self, path: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        offset = 0
        limit = 50
        while True:
            payload = self._get(
                path,
                params={
                    "region": self.region,
                    "delay": self.delay,
                    "universe": self.universe,
                    "instrumentType": "EQUITY",
                    "limit": limit,
                    "offset": offset,
                },
            )
            page = payload.get("results", payload if isinstance(payload, list) else [])
            if not isinstance(page, list):
                raise BrainClientError(f"Unexpected response shape for {path}: missing results list")
            results.extend(page)
            count = int(payload.get("count", len(results)) if isinstance(payload, dict) else len(results))
            if len(results) >= count or not page:
                return results
            offset += limit

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if self.requests_made >= self.max_requests_per_run:
            raise BrainClientError(
                f"Stopped before {path}: max_requests_per_run={self.max_requests_per_run} reached."
            )
        if self.requests_made:
            self.sleep(self.delay_seconds)
        url = f"{self.base_url}{path}"
        response = self._get_with_rate_limit_retry(url, params)
        if response.status_code in {401, 403}:
            raise BrainClientError("WorldQuant BRAIN session is invalid or lacks permission.")
        if response.status_code >= 400:
            raise BrainClientError(f"WorldQuant BRAIN request failed: {response.status_code} {response.text[:300]}")
        try:
            return response.json()
        except ValueError as exc:
            raise BrainClientError(f"WorldQuant BRAIN returned non-JSON response for {path}.") from exc

    def _get_with_rate_limit_retry(self, url: str, params: dict[str, Any] | None) -> Any:
        rate_limit_attempts = 0
        while True:
            response = self.session.get(url, params=params, timeout=60)
            self.requests_made += 1
            if response.status_code != 429:
                return response
            if rate_limit_attempts >= self.max_rate_limit_retries:
                raise BrainClientError(
                    f"WorldQuant BRAIN API rate limit exceeded after {self.max_rate_limit_retries} retries."
                )
            wait_seconds = self._rate_limit_wait_seconds(response, rate_limit_attempts)
            rate_limit_attempts += 1
            self.sleep(wait_seconds)

    def _rate_limit_wait_seconds(self, response: Any, attempt: int) -> float:
        retry_after = getattr(response, "headers", {}).get("Retry-After", "")
        if retry_after:
            try:
                wait_seconds = float(retry_after)
            except ValueError:
                wait_seconds = self.rate_limit_backoff_seconds * (2**attempt)
        else:
            wait_seconds = self.rate_limit_backoff_seconds * (2**attempt)
        return min(wait_seconds, self.max_rate_limit_sleep_seconds)
