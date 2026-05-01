import json

from worldquant_knowledge.brain_client import InternalBrainClient


class FakeResponse:
    def __init__(self, status_code, payload, headers=None):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)
        self.headers = headers or {}

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self):
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        if url.endswith("/operators"):
            return FakeResponse(200, [{"name": "rank", "category": "Cross Sectional"}])
        if url.endswith("/data-sets"):
            return FakeResponse(200, {"results": [{"id": "pv1", "name": "Price Volume"}], "count": 1})
        if url.endswith("/data-fields"):
            return FakeResponse(200, {"results": [{"id": "close", "dataset": {"id": "pv1"}}], "count": 1})
        return FakeResponse(404, {"detail": "missing"})


def test_internal_brain_client_fetches_read_only_resources_without_mutations():
    session = FakeSession()
    client = InternalBrainClient(
        base_url="https://api.worldquantbrain.com",
        cookie="session=abc",
        delay_seconds=0,
        max_requests_per_run=10,
        session=session,
    )

    assert client.get_operators()[0]["name"] == "rank"
    assert client.get_datasets()[0]["id"] == "pv1"
    assert client.get_fields()[0]["id"] == "close"
    assert [call[0] for call in session.calls] == [
        "https://api.worldquantbrain.com/operators",
        "https://api.worldquantbrain.com/data-sets",
        "https://api.worldquantbrain.com/data-fields",
    ]


def test_internal_brain_client_reports_rate_limit_clearly():
    class RateLimitedSession(FakeSession):
        def get(self, url, params=None, timeout=None):
            return FakeResponse(429, {"message": "API rate limit exceeded"})

    client = InternalBrainClient(
        base_url="https://api.worldquantbrain.com",
        cookie="session=abc",
        delay_seconds=0,
        max_requests_per_run=10,
        max_rate_limit_retries=0,
        session=RateLimitedSession(),
    )

    try:
        client.get_operators()
    except Exception as exc:
        assert "rate limit" in str(exc).lower()
    else:
        raise AssertionError("Expected rate limit error")


def test_internal_brain_client_retries_rate_limit_using_retry_after():
    class EventuallyOkSession(FakeSession):
        def __init__(self):
            super().__init__()
            self.attempts = 0

        def get(self, url, params=None, timeout=None):
            self.attempts += 1
            if self.attempts == 1:
                return FakeResponse(429, {"message": "API rate limit exceeded"}, {"Retry-After": "7"})
            return FakeResponse(200, [{"name": "rank", "category": "Cross Sectional"}])

    sleeps = []
    session = EventuallyOkSession()
    client = InternalBrainClient(
        base_url="https://api.worldquantbrain.com",
        cookie="session=abc",
        delay_seconds=0,
        max_requests_per_run=10,
        max_rate_limit_retries=2,
        max_rate_limit_sleep_seconds=30,
        sleep=sleeps.append,
        session=session,
    )

    operators = client.get_operators()

    assert operators[0]["name"] == "rank"
    assert session.attempts == 2
    assert sleeps == [7]


def test_internal_brain_client_caps_rate_limit_sleep():
    class EventuallyOkSession(FakeSession):
        def __init__(self):
            super().__init__()
            self.attempts = 0

        def get(self, url, params=None, timeout=None):
            self.attempts += 1
            if self.attempts == 1:
                return FakeResponse(429, {"message": "API rate limit exceeded"}, {"Retry-After": "999"})
            return FakeResponse(200, [{"name": "rank", "category": "Cross Sectional"}])

    sleeps = []
    client = InternalBrainClient(
        base_url="https://api.worldquantbrain.com",
        cookie="session=abc",
        delay_seconds=0,
        max_requests_per_run=10,
        max_rate_limit_retries=2,
        max_rate_limit_sleep_seconds=60,
        sleep=sleeps.append,
        session=EventuallyOkSession(),
    )

    client.get_operators()

    assert sleeps == [60]
