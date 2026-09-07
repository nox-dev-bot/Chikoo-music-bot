import asyncio
import random
import time
from collections import defaultdict, deque
from dataclasses import dataclass

@dataclass
class Track:
    title: str
    duration: str
    duration_sec: int
    video_id: str
    thumb: str = ""
    link: str = ""
    media_type: str = "audio"

class ChatPlayer:
    def __init__(self, streamer):
        self.streamer = streamer
        self.queues = defaultdict(deque)
        self.current = {}
        self.history = defaultdict(list)
        self.started = {}
        self.paused_at = {}
        self.paused_total = defaultdict(float)
        self.volumes = defaultdict(lambda: 100)
        self.loops = defaultdict(lambda: "off")
        self.locks = defaultdict(asyncio.Lock)

    def _track(self, item):
        return Track(
            title=item["title"],
            duration=item["duration"],
            duration_sec=item["duration_sec"],
            video_id=item["id"],
            thumb=item.get("thumb", ""),
            link=item.get("link", ""),
            media_type=item.get("media_type", "audio"),
        )

    async def add(self, chat_id, item, force=False):
        track = self._track(item)
        async with self.locks[chat_id]:
            if force or chat_id not in self.current:
                if chat_id in self.current and not force:
                    self.queues[chat_id].append(track)
                else:
                    self.current[chat_id] = track
                    self.history[chat_id].append(track)
                    await self._start(chat_id, track)
            else:
                self.queues[chat_id].append(track)
        return track

    async def _start(self, chat_id, track, seek=0):
        await self.streamer.play(chat_id, track.video_id, seek, media_type=track.media_type)
        self.started[chat_id] = time.monotonic() - seek
        self.paused_at.pop(chat_id, None)
        self.paused_total[chat_id] = 0

    async def next(self, chat_id):
        async with self.locks[chat_id]:
            mode = self.loops[chat_id]
            cur = self.current.get(chat_id)
            if mode == "one" and cur:
                await self._start(chat_id, cur)
                return cur

            if cur and mode == "all":
                self.queues[chat_id].append(cur)

            if not self.queues[chat_id]:
                self.current.pop(chat_id, None)
                try:
                    await self.streamer.stop_call(chat_id)
                except Exception:
                    pass
                return None

            track = self.queues[chat_id].popleft()
            self.current[chat_id] = track
            self.history[chat_id].append(track)
            await self._start(chat_id, track)
            return track

    async def on_stream_end(self, chat_id):
        if chat_id in self.current:
            await self.next(chat_id)

    async def pause(self, chat_id):
        if chat_id not in self.current:
            raise RuntimeError("ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ")
        await self.streamer.pause(chat_id)
        self.paused_at[chat_id] = time.monotonic()

    async def resume(self, chat_id):
        if chat_id not in self.current:
            raise RuntimeError("ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ")
        await self.streamer.resume(chat_id)
        self.paused_at.pop(chat_id, None)

    def position(self, chat_id):
        if chat_id not in self.current or chat_id not in self.started:
            return 0
        if chat_id in self.paused_at:
            return max(0, int(self.paused_at[chat_id] - self.started[chat_id]))
        return max(0, int(time.monotonic() - self.started[chat_id]))

    async def seek(self, chat_id, delta):
        cur = self.current.get(chat_id)
        if not cur:
            raise RuntimeError("ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ")
        target = max(0, min(cur.duration_sec or 10**9, self.position(chat_id) + int(delta)))
        await self.streamer.change(
            chat_id, cur.video_id, target, media_type=cur.media_type
        )
        self.started[chat_id] = time.monotonic() - target
        self.paused_at.pop(chat_id, None)
        return target

    async def replay(self, chat_id):
        cur = self.current.get(chat_id)
        if not cur:
            raise RuntimeError("ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ")
        await self._start(chat_id, cur)

    async def previous(self, chat_id):
        hist = self.history[chat_id]
        cur = self.current.get(chat_id)
        if len(hist) < 2:
            return await self.replay(chat_id)
        if cur is hist[-1]:
            hist.pop()
        track = hist[-1]
        self.current[chat_id] = track
        await self._start(chat_id, track)
        return track

    async def stop(self, chat_id):
        self.queues[chat_id].clear()
        self.current.pop(chat_id, None)
        self.history[chat_id].clear()
        self.started.pop(chat_id, None)
        self.paused_at.pop(chat_id, None)
        await self.streamer.stop_call(chat_id)

    async def clear(self, chat_id):
        self.queues[chat_id].clear()

    async def shuffle(self, chat_id):
        values = list(self.queues[chat_id])
        random.shuffle(values)
        self.queues[chat_id] = deque(values)

    async def volume(self, chat_id, delta):
        new_value = max(0, min(200, self.volumes[chat_id] + int(delta)))
        self.volumes[chat_id] = new_value
        await self.streamer.volume(chat_id, new_value)
        return new_value

    def queue_text(self, chat_id):
        cur = self.current.get(chat_id)
        rows = ["📜 <b>ǫᴜᴇᴜᴇ</b>"]
        if cur:
            rows.append(f"▶️ <b>ɴᴏᴡ:</b> {cur.title}")
        if self.queues[chat_id]:
            for i, track in enumerate(self.queues[chat_id], 1):
                rows.append(f"{i}. {track.title} — <code>{track.duration}</code>")
        else:
            rows.append("ᴇᴍᴘᴛʏ")
        return "\n".join(rows)
