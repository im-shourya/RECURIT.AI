"""
The signing key must not reach production as a value published in this
repository, or as something short enough to guess.
"""

import pytest
from pydantic import ValidationError

from app.config import KNOWN_PLACEHOLDER_SECRETS, Settings

STRONG = "a" * 64


@pytest.mark.parametrize("placeholder", sorted(KNOWN_PLACEHOLDER_SECRETS))
def test_production_refuses_a_published_placeholder(placeholder):
    with pytest.raises(ValidationError, match="placeholder"):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY=placeholder)


def test_production_refuses_a_short_key():
    with pytest.raises(ValidationError, match="at least 32"):
        Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY="short-but-not-default")


def test_production_accepts_a_strong_key():
    assert Settings(_env_file=None, ENVIRONMENT="production", SECRET_KEY=STRONG).SECRET_KEY == STRONG


def test_environment_name_is_matched_loosely():
    """A stray capital or space must not switch the check off."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT=" Production ", SECRET_KEY="short")


def test_the_built_in_default_is_itself_refused():
    """A deployment that forgets the variable entirely must not boot."""
    with pytest.raises(ValidationError):
        Settings(_env_file=None, ENVIRONMENT="production")


def test_development_keeps_working_with_the_default():
    """Local setup should need no secret at all."""
    assert Settings(_env_file=None, ENVIRONMENT="development").SECRET_KEY
