"""
Every endpoint spends Gemini quota on an arbitrary repository URL, so the
service must not answer cross-origin requests from any website.
"""
import pytest
from fastapi.middleware.cors import CORSMiddleware

from main import app, parse_allowed_origins


def test_wildcard_is_refused():
    with pytest.raises(RuntimeError, match="cannot be"):
        parse_allowed_origins("https://recruitai.example, *")


def test_origins_are_split_and_trimmed():
    assert parse_allowed_origins(" https://a.example ,https://b.example,, ") == [
        "https://a.example",
        "https://b.example",
    ]


def test_unset_allows_no_cross_origin_callers():
    """The bundled page is same-origin, so an empty list still serves it."""
    assert parse_allowed_origins("") == []


def test_middleware_sends_no_credentials_and_no_wildcard():
    cors = next(m for m in app.user_middleware if m.cls is CORSMiddleware)
    assert cors.kwargs["allow_credentials"] is False
    assert "*" not in cors.kwargs["allow_origins"]
