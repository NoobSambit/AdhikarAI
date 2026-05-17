import asyncio
import json
import shlex

from app.core.config import Settings
from app.core.errors import ApiError
from app.schemas.voice import AsrResponseModel
from app.voice.audio_utils import audio_duration_ms, cleanup_temp_files, resample_to_48khz_mono, write_temp_audio


class WhisperCppProvider:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def transcribe(self, audio: bytes, mime_type: str, language_hint: str | None) -> AsrResponseModel:
        input_path = await write_temp_audio(audio, mime_type)
        wav_path = None
        try:
            wav_path = await resample_to_48khz_mono(input_path)
            command = [
                self.settings.whisper_cpp_binary,
                "-m",
                self.settings.whisper_cpp_model_path,
                "-f",
                str(wav_path),
                *shlex.split(self.settings.whisper_cpp_args),
            ]
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=self.settings.asr_timeout_seconds)
            except asyncio.TimeoutError as exc:
                process.kill()
                raise ApiError(504, "ASR_TIMEOUT", "Speech service is slow. Please try again or type your message.", "audio") from exc
            if process.returncode != 0:
                raise ApiError(502, "ASR_PROVIDER_ERROR", "Speech service failed. Please try again or type your message.", "audio", stderr.decode("utf-8", "ignore")[-500:])
            transcript, confidence = _parse_whisper_output(stdout.decode("utf-8", "ignore"))
            return AsrResponseModel(
                transcript=transcript,
                detected_language_code=language_hint or "en",
                confidence=confidence,
                duration_ms=await audio_duration_ms(wav_path),
                provider="local",
                confidence_method="provider_default" if confidence == 0.80 else "token_probability",
            )
        finally:
            cleanup_temp_files(input_path, wav_path)


def _parse_whisper_output(output: str) -> tuple[str, float]:
    try:
        payload = json.loads(output)
    except json.JSONDecodeError:
        return output.strip(), 0.80 if output.strip() else 0.0
    transcript = (payload.get("text") or payload.get("transcription") or "").strip()
    tokens = payload.get("tokens") or []
    probs = [float(token["probability"]) for token in tokens if isinstance(token, dict) and "probability" in token]
    confidence = sum(probs) / len(probs) if probs else (0.80 if transcript else 0.0)
    return transcript, max(0.0, min(1.0, confidence))
