"""Small Bot API transport used only where native button styles are required."""

import aiohttp

from .config import CFG


class BotAPIError(RuntimeError):
    pass


class BotAPI:
    def __init__(self, token: str):
        self.base = f"https://api.telegram.org/bot{token}"
        self.session = None

    async def start(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def call(self, method: str, data=None, form=None):
        await self.start()
        url = f"{self.base}/{method}"
        if form is not None:
            payload = form
        else:
            payload = {k: v for k, v in (data or {}).items() if v is not None}
        async with self.session.post(url, data=payload) as response:
            try:
                result = await response.json(content_type=None)
            except Exception as exc:
                body = await response.text()
                raise BotAPIError(f"Bot API returned invalid JSON: {body[:300]}") from exc
        if not result.get("ok"):
            raise BotAPIError(result.get("description", "Telegram Bot API request failed"))
        return result.get("result")

    @staticmethod
    def _json(value):
        import json
        return json.dumps(value, separators=(",", ":"))

    async def send_message(self, chat_id, text, reply_markup=None, reply_to_message_id=None):
        return await self.call("sendMessage", data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": self._json(reply_markup) if reply_markup else None,
            "reply_to_message_id": reply_to_message_id,
        })

    async def send_photo(self, chat_id, photo_path, caption=None, reply_markup=None, reply_to_message_id=None):
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        form.add_field("photo", open(photo_path, "rb"), filename="thumbnail.jpg")
        if caption:
            form.add_field("caption", caption)
            form.add_field("parse_mode", "HTML")
        if reply_markup:
            form.add_field("reply_markup", self._json(reply_markup))
        if reply_to_message_id:
            form.add_field("reply_to_message_id", str(reply_to_message_id))
        try:
            return await self.call("sendPhoto", form=form)
        finally:
            for field in form._fields:
                value = field[2]
                if hasattr(value, "close"):
                    value.close()

    async def send_audio(self, chat_id, audio_path, *, title=None, duration=None,
                         performer=None, caption=None, reply_markup=None,
                         reply_to_message_id=None):
        form = aiohttp.FormData()
        form.add_field("chat_id", str(chat_id))
        form.add_field("audio", open(audio_path, "rb"), filename="audio.mp3")
        if title:
            form.add_field("title", title)
        if duration is not None:
            form.add_field("duration", str(duration))
        if performer:
            form.add_field("performer", performer)
        if caption:
            form.add_field("caption", caption)
            form.add_field("parse_mode", "HTML")
        if reply_markup:
            form.add_field("reply_markup", self._json(reply_markup))
        if reply_to_message_id:
            form.add_field("reply_to_message_id", str(reply_to_message_id))
        try:
            return await self.call("sendAudio", form=form)
        finally:
            for field in form._fields:
                value = field[2]
                if hasattr(value, "close"):
                    value.close()

    async def edit_reply_markup(self, chat_id, message_id, reply_markup):
        return await self.call("editMessageReplyMarkup", data={
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": self._json(reply_markup),
        })


bot_api = BotAPI(CFG.bot_token)
