"""
tests/test_db_adapter.py
Unit tests for database adapter factory and URL normalization (P1-05).
"""
from __future__ import annotations

from src.api.db.adapter import (
    PostgreSQLAdapter,
    SQLiteAdapter,
    make_adapter,
    normalize_database_url,
)


def test_make_adapter_sqlite():
    a = make_adapter("sqlite:///data/bid.sqlite3")
    assert isinstance(a, SQLiteAdapter)


def test_make_adapter_postgresql():
    a = make_adapter("postgresql://user:pass@localhost:5432/bid")
    assert isinstance(a, PostgreSQLAdapter)


def test_normalize_relative_sqlite_url():
    out = normalize_database_url("sqlite:///data/bid.sqlite3")
    assert out.startswith("sqlite:///")
    assert "bid.sqlite3" in out


def test_normalize_non_sqlite_url_unchanged():
    url = "postgresql://user:pass@localhost:5432/bid"
    assert normalize_database_url(url) == url
