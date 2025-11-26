import time
from unittest.mock import MagicMock, patch

import httpx
import pytest

from sdk.config import SDKError
from sdk.shared.httpext import (
    HTTPClient,
    build_query_string,
    parse_json_response,
    retry_on_http_error,
)


class TestHTTPClientInit:
    def test_http_client_initialization_defaults(self):
        client = HTTPClient()

        assert client.base_url is None
        assert isinstance(client._client, httpx.Client)  # type: ignore[attr-defined]

    def test_http_client_initialization_with_base_url_and_timeout(self):
        client = HTTPClient(base_url="https://api.example.com/", timeout=10.0, max_retries=5)

        assert client.base_url == "https://api.example.com"
        assert client._timeout == 10.0  # type: ignore[attr-defined]
        assert client._retry_config.max_attempts == 5  # type: ignore[attr-defined]


class TestHTTPClientBuildUrl:
    def test_build_url_with_base_and_relative_path(self):
        client = HTTPClient(base_url="https://api.example.com")

        full = client._build_url("/v1/items")  # type: ignore[attr-defined]
        assert full == "https://api.example.com/v1/items"

        full2 = client._build_url("v1/items")  # type: ignore[attr-defined]
        assert full2 == "https://api.example.com/v1/items"

    def test_build_url_with_absolute_url(self):
        client = HTTPClient(base_url="https://api.example.com")
        full = client._build_url("https://other.example.com/x")  # type: ignore[attr-defined]
        assert full == "https://other.example.com/x"

    def test_build_url_without_base_url(self):
        client = HTTPClient()
        assert client._build_url("/v1/items") == "/v1/items"  # type: ignore[attr-defined]


class TestHTTPClientContextManager:
    @patch("httpx.Client.request")
    def test_context_manager_closes_client(self, mock_request):
        request = httpx.Request("GET", "https://api.example.com/v1/health")
        mock_request.return_value = httpx.Response(200, request=request)

        with HTTPClient(base_url="https://api.example.com") as client:
            resp = client.get("/v1/health")
            assert resp.status_code == 200
            assert client._client.is_closed is False  # type: ignore[attr-defined]
        # closed after context exit
        assert client._client.is_closed is True  # type: ignore[attr-defined]


class TestParseJsonResponse:
    def test_parse_json_response_success(self):
        request = httpx.Request("GET", "https://api.example.com/item")
        response = httpx.Response(200, json={"name": "akave"}, request=request)

        data = parse_json_response(response)
        assert isinstance(data, dict)
        assert data["name"] == "akave"

    def test_parse_json_response_failure(self):
        request = httpx.Request("GET", "https://api.example.com/item")
        response = httpx.Response(200, content=b"not-json", request=request)

        with pytest.raises(SDKError) as exc:
            parse_json_response(response)

        assert "Failed to parse JSON response" in str(exc.value)


class TestRetryOnHttpErrorBackoff:
    def test_retry_decorator_exponential_backoff_and_success(self, mocker):
        calls = {"count": 0}

        @retry_on_http_error
        def flaky() -> int:
            calls["count"] += 1
            if calls["count"] < 3:
                raise httpx.RequestError("temporary", request=httpx.Request("GET", "https://x"))
            return 42

        sleep_mock = mocker.patch.object(time, "sleep")

        result = flaky()

        assert result == 42
        # Two retries with exponential delays: base 0.5 → 0.5, 1.0
        assert sleep_mock.call_count == 2
        delays = [args[0] for args, _ in sleep_mock.call_args_list]
        assert pytest.approx(delays[0], rel=1e-3) == 0.5
        assert pytest.approx(delays[1], rel=1e-3) == 1.0

    def test_retry_decorator_eventual_failure_raises_sdk_error(self, mocker):
        @retry_on_http_error(max_attempts=3, base_delay=0.1)
        def always_fail() -> None:
            raise httpx.RequestError("boom", request=httpx.Request("GET", "https://x"))

        sleep_mock = mocker.patch.object(time, "sleep")

        with pytest.raises(SDKError) as exc:
            always_fail()

        # Should have slept twice (between 3 attempts)
        assert sleep_mock.call_count == 2
        assert "HTTP operation failed after 3 attempts" in str(exc.value)


class TestHTTPClientRequests:
    @patch("httpx.Client.request")
    def test_get_success(self, mock_request):
        request = httpx.Request("GET", "https://api.example.com/v1/items")
        response = httpx.Response(200, json={"items": []}, request=request)
        mock_request.return_value = response

        client = HTTPClient(base_url="https://api.example.com")
        resp = client.get("/v1/items")

        assert resp.status_code == 200
        mock_request.assert_called_once()
        _, kwargs = mock_request.call_args
        assert kwargs["method"] == "GET"
        assert kwargs["url"] == "https://api.example.com/v1/items"

    @patch("httpx.Client.request")
    def test_get_timeout_raises_sdk_error(self, mock_request):
        mock_request.side_effect = httpx.TimeoutException("timeout")

        client = HTTPClient(base_url="https://api.example.com", timeout=1.0)

        with pytest.raises(SDKError) as exc:
            client.get("/v1/items")

        assert "timed out" in str(exc.value)


class TestBuildQueryString:
    def test_build_query_string_empty(self):
        assert build_query_string({}) == ""
        assert build_query_string(None) == ""

    def test_build_query_string_simple_and_list(self):
        qs = build_query_string({"q": "akave", "tags": ["python", "sdk"], "page": 1})
        assert qs.startswith("?")
        # Order is not guaranteed, so check components:
        assert "q=akave" in qs
        assert "tags=python" in qs
        assert "tags=sdk" in qs
        assert "page=1" in qs


