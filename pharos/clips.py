"""Cut a short clip around an event with ffmpeg."""
import subprocess
from pathlib import Path


def cut_clip(video: str, start: float, end: float, out: str, pad: float = 2.0) -> str:
    s = max(0.0, start - pad)
    d = (end - start) + 2 * pad
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{s:.2f}", "-i", video, "-t", f"{d:.2f}",
         "-c:v", "libx264", "-preset", "veryfast", "-an", "-movflags", "+faststart", out],
        check=True,
    )
    return out
