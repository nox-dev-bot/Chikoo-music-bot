# Telegram Bot API styled inline keyboards.
# The `style` field is a Bot API feature; Pyrogram's InlineKeyboardButton
# abstraction does not expose it, so these functions return Bot API JSON.

def _button(text, *, callback_data=None, url=None, switch_inline_query_current_chat=None, style=None):
    button = {"text": text}
    if callback_data is not None:
        button["callback_data"] = callback_data
    if url is not None:
        button["url"] = url
    if switch_inline_query_current_chat is not None:
        button["switch_inline_query_current_chat"] = switch_inline_query_current_chat
    if style is not None:
        button["style"] = style
    return button


def _markup(rows):
    return {"inline_keyboard": rows}


def home():
    return _markup([
        [
            _button("🎧 ᴘʟᴀʏ", switch_inline_query_current_chat="", style="success"),
            _button("🔎 sᴇᴀʀᴄʜ", switch_inline_query_current_chat="", style="primary"),
        ],
        [
            _button("📡 sᴛʀᴇᴀᴍ", callback_data="noop", style="primary"),
            _button("❓ ʜᴇʟᴘ", callback_data="help", style="primary"),
        ],
        [_button("👑 ᴏᴡɴᴇʀ", url="https://t.me/nox_shadowx", style="primary")],
    ])


def results(items):
    rows = []
    for item in items[:8]:
        rows.append([
            _button(
                f"▶️ {item['title'][:34]}",
                callback_data=f"play:{item['id']}",
                style="success",
            )
        ])
    rows.append([_button("❌ ᴄʟᴏsᴇ", callback_data="close", style="danger")])
    return _markup(rows)


def player(video_id=None):
    suffix = video_id or ""
    return _markup([
        [
            _button("⏮ ᴘʀᴇᴠ", callback_data="prev", style="primary"),
            _button("⏪ -10s", callback_data="seek:-10", style="primary"),
            _button("⏩ +10s", callback_data="seek:10", style="primary"),
            _button("⏭ ɴᴇxᴛ", callback_data="next", style="primary"),
        ],
        [
            _button("▶️ ᴘʟᴀʏ", callback_data="resume", style="success"),
            _button("⏸ ᴘᴀᴜsᴇ", callback_data="pause", style="primary"),
            _button("🔁 ʀᴇᴘʟᴀʏ", callback_data="replay", style="primary"),
            _button("⏹️ sᴛᴏᴘ", callback_data="stop", style="danger"),
        ],
        [
            _button("🔉 -ᴠᴏʟ", callback_data="vol:-10", style="primary"),
            _button("🔊 +ᴠᴏʟ", callback_data="vol:10", style="primary"),
            _button("📜 ǫᴜᴇᴜᴇ", callback_data="queue", style="primary"),
            _button("🎵 ɴᴏᴡ", callback_data="now", style="primary"),
        ],
        [
            _button("📡 ᴀᴜᴅɪᴏ", callback_data=f"stream:{suffix}", style="primary"),
            _button("🎬 ᴠɪᴅᴇᴏ", callback_data=f"vstream:{suffix}", style="success"),
        ],
        [
            _button("🔴 ᴇɴᴅ", callback_data="end", style="danger"),
            _button("❌ ᴄʟᴏsᴇ", callback_data="close", style="danger"),
        ],
    ])


def seek_menu():
    return _markup([
        [
            _button("⏪ -30s", callback_data="seek:-30", style="primary"),
            _button("⏪ -10s", callback_data="seek:-10", style="primary"),
            _button("⏩ +10s", callback_data="seek:10", style="primary"),
            _button("⏩ +30s", callback_data="seek:30", style="primary"),
        ],
        [_button("🔙 ʙᴀᴄᴋ", callback_data="backplayer", style="primary")],
    ])
