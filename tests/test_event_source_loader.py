"""
tests/test_event_source_loader.py
Unit tests for bid.events.source_loader — JSON fetching and parsing.
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from bid.events.models import EventSource, SourceType
from bid.events.source_loader import (
    detect_source_type,
    fetch_json_from_url,
    load_event_source,
    load_json_from_file,
)


# ---------------------------------------------------------------------------
# Sample JSON data
# ---------------------------------------------------------------------------

VALID_SCHEDULE_JSON = {
    "time": "sobota, 16:17:23",
    "title": "Sobota KONKURS",
    "schedule": [
        {
            "id": "event-26-1",
            "type": "#cba9ff",
            "name": "Kankan",
            "time": "12:00 - 12:04",
            "status": "was",
            "start": 1773486000000,
            "duration": 240000,
        },
        {
            "id": "event-26-3",
            "type": "#abdfff",
            "name": "Grupa ELORE",
            "time": "12:06 - 12:13",
            "status": "was",
            "start": 1773486360000,
            "duration": 420000,
        },
    ],
    "last_update": "2026-03-14 16:17:23",
}


# ---------------------------------------------------------------------------
# detect_source_type
# ---------------------------------------------------------------------------

class TestDetectSourceType:
    def test_http_url(self):
        assert detect_source_type("http://example.com/data.json") == SourceType.URL

    def test_https_url(self):
        assert detect_source_type("https://www.yapa.art.pl/2026/obsuwa/json2.php?idKoncertu=26") == SourceType.URL

    def test_local_file_relative(self):
        assert detect_source_type("./data/schedule.json") == SourceType.FILE

    def test_local_file_absolute(self):
        assert detect_source_type("C:\\data\\schedule.json") == SourceType.FILE
        assert detect_source_type("/home/user/schedule.json") == SourceType.FILE

    def test_whitespace_trimmed(self):
        assert detect_source_type("  https://example.com/  ") == SourceType.URL


# ---------------------------------------------------------------------------
# load_json_from_file
# ---------------------------------------------------------------------------

class TestLoadJsonFromFile:
    def test_valid_json(self, tmp_path):
        json_file = tmp_path / "test.json"
        json_file.write_text(json.dumps(VALID_SCHEDULE_JSON), encoding="utf-8")
        data = load_json_from_file(json_file)
        assert data["title"] == "Sobota KONKURS"
        assert len(data["schedule"]) == 2

    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            load_json_from_file(tmp_path / "nonexistent.json")

    def test_invalid_json(self, tmp_path):
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("{invalid json!!}", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load_json_from_file(bad_file)

    def test_utf8_content(self, tmp_path):
        data = {"title": "Zażółć gęślą jaźń", "schedule": []}
        json_file = tmp_path / "unicode.json"
        json_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        loaded = load_json_from_file(json_file)
        assert loaded["title"] == "Zażółć gęślą jaźń"


# ---------------------------------------------------------------------------
# fetch_json_from_url (mocked)
# ---------------------------------------------------------------------------

class TestFetchJsonFromUrl:
    @patch("bid.events.source_loader.urllib.request.urlopen")
    def test_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps(VALID_SCHEDULE_JSON).encode()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        data = fetch_json_from_url("https://example.com/test.json")
        assert data["title"] == "Sobota KONKURS"

    @patch("bid.events.source_loader.urllib.request.urlopen")
    def test_non_200_raises(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 404
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with pytest.raises(ValueError, match="HTTP 404"):
            fetch_json_from_url("https://example.com/notfound")

    @patch("bid.events.source_loader.urllib.request.urlopen")
    def test_invalid_json_raises(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b"not json"
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        with pytest.raises(ValueError, match="Invalid JSON"):
            fetch_json_from_url("https://example.com/bad")


# ---------------------------------------------------------------------------
# load_event_source
# ---------------------------------------------------------------------------

class TestLoadEventSource:
    def test_load_file_source(self, tmp_path):
        json_file = tmp_path / "schedule.json"
        json_file.write_text(json.dumps(VALID_SCHEDULE_JSON), encoding="utf-8")

        source = EventSource(
            location=str(json_file),
            source_type=SourceType.FILE,
        )
        schedule = load_event_source(source)
        assert schedule.title == "Sobota KONKURS"
        assert len(schedule.events) == 2
        assert source.schedule is not None
        assert source.last_loaded is not None
        assert source.error is None

    def test_load_missing_file_sets_error(self, tmp_path):
        source = EventSource(
            location=str(tmp_path / "missing.json"),
            source_type=SourceType.FILE,
        )
        with pytest.raises(FileNotFoundError):
            load_event_source(source)
        assert source.error is not None
