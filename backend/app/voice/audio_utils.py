from pathlib import Path
import asyncio
import json
import tempfile
from uuid import uuid4

from app.core.errors import ApiError

SUPPORTED_AUDIO_MIME_TYPES = {
    "audio/webm",
    "audio/wav",
    "audio/x-wav",
    "audio/mpeg",
    "audio/mp3",
    "audio/mp4",
    "audio/mpga",
    "audio/m4a",
    "audio/ogg",
}
TEMP_AUDIO_DIR = Path("/tmp/adhikarai/audio")


def validate_audio_upload(audio: bytes, mime_type: str | None, max_upload_mb: int) -> None:
    if len(audio) > max_upload_mb * 1024 * 1024:
        raise ApiError(
            413,
            "AUDIO_TOO_LARGE",
            "Audio is too large. Please speak for less than 20 seconds. You can also type your message.",
            "audio",
        )
    if not mime_type or mime_type.split(";")[0].strip().lower() not in SUPPORTED_AUDIO_MIME_TYPES:
        raise ApiError(
            415,
            "UNSUPPORTED_AUDIO_FORMAT",
            "This audio format is not supported. Please record again or type your message.",
            "audio",
        )


def temp_audio_path(suffix: str) -> Path:
    TEMP_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    safe_suffix = suffix if suffix.startswith(".") else f".{suffix}"
    return TEMP_AUDIO_DIR / f"{uuid4().hex}{safe_suffix}"


async def write_temp_audio(audio: bytes, mime_type: str) -> Path:
    suffix = _suffix_for_mime(mime_type)
    path = temp_audio_path(suffix)
    path.write_bytes(audio)
    return path


async def resample_to_48khz_mono(input_path: Path) -> Path:
    output_path = temp_audio_path(".wav")
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "48000",
        str(output_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode != 0:
        raise ApiError(502, "AUDIO_RESAMPLE_FAILED", "Audio could not be processed. Please try again or type.", "audio", stderr.decode("utf-8", "ignore")[-500:])
    return output_path


async def audio_duration_ms(path: Path) -> int:
    process = await asyncio.create_subprocess_exec(
        "ffprobe",
        "-v",
        "quiet",
        "-print_format",
        "json",
        "-show_format",
        str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await process.communicate()
    if process.returncode != 0:
        return 0
    try:
        duration = float(json.loads(stdout.decode()).get("format", {}).get("duration", 0))
    except (ValueError, json.JSONDecodeError):
        return 0
    return int(duration * 1000)


def cleanup_temp_files(*paths: Path | None) -> None:
    for path in paths:
        if path and path.exists():
            try:
                path.unlink()
            except OSError:
                pass


def _suffix_for_mime(mime_type: str) -> str:
    mime = mime_type.split(";")[0].strip().lower()
    return {
        "audio/webm": ".webm",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/mp3": ".mp3",
        "audio/mp4": ".mp4",
        "audio/mpga": ".mpga",
        "audio/m4a": ".m4a",
        "audio/ogg": ".ogg",
    }.get(mime, Path(tempfile.gettempdir()).suffix or ".audio")
