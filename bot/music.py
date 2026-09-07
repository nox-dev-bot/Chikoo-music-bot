import aiohttp
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import quote

from .config import CFG

VIDEO_ID_RE = re.compile(
    r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{6,})"
)

def extract_video_id(value):
    value = value.strip()
    match = VIDEO_ID_RE.search(value)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9_-]{6,}", value):
        return value
    return None

def stream_url(video_id, media_type="audio", quality=None):
    if not CFG.music_api_key:
        raise RuntimeError("MUSIC_API_KEY is not configured")
    quality = quality or (
        CFG.audio_quality if media_type == "audio" else CFG.video_quality
    )
    return (
        f"{CFG.music_api_url}/stream/{quote(video_id)}"
        f"?key={quote(CFG.music_api_key)}"
        f"&type={media_type}&quality={quality}"
    )

async def _download(url, suffix, min_size=10000):
    fd, path = tempfile.mkstemp(prefix="chikoo_", suffix=suffix)
    os.close(fd)
    try:
        timeout = aiohttp.ClientTimeout(total=600)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    body = await resp.text()
                    raise RuntimeError(
                        f"music api http {resp.status}: {body[:180]}"
                    )
                with open(path, "wb") as out:
                    async for chunk in resp.content.iter_chunked(131072):
                        out.write(chunk)
        if Path(path).stat().st_size < min_size:
            raise RuntimeError("upstream returned an unexpectedly small file")
        return path
    except Exception:
        try:
            os.remove(path)
        except OSError:
            pass
        raise

async def fetch_audio(video_id):
    return await _download(
        stream_url(video_id, "audio", CFG.audio_quality),
        ".mp3",
    )

async def fetch_thumbnail(url):
    if not url:
        return None
    try:
        return await _download(url, ".jpg", min_size=500)
    except Exception:
        return None
