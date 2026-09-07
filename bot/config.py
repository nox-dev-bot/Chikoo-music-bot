import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

def optional_int(name):
    value = os.getenv(name, "").strip()
    return int(value) if value else None

@dataclass(frozen=True)
class Config:
    api_id: int
    api_hash: str
    bot_token: str
    owner_id: int
    owner_username: str
    log_group_id: int | None
    music_api_url: str
    music_api_key: str
    audio_quality: int
    video_quality: int
    assistant_session: str
    assistant_session_name: str
    broadcast_concurrency: int
    mongodb_uri: str
    mongodb_database: str

CFG = Config(
    api_id=int(os.getenv("API_ID", "0")),
    api_hash=os.getenv("API_HASH", ""),
    bot_token=os.getenv("BOT_TOKEN", ""),
    owner_id=int(os.getenv("OWNER_ID", "8455806295")),
    owner_username=os.getenv("OWNER_USERNAME", "nox_shadowx").lstrip("@"),
    log_group_id=optional_int("LOG_GROUP_ID"),
    music_api_url=os.getenv("MUSIC_API_URL", "https://music.yukiapi.site").rstrip("/"),
    music_api_key=os.getenv("MUSIC_API_KEY", ""),
    audio_quality=int(os.getenv("AUDIO_QUALITY", "320")),
    video_quality=int(os.getenv("VIDEO_QUALITY", "1080")),
    assistant_session=os.getenv("ASSISTANT_SESSION_STRING", ""),
    assistant_session_name=os.getenv("ASSISTANT_SESSION_NAME", "chikoo_assistant"),
    broadcast_concurrency=int(os.getenv("MAX_BROADCAST_CONCURRENCY", "8")),
    mongodb_uri=os.getenv("MONGODB_URI", ""),
    mongodb_database=os.getenv("MONGODB_DATABASE", "chikoo_music"),
)

if not CFG.api_id or not CFG.api_hash or not CFG.bot_token:
    raise RuntimeError("Set API_ID, API_HASH and BOT_TOKEN in .env")
if not CFG.mongodb_uri:
    raise RuntimeError("Set MONGODB_URI in .env")
