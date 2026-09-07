# Copyright (C) 2021-2022 by Oyekanhaa@Github.
# This file is part of KanhaMusic and carries the original GNU GPL v3 notice.
#
# Adapted for this project: search/metadata are separated from the upstream
# authorized media stream provider.

import re
from py_yt import VideosSearch

def time_to_seconds(value):
    value = str(value or "")
    try:
        return sum(int(x) * 60 ** i for i, x in enumerate(reversed(value.split(":"))))
    except ValueError:
        return 0

class YouTubeAPI:
    base = "https://www.youtube.com/watch?v="
    regex = re.compile(r"(?:youtube\.com|youtu\.be)", re.I)

    async def exists(self, link):
        return bool(self.regex.search(link or ""))

    async def search(self, query, limit=8):
        results = VideosSearch(query, limit=limit)
        data = (await results.next()).get("result", [])
        return [{
            "title": r.get("title", "Unknown"),
            "duration": r.get("duration") or "Unknown",
            "duration_sec": time_to_seconds(r.get("duration")),
            "id": r.get("id"),
            "link": r.get("link"),
            "thumb": (r.get("thumbnails") or [{}])[0].get("url", "").split("?")[0],
        } for r in data if r.get("id")]

    async def by_id(self, video_id):
        items = await self.search(self.base + video_id, 1)
        return items[0] if items else None

    async def resolve(self, query):
        query = query.strip()
        m = re.search(
            r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{6,})",
            query,
        )
        if m:
            item = await self.by_id(m.group(1))
            if item:
                return item
        if re.fullmatch(r"[A-Za-z0-9_-]{6,}", query):
            item = await self.by_id(query)
            if item:
                return item
        items = await self.search(query, 1)
        return items[0] if items else None

YouTube = YouTubeAPI()
