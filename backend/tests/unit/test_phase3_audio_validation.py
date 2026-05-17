import pytest

from app.core.errors import ApiError
from app.voice.audio_utils import validate_audio_upload


def test_audio_rejects_upload_over_configured_limit():
    with pytest.raises(ApiError) as exc:
        validate_audio_upload(b"0" * (9 * 1024 * 1024), "audio/webm", max_upload_mb=8)

    assert exc.value.status_code == 413
    assert exc.value.code == "AUDIO_TOO_LARGE"


def test_audio_rejects_unsupported_mime_type():
    with pytest.raises(ApiError) as exc:
        validate_audio_upload(b"audio", "application/octet-stream", max_upload_mb=8)

    assert exc.value.status_code == 415
    assert exc.value.code == "UNSUPPORTED_AUDIO_FORMAT"
