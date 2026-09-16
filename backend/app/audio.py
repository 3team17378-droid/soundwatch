import shutil
import subprocess
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

from app.core.config import settings

MIMES = {
    ".wav": {"audio/wav", "audio/x-wav", "audio/wave", "audio/vnd.wave"},
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".m4a": {"audio/mp4", "audio/x-m4a"},
    ".flac": {"audio/flac", "audio/x-flac"},
    ".ogg": {"audio/ogg", "application/ogg"},
}


class AudioError(ValueError):
    pass


def validate_header(filename, mime):
    # Reject path-like client filenames, even though none are used as filesystem paths.
    if not filename or any(c in filename for c in ["/", "\\", "\x00"]):
        raise AudioError("유효하지 않은 파일명입니다.")
    suffix = Path(filename).suffix.lower()
    if suffix not in MIMES:
        raise AudioError("WAV, MP3, M4A, FLAC, OGG 파일만 업로드할 수 있습니다.")
    if mime not in MIMES[suffix]:
        raise AudioError("파일 확장자와 MIME 유형이 일치하지 않습니다.")
    return suffix


def ffmpeg_binary():
    if shutil.which("ffmpeg"):
        return shutil.which("ffmpeg")
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def decode(path: Path):
    # Decode at bounded sample rate/channel count and duration to cap memory use.
    # No shell, network protocols disabled, strict decoder errors rejected.
    command = [
        ffmpeg_binary(),
        "-nostdin",
        "-v",
        "error",
        "-xerror",
        "-err_detect",
        "explode",
        "-protocol_whitelist",
        "file,pipe",
        "-i",
        str(path),
        "-t",
        str(settings.max_duration_seconds + 1),
        "-vn",
        "-ac",
        "1",
        "-ar",
        str(settings.sample_rate),
        "-f",
        "f32le",
        "pipe:1",
    ]
    try:
        result = subprocess.run(command, capture_output=True, timeout=45, check=True)
        y = np.frombuffer(result.stdout, dtype="<f4").copy()
    except (subprocess.SubprocessError, OSError, ValueError) as exc:
        raise AudioError("오디오를 디코딩할 수 없습니다. 손상되었거나 지원하지 않는 파일입니다.") from exc
    if len(y) < 256 or not np.isfinite(y).all():
        raise AudioError("비어 있거나 너무 짧은 오디오입니다 (최소 16ms).")
    if len(y) / settings.sample_rate > settings.max_duration_seconds:
        raise AudioError(f"최대 재생 시간 {settings.max_duration_seconds}초를 초과했습니다.")
    return y


def dbfs(amplitude):
    return float(20 * np.log10(max(float(amplitude), 1e-6)))


def extract(y: np.ndarray, sr: int):
    rms = float(np.sqrt(np.mean(y.astype(np.float64) ** 2)))
    peak = float(np.max(np.abs(y)))
    frame_rms = librosa.feature.rms(y=y, frame_length=1024, hop_length=512)[0]
    mel = librosa.power_to_db(
        librosa.feature.melspectrogram(y=y, sr=sr, n_fft=1024, hop_length=512, n_mels=64), ref=1.0
    )
    indices = np.linspace(0, len(y) - 1, min(len(y), 500), dtype=int)
    mel_indices = np.linspace(0, mel.shape[1] - 1, min(mel.shape[1], 160), dtype=int)
    spectral = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    centroid = float(np.sum(freqs * spectral) / max(float(spectral.sum()), 1e-10))
    return {
        "rms": rms,
        "peak_amplitude": peak,
        "average_dbfs": dbfs(rms),
        "maximum_dbfs": dbfs(peak),
        "silence_ratio": float(np.mean(frame_rms < 0.001)),
        "duration": len(y) / sr,
        "centroid": centroid,
        "zcr": float(np.mean(np.diff(np.signbit(y)) != 0)),
        "modulation": float(np.std(frame_rms) / max(float(np.mean(frame_rms)), 1e-8)),
        "waveform": y[indices].round(5).tolist(),
        "log_mel": mel[:, mel_indices].round(2).tolist(),
        "sample_rate": sr,
        "preprocessing_version": "mono-16k-mel64-fft1024-hop512-v1",
    }


def write_synthetic(path, kind=0):
    sr = 16000
    t = np.arange(sr * 3) / sr
    rng = np.random.default_rng(42 + kind)
    y = 0.2 * np.sin(2 * np.pi * (180 + 300 * kind) * t) * (
        0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)
    ) + 0.015 * rng.normal(size=len(t))
    sf.write(path, y, sr)
