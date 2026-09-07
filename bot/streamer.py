from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.types import AudioQuality, VideoQuality

from .config import CFG
from .music import stream_url


def _audio_quality():
    # Yuki's requested audio quality controls the source; PyTgCalls still
    # transcodes the call audio to Telegram's supported call format.
    return AudioQuality.HIGH


def _video_quality():
    # Select the closest PyTgCalls output quality supported by the installed
    # library. The upstream source may be 1080p, but Telegram/PyTgCalls may
    # negotiate a lower call-video resolution on some clients/versions.
    requested = int(CFG.video_quality or 720)
    if requested >= 1080 and hasattr(VideoQuality, "FHD_1080p"):
        return VideoQuality.FHD_1080p
    if requested >= 720 and hasattr(VideoQuality, "HD_720p"):
        return VideoQuality.HD_720p
    if requested >= 480 and hasattr(VideoQuality, "SD_480p"):
        return VideoQuality.SD_480p
    if hasattr(VideoQuality, "SD_360p"):
        return VideoQuality.SD_360p
    return None


class AssistantStreamer:
    def __init__(self):
        self.client = None
        self.calls = None
        self.ready = False
        self.on_end_callback = None

    def set_on_end(self, callback):
        self.on_end_callback = callback

    async def start(self):
        if not CFG.assistant_session:
            print("Assistant streaming disabled: ASSISTANT_SESSION_STRING is empty.")
            return

        self.client = Client(
            CFG.assistant_session_name,
            api_id=CFG.api_id,
            api_hash=CFG.api_hash,
            session_string=CFG.assistant_session,
        )
        self.calls = PyTgCalls(self.client)

        @self.calls.on_stream_end()
        async def _stream_end(_, update):
            if self.on_end_callback:
                await self.on_end_callback(update.chat_id)

        await self.client.start()
        self.calls.start()
        self.ready = True
        print("Assistant voice/video streamer started.")

    async def stop(self):
        if not self.ready:
            return
        try:
            self.calls.stop()
        except Exception:
            pass
        try:
            await self.client.stop()
        except Exception:
            pass
        self.ready = False

    def _require(self):
        if not self.ready:
            raise RuntimeError(
                "Assistant streaming is not configured. "
                "Set ASSISTANT_SESSION_STRING and restart the bot."
            )

    def _media(self, video_id, seek=0, media_type="audio"):
        media_type = media_type if media_type in {"audio", "video"} else "audio"
        url = stream_url(
            video_id,
            media_type,
            CFG.audio_quality if media_type == "audio" else CFG.video_quality,
        )
        ffmpeg = f"-ss {max(0, int(seek))}" if seek > 0 else ""
        if media_type == "video":
            quality = _video_quality()
            if quality is None:
                return MediaStream(url, _audio_quality(), ffmpeg_parameters=ffmpeg)
            return MediaStream(
                url,
                _audio_quality(),
                quality,
                ffmpeg_parameters=ffmpeg,
            )
        return MediaStream(
            url,
            _audio_quality(),
            ffmpeg_parameters=ffmpeg,
        )

    async def play(self, chat_id, video_id, seek=0, media_type="audio"):
        self._require()
        media = self._media(video_id, seek, media_type)
        self.calls.play(chat_id, media)

    async def change(self, chat_id, video_id, seek=0, media_type="audio"):
        self._require()
        media = self._media(video_id, seek, media_type)
        if hasattr(self.calls, "change_stream"):
            self.calls.change_stream(chat_id, media)
        else:
            self.calls.play(chat_id, media)

    async def pause(self, chat_id):
        self._require()
        self.calls.pause_stream(chat_id)

    async def resume(self, chat_id):
        self._require()
        self.calls.resume_stream(chat_id)

    async def volume(self, chat_id, value):
        self._require()
        value = max(0, min(200, int(value)))
        self.calls.change_volume_call(chat_id, value)

    async def stop_call(self, chat_id):
        self._require()
        if hasattr(self.calls, "leave_group_call"):
            self.calls.leave_group_call(chat_id)
        elif hasattr(self.calls, "leave_call"):
            self.calls.leave_call(chat_id)


streamer = AssistantStreamer()
