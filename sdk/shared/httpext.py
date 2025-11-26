import logging
import time
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Dict, Iterable, Mapping, Optional, Type, TypeVar

import httpx
from urllib.parse import urlencode, urljoin

from ..config import SDKError


_LOG = logging.getLogger(__name__)

R = TypeVar("R")


class HTTPClientError(SDKError):
    """HTTP-specific error raised by :class:`HTTPClient` and helpers."""


@dataclass
class RetryConfig:
    """Configuration for HTTP retry behaviour."""

    max_attempts: int = 3
    base_delay: float = 0.5  # seconds


def retry_on_http_error(
    fn: Optional[Callable[..., R]] = None,
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    retry_exceptions: Iterable[Type[BaseException]] = (httpx.RequestError, SDKError),
) -> Callable[..., R]:
    """Retry a callable on HTTP-related errors using exponential backoff."""

    def decorator(func: Callable[..., R]) -> Callable[..., R]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> R:
            attempts = 0
            last_error: Optional[BaseException] = None
            exception_types = tuple(retry_exceptions)

            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exception_types as exc:  # type: ignore[arg-type]
                    last_error = exc
                    attempts += 1

                    if attempts >= max_attempts:
                        _LOG.error(
                            "HTTP operation failed after %d attempts: %s",
                            attempts,
                            exc,
                        )
                        # If the underlying error is already an SDKError, just re-raise it
                        if isinstance(exc, SDKError):
                            raise
                        raise HTTPClientError(
                            f"HTTP operation failed after {attempts} attempts: {exc}"
                        ) from exc

                    delay = base_delay * (2 ** (attempts - 1))
                    _LOG.debug(
                        "HTTP operation failed (attempt %d/%d), retrying in %.2fs: %s",
                        attempts,
                        max_attempts,
                        delay,
                        exc,
                    )
                    time.sleep(delay)

            # Should never reach here because we either return or raise above
            assert last_error is not None
            raise HTTPClientError(f"HTTP operation failed: {last_error}") from last_error

        return wrapper

    # Support both @retry_on_http_error and @retry_on_http_error(...)
    if callable(fn):
        return decorator(fn)
    return decorator


