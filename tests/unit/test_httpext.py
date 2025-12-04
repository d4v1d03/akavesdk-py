import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Tuple

import pytest
import requests

from private.httpext import range_download


TEST_DATA = b"Hello, World! This is some test data for the client."


class _RangeHandler(BaseHTTPRequestHandler):
    def do_GET(self):  # type: ignore[override]
        range_header = self.headers.get("Range")
        if not range_header:
            self.send_response(400)
            self.end_headers()
            return

        try:
            # Expect header of form: bytes=start-end
            _, value = range_header.split("=", 1)
            start_str, end_str = value.split("-", 1)
            start, end = int(start_str), int(end_str)
        except Exception:
            self.send_response(400)
            self.end_headers()
            return

        if start < 0 or end >= len(TEST_DATA) or start > end:
            self.send_response(416)  # Requested Range Not Satisfiable
            self.end_headers()
            return

        self.send_response(206)  # Partial Content
        chunk = TEST_DATA[start : end + 1]
        self.send_header("Content-Length", str(len(chunk)))
        self.end_headers()
        self.wfile.write(chunk)

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        # Silence default HTTP server logging in tests.
        return


def _start_http_server() -> Tuple[HTTPServer, str]:
    server = HTTPServer(("127.0.0.1", 0), _RangeHandler)
    host, port = server.server_address

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    return server, f"http://{host}:{port}"


@pytest.fixture(scope="module")
def http_server():
    server, base_url = _start_http_server()
    try:
        yield base_url
    finally:
        server.shutdown()


def test_range_download_full(http_server: str):
    session = requests.Session()
    try:
        result = range_download(session, http_server, 0, len(TEST_DATA))
    finally:
        session.close()

    assert result == TEST_DATA


def test_range_download_partial(http_server: str):
    session = requests.Session()
    try:
        # "World" substring in TEST_DATA
        offset = TEST_DATA.index(b"World")
        length = len(b"World")
        result = range_download(session, http_server, offset, length)
    finally:
        session.close()

    assert result == b"World"


def test_range_download_invalid_offset(http_server: str):
    session = requests.Session()
    try:
        with pytest.raises(ValueError):
            range_download(session, http_server, -1, 5)
    finally:
        session.close()


def test_range_download_invalid_length_zero(http_server: str):
    session = requests.Session()
    try:
        with pytest.raises(ValueError):
            range_download(session, http_server, 0, 0)
    finally:
        session.close()


def test_range_download_invalid_length_negative(http_server: str):
    session = requests.Session()
    try:
        with pytest.raises(ValueError):
            range_download(session, http_server, 0, -1)
    finally:
        session.close()


