import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.config import Settings
from app.integrations.youtube_oauth import STATE_ALGORITHM, decode_state


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret="test-secret",
        youtube_client_id="test-client",
        youtube_client_secret="test-secret",
    )


def test_decode_state_valid(settings: Settings):
    channel_id = uuid.uuid4()
    state = jwt.encode(
        {
            "channel_id": str(channel_id),
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.jwt_secret,
        algorithm=STATE_ALGORITHM,
    )
    assert decode_state(settings, state) == channel_id


def test_decode_state_invalid(settings: Settings):
    with pytest.raises(ValueError, match="유효하지 않은"):
        decode_state(settings, "invalid-state")