class HTTPClient:
    """Small HTTP client wrapper with pooling, retries and SDK-style errors."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = base_url.rstrip("/") if base_url else None
        self._timeout = timeout
        self._retry_config = RetryConfig(max_attempts=max_retries)

        # Use a plain client; URL resolution is handled by _build_url.
        self._client = httpx.Client(timeout=self._timeout)

    def close(self) -> None:
        """Close the underlying :class:`httpx.Client` instance."""
        self._client.close()

    def __enter__(self) -> "HTTPClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # type: ignore[override]
        self.close()

    @retry_on_http_error
    def get(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """Send an HTTP ``GET`` request.

        Args:
            url: Request URL or path. If a ``base_url`` was configured, relative
                paths are resolved against it.
            params: Optional query-string parameters.
            headers: Optional HTTP headers to include in the request.
            timeout: Optional per-request timeout in seconds. Falls back to the
                default timeout configured on the client.

        Returns:
            The underlying :class:`httpx.Response` object.

        Raises:
            HTTPClientError: If the request fails permanently after retries or
                a timeout/HTTP error occurs.
        """
        return self._request("GET", url, params=params, headers=headers, timeout=timeout)

    @retry_on_http_error
    def post(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """Send an HTTP ``POST`` request.

        Args:
            url: Request URL or path.
            params: Optional query-string parameters.
            json: Optional JSON-serialisable body to send.
            data: Optional raw body or form data to send.
            headers: Optional HTTP headers to include in the request.
            timeout: Optional per-request timeout in seconds.

        Returns:
            The underlying :class:`httpx.Response` object.

        Raises:
            HTTPClientError: If the request fails permanently after retries or
                a timeout/HTTP error occurs.
        """
        return self._request(
            "POST",
            url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
        )

    @retry_on_http_error
    def put(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """Send an HTTP ``PUT`` request.

        Args:
            url: Request URL or path.
            params: Optional query-string parameters.
            json: Optional JSON-serialisable body to send.
            data: Optional raw body or form data to send.
            headers: Optional HTTP headers to include in the request.
            timeout: Optional per-request timeout in seconds.

        Returns:
            The underlying :class:`httpx.Response` object.

        Raises:
            HTTPClientError: If the request fails permanently after retries or
                a timeout/HTTP error occurs.
        """
        return self._request(
            "PUT",
            url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
        )

    @retry_on_http_error
    def delete(
        self,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """Send an HTTP ``DELETE`` request.

        Args:
            url: Request URL or path.
            params: Optional query-string parameters.
            headers: Optional HTTP headers to include in the request.
            timeout: Optional per-request timeout in seconds.

        Returns:
            The underlying :class:`httpx.Response` object.

        Raises:
            HTTPClientError: If the request fails permanently after retries or
                a timeout/HTTP error occurs.
        """
        return self._request("DELETE", url, params=params, headers=headers, timeout=timeout)

    def _request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        data: Any = None,
        headers: Optional[Mapping[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> httpx.Response:
        """Perform the HTTP request and normalise errors into :class:`SDKError`."""
        request_timeout = timeout if timeout is not None else self._timeout

        try:
            full_url = self._build_url(url)
            _LOG.debug("HTTP %s %s params=%s", method, full_url, params)
            response = self._client.request(
                method=method,
                url=full_url,
                params=params,
                json=json,
                data=data,
                headers=dict(headers) if headers is not None else None,
                timeout=request_timeout,
            )
            response.raise_for_status()
            return response

        except httpx.TimeoutException as exc:
            _LOG.warning(
                "HTTP %s %s timed out after %.2fs",
                method,
                url,
                request_timeout,
            )
            raise HTTPClientError(
                f"HTTP {method} {url} timed out after {request_timeout:.2f}s"
            ) from exc

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            text = exc.response.text
            _LOG.error(
                "HTTP %s %s failed with status %s: %s",
                method,
                url,
                status_code,
                text,
            )
            raise HTTPClientError(
                f"HTTP {method} {url} failed with status {status_code}: {text}"
            ) from exc

        except httpx.RequestError as exc:
            _LOG.error("HTTP %s %s request error: %s", method, url, exc)
            raise HTTPClientError(f"HTTP {method} {url} request error: {exc}") from exc

    def _build_url(self, url: str) -> str:
        """
        Build an absolute URL using the configured ``base_url`` when necessary.

        If ``base_url`` is set and ``url`` is a relative path or does not include a
        scheme, the two are joined. Otherwise, ``url`` is returned as-is.
        """
        if not self.base_url:
            return url

        if url.startswith("http://") or url.startswith("https://"):
            return url

        # Ensure we don't end up with duplicate slashes.
        base = self.base_url.rstrip("/") + "/"
        path = url.lstrip("/")
        return urljoin(base, path)


def parse_json_response(response: httpx.Response) -> Any:
    """Parse JSON from an :class:`httpx.Response` with :class:`SDKError` on failure.

    Args:
        response: HTTP response to decode JSON from.

    Returns:
        The decoded JSON value (usually a ``dict`` or ``list``).

    Raises:
        SDKError: If decoding fails due to invalid JSON.

    Example:
        >>> from sdk.shared.httpext import HTTPClient, parse_json_response
        >>> client = HTTPClient(base_url="https://api.example.com")
        >>> response = client.get("/items/1")
        >>> item = parse_json_response(response)
    """
    try:
        return response.json()
    except ValueError as exc:
        _LOG.error("Failed to parse JSON response from %s: %s", response.request.url, exc)
        raise SDKError(f"Failed to parse JSON response: {exc}") from exc


def build_query_string(params: Optional[Mapping[str, Any]] = None) -> str:
    """Build a URL query string from mapping parameters.

    ``None`` values are excluded, and the implementation uses
    :func:`urllib.parse.urlencode` with ``doseq=True`` so that list and tuple
    values are expanded into repeated query parameters.

    Args:
        params: Mapping of query parameter names to values. Values may be scalars
            or iterables (e.g. ``list`` or ``tuple``).

    Returns:
        A query string starting with ``?`` or an empty string if there are no
        effective parameters.

    Example:
        >>> from sdk.shared.httpext import build_query_string
        >>> build_query_string({'q': 'akave', 'tags': ['python', 'sdk']})
        '?q=akave&tags=python&tags=sdk'
    """
    if not params:
        return ""

    # Filter out None values to avoid sending "param=None" in the URL
    clean_params: Dict[str, Any] = {
        key: value for key, value in params.items() if value is not None
    }

    if not clean_params:
        return ""

    return "?" + urlencode(clean_params, doseq=True)


