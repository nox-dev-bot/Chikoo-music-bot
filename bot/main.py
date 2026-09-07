import asyncio
import html
import os
import tempfile

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified

from .webserver import health_server

from .config import CFG
from .database import Database
from .youtube import YouTube
from .music import fetch_audio, fetch_thumbnail
from .keyboards import home, results, player
from .bot_api import bot_api
from .utils import mention
from .streamer import streamer
from .player import ChatPlayer
from .broadcast import broadcast
from .exporter import build_stats_export

app = Client(
    "chikoo_music_bot",
    api_id=CFG.api_id,
    api_hash=CFG.api_hash,
    bot_token=CFG.bot_token,
)

db = Database()
music = ChatPlayer(streamer)

def is_owner(_, __, message):
    return bool(message.from_user and message.from_user.id == CFG.owner_id)

owner_only = filters.create(is_owner)

async def log(text):
    if CFG.log_group_id:
        try:
            await app.send_message(CFG.log_group_id, text)
        except Exception:
            pass

@app.on_message(filters.incoming, group=-10)
async def register(_, message):
    if message.from_user:
        await db.add_user(message.from_user)
    if message.chat:
        await db.add_chat(message.chat)

async def resolve(query):
    item = await YouTube.resolve(query)
    if not item:
        raise RuntimeError("ɴᴏ ʀᴇsᴜʟᴛ ғᴏᴜɴᴅ")
    return item

async def reply_styled(message, text, markup):
    return await bot_api.send_message(
        message.chat.id,
        text,
        reply_markup=markup,
        reply_to_message_id=message.id,
    )

async def send_player_card(message, item, action="ᴇɴǫᴜᴇᴅ"):
    thumb = await fetch_thumbnail(item.get("thumb"))
    caption = (
        f"🎶 <b>sᴛʀᴇᴀᴍ ɪɴɪᴛɪᴀᴛᴇᴅ</b>\n\n"
        f"🎵 <b>ᴛɪᴛʟᴇ:</b> {html.escape(item['title'])}\n"
        f"⏱️ <b>ᴅᴜʀᴀᴛɪᴏɴ:</b> {html.escape(item['duration'])}\n"
        f"👤 <b>ᴘʟᴀʏᴇᴅ ʙʏ:</b> {mention(message.from_user)}\n"
        f"📌 <b>sᴛᴀᴛᴜs:</b> {action}"
    )
    try:
        if thumb:
            return await bot_api.send_photo(
                message.chat.id,
                thumb,
                caption=caption,
                reply_markup=player(item["id"]),
                reply_to_message_id=message.id,
            )
        return await reply_styled(message, caption, player(item["id"]))
    finally:
        if thumb:
            try:
                os.remove(thumb)
            except OSError:
                pass

async def send_audio(message, query, add_voice=True):
    status = await message.reply_text("🔎 <b>sᴇᴀʀᴄʜɪɴɢ…</b>")
    path = thumb = None
    try:
        item = await resolve(query)
        await status.edit_text("⏳ <b>ᴘʀᴇᴘᴀʀɪɴɢ ᴛᴏᴘ ǫᴜᴀʟɪᴛʏ…</b>")

        # Queue/voice playback is optional; /play always sends the audio file.
        if add_voice and message.chat.type in (
            ChatType.GROUP, ChatType.SUPERGROUP, ChatType.CHANNEL
        ) and CFG.assistant_session:
            await music.add(message.chat.id, item)

        await send_player_card(message, item, "sᴇɴᴛ + ᴇɴǫᴜᴇᴜᴅ")

        path = await fetch_audio(item["id"])
        await bot_api.send_audio(
            message.chat.id,
            path,
            title=item["title"][:64],
            duration=item["duration_sec"],
            performer="ʏᴏᴜᴛᴜʙᴇ",
            caption=(
                f"🎧 <b>{html.escape(item['title'])}</b>\n"
                f"⏱️ <code>{html.escape(item['duration'])}</code>"
            ),
            reply_markup=player(item["id"]),
            reply_to_message_id=message.id,
        )
        await status.delete()
        await log(
            f"🎵 <b>ᴘʟᴀʏ</b>\n"
            f"👤 {mention(message.from_user)}\n"
            f"🎧 {html.escape(item['title'])}\n"
            f"ᴄʜᴀᴛ: <code>{message.chat.id}</code>"
        )
    except Exception as exc:
        await status.edit_text(
            f"❌ <b>ᴇʀʀᴏʀ:</b> <code>{html.escape(str(exc)[:700])}</code>"
        )
        await log(
            f"⚠️ <b>ᴘʟᴀʏ ᴇʀʀᴏʀ</b>\n"
            f"<code>{html.escape(str(exc)[:900])}</code>"
        )
    finally:
        for path_to_delete in (path, thumb):
            if path_to_delete:
                try:
                    os.remove(path_to_delete)
                except OSError:
                    pass

@app.on_message(filters.command("start"))
async def start(_, message):
    await reply_styled(
        message,
        (await db.get_setting("welcome")) +
        "\n\n🔎 <code>/search song</code>"
        "\n🎵 <code>/play song</code>"
        "\n📡 <code>/stream song</code>",
        home(),
    )

@app.on_message(filters.command("help"))
async def help_cmd(_, message):
    await reply_styled(
        message,
        "🎧 <b>ᴄʜɪᴋᴏᴏ ᴍᴜsɪᴄ</b>\n\n"
        "🔎 /search · 🎵 /play · 📡 /stream\n"
        "⏸ /pause · ▶ /resume · ⏭ /next · ⏮ /prev\n"
        "⏪ /seek · ⏹ /stop · 📜 /queue · 🔊 /volume\n"
        "🔁 /replay · 🔀 /shuffle · 🔂 /loop\n\n"
        "👑 <b>ᴏᴡɴᴇʀ</b>\n"
        "/broadcast · /notify · /notifygroup · /notifychannel\n"
        "/stats · /exportstats · /settings",
        home(),
    )

@app.on_message(filters.command(["play", "song"]))
async def play_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "🎵 <code>/play song name or youtube url</code>"
        )
    await send_audio(message, " ".join(message.command[1:]))

@app.on_message(filters.command("search"))
async def search_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text("🔎 <code>/search song name</code>")
    try:
        items = await YouTube.search(" ".join(message.command[1:]), 8)
        if not items:
            return await message.reply_text("❌ ɴᴏ ʀᴇsᴜʟᴛs")
        text = ["🔎 <b>sᴇᴀʀᴄʜ ʀᴇsᴜʟᴛs</b>\n"]
        for i, item in enumerate(items, 1):
            text.append(
                f"<b>{i}.</b> {html.escape(item['title'])} "
                f"— <code>{html.escape(item['duration'])}</code>"
            )
        await reply_styled(message, "\n".join(text), results(items))
    except Exception as exc:
        await message.reply_text(
            f"❌ <code>{html.escape(str(exc)[:600])}</code>"
        )

@app.on_message(filters.command("stream"))
async def stream_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "📡 <code>/stream song name or YouTube URL</code>"
        )
    try:
        item = await resolve(" ".join(message.command[1:]))
        item["media_type"] = "audio"
        await music.add(message.chat.id, item)
        await send_player_card(message, item, "ᴀᴜᴅɪᴏ sᴛʀᴇᴀᴍɪɴɢ")
    except Exception as exc:
        await message.reply_text(
            f"❌ <code>{html.escape(str(exc)[:700])}</code>"
        )

@app.on_message(filters.command(["vstream", "vplay"]))
async def video_stream_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text(
            "🎬 <code>/vstream video name or YouTube URL</code>"
        )
    try:
        item = await resolve(" ".join(message.command[1:]))
        item["media_type"] = "video"
        await music.add(message.chat.id, item)
        await send_player_card(message, item, "ᴠɪᴅᴇᴏ sᴛʀᴇᴀᴍɪɴɢ")
    except Exception as exc:
        await message.reply_text(
            f"❌ <code>{html.escape(str(exc)[:700])}</code>"
        )

@app.on_message(filters.command(["pause"]))
async def pause_cmd(_, message):
    try:
        await music.pause(message.chat.id)
        await reply_styled(message, "⏸️ <b>ᴘᴀᴜsᴇᴅ</b>", player())
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:500])}</code>")

@app.on_message(filters.command(["resume", "playnow"]))
async def resume_cmd(_, message):
    try:
        await music.resume(message.chat.id)
        await reply_styled(message, "▶️ <b>ʀᴇsᴜᴍᴇᴅ</b>", player())
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:500])}</code>")

@app.on_message(filters.command(["next", "skip"]))
async def next_cmd(_, message):
    try:
        item = await music.next(message.chat.id)
        if not item:
            return await message.reply_text("📭 <b>ǫᴜᴇᴜᴇ ᴇᴍᴘᴛʏ</b>")
        await send_player_card(message, {
            "id": item.video_id, "title": item.title, "duration": item.duration,
            "duration_sec": item.duration_sec, "thumb": item.thumb, "link": item.link,
            "media_type": item.media_type
        }, "ɴᴏᴡ ᴘʟᴀʏɪɴɢ")
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:600])}</code>")

@app.on_message(filters.command(["prev", "previous"]))
async def prev_cmd(_, message):
    try:
        item = await music.previous(message.chat.id)
        await reply_styled(
            message,
            f"⏮️ <b>ᴘʀᴇᴠɪᴏᴜs</b>\n🎵 {html.escape(item.title)}",
            player(item.video_id),
        )
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:600])}</code>")

@app.on_message(filters.command(["stop", "end", "vstop", "stopstream"]))
async def stop_cmd(_, message):
    try:
        await music.stop(message.chat.id)
        await message.reply_text("⏹️ <b>sᴛᴏᴘᴘᴇᴅ + ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>")
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:500])}</code>")

@app.on_message(filters.command("seek"))
async def seek_cmd(_, message):
    if len(message.command) < 2:
        return await message.reply_text("⏩ <code>/seek 1:30</code> ᴏʀ <code>/seek 90</code>")
    value = message.command[1]
    try:
        if ":" in value:
            a, b = value.split(":", 1)
            target = int(a) * 60 + int(b)
            delta = target - music.position(message.chat.id)
        else:
            delta = int(value)
        pos = await music.seek(message.chat.id, delta)
        await reply_styled(
            message,
            f"⏩ <b>sᴇᴇᴋᴇᴅ</b> · <code>{pos}s</code>",
            player(),
        )
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:700])}</code>")

@app.on_message(filters.command("forward"))
async def forward_cmd(_, message):
    value = int(message.command[1]) if len(message.command) > 1 else 10
    try:
        pos = await music.seek(message.chat.id, abs(value))
        await reply_styled(message, f"⏩ <code>{pos}s</code>", player())
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:500])}</code>")

@app.on_message(filters.command("back"))
async def back_cmd(_, message):
    value = int(message.command[1]) if len(message.command) > 1 else 10
    try:
        pos = await music.seek(message.chat.id, -abs(value))
        await reply_styled(message, f"⏪ <code>{pos}s</code>", player())
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:500])}</code>")

@app.on_message(filters.command("replay"))
async def replay_cmd(_, message):
    try:
        await music.replay(message.chat.id)
        await reply_styled(message, "🔁 <b>ʀᴇᴘʟᴀʏɪɴɢ</b>", player())
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:500])}</code>")

@app.on_message(filters.command("queue"))
async def queue_cmd(_, message):
    await reply_styled(message, music.queue_text(message.chat.id), player())

@app.on_message(filters.command("now"))
async def now_cmd(_, message):
    cur = music.current.get(message.chat.id)
    if not cur:
        return await message.reply_text("📭 ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ")
    await reply_styled(
        message,
        f"🎵 <b>ɴᴏᴡ ᴘʟᴀʏɪɴɢ</b>\n"
        f"🎧 {html.escape(cur.title)}\n"
        f"⏱️ <code>{music.position(message.chat.id)}s / {cur.duration_sec}s</code>",
        player(cur.video_id),
    )

@app.on_message(filters.command("volume"))
async def volume_cmd(_, message):
    try:
        value = int(message.command[1])
        await music.streamer.volume(message.chat.id, value)
        music.volumes[message.chat.id] = max(0, min(200, value))
        await message.reply_text(f"🔊 <b>ᴠᴏʟᴜᴍᴇ:</b> <code>{value}</code>")
    except Exception as exc:
        await message.reply_text(f"❌ <code>{html.escape(str(exc)[:500])}</code>")

@app.on_message(filters.command("shuffle"))
async def shuffle_cmd(_, message):
    await music.shuffle(message.chat.id)
    await message.reply_text("🔀 <b>ǫᴜᴇᴜᴇ sʜᴜғғʟᴇᴅ</b>")

@app.on_message(filters.command("clear"))
async def clear_cmd(_, message):
    await music.clear(message.chat.id)
    await message.reply_text("🗑️ <b>ǫᴜᴇᴜᴇ ᴄʟᴇᴀʀᴇᴅ</b>")

@app.on_message(filters.command("loop"))
async def loop_cmd(_, message):
    mode = message.command[1].lower() if len(message.command) > 1 else "off"
    if mode not in {"off", "one", "all"}:
        return await message.reply_text("ᴜsᴇ <code>/loop off</code>, <code>/loop one</code> ᴏʀ <code>/loop all</code>")
    music.loops[message.chat.id] = mode
    await message.reply_text(f"🔁 <b>ʟᴏᴏᴘ:</b> <code>{mode}</code>")

# Inline control callbacks.
@app.on_callback_query(filters.regex(r"^play:"))
async def cb_play(_, query: CallbackQuery):
    await query.answer("⏳ ᴘʀᴇᴘᴀʀɪɴɢ…")
    try:
        item = await resolve(query.data.split(":", 1)[1])
        await music.add(query.message.chat.id, item, force=True)
        await bot_api.edit_reply_markup(query.message.chat.id, query.message.id, player(item["id"]))
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^pause$"))
async def cb_pause(_, query):
    try:
        await music.pause(query.message.chat.id)
        await query.answer("⏸️ ᴘᴀᴜsᴇᴅ")
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^resume$"))
async def cb_resume(_, query):
    try:
        await music.resume(query.message.chat.id)
        await query.answer("▶️ ʀᴇsᴜᴍᴇᴅ")
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^next$"))
async def cb_next(_, query):
    try:
        item = await music.next(query.message.chat.id)
        await query.answer("⏭️ ɴᴇxᴛ")
        if item:
            await bot_api.edit_reply_markup(query.message.chat.id, query.message.id, player(item.video_id))
        else:
            await bot_api.edit_reply_markup(query.message.chat.id, query.message.id, player())
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^prev$"))
async def cb_prev(_, query):
    try:
        item = await music.previous(query.message.chat.id)
        await query.answer("⏮️ ᴘʀᴇᴠɪᴏᴜs")
        await bot_api.edit_reply_markup(query.message.chat.id, query.message.id, player(item.video_id))
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex(r"^seek:"))
async def cb_seek(_, query):
    try:
        delta = int(query.data.split(":", 1)[1])
        pos = await music.seek(query.message.chat.id, delta)
        await query.answer(f"⏩ {pos}s")
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex(r"^vol:"))
async def cb_vol(_, query):
    try:
        delta = int(query.data.split(":", 1)[1])
        value = await music.volume(query.message.chat.id, delta)
        await query.answer(f"🔊 {value}%")
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^replay$"))
async def cb_replay(_, query):
    try:
        await music.replay(query.message.chat.id)
        await query.answer("🔁 ʀᴇᴘʟᴀʏ")
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^stop$|^end$"))
async def cb_stop(_, query):
    try:
        await music.stop(query.message.chat.id)
        await query.answer("⏹️ sᴛᴏᴘᴘᴇᴅ")
        await bot_api.edit_reply_markup(query.message.chat.id, query.message.id, player())
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^queue$"))
async def cb_queue(_, query):
    await query.answer()
    await bot_api.send_message(
        query.message.chat.id,
        music.queue_text(query.message.chat.id),
        reply_markup=player(),
        reply_to_message_id=query.message.id,
    )

@app.on_callback_query(filters.regex("^now$"))
async def cb_now(_, query):
    cur = music.current.get(query.message.chat.id)
    if not cur:
        return await query.answer("📭 ɴᴏᴛʜɪɴɢ ɪs ᴘʟᴀʏɪɴɢ", show_alert=True)
    await query.answer(
        f"{cur.title[:80]} · {music.position(query.message.chat.id)}s",
        show_alert=True,
    )

@app.on_callback_query(filters.regex("^stream:"))
async def cb_stream(_, query):
    try:
        vid = query.data.split(":", 1)[1]
        if not vid:
            return await query.answer("ᴘʟᴀʏ ᴀ sᴏɴɢ ғɪʀsᴛ", show_alert=True)
        item = await resolve(vid)
        item["media_type"] = "audio"
        await music.add(query.message.chat.id, item)
        await query.answer("📡 ᴀᴜᴅɪᴏ sᴛʀᴇᴀᴍɪɴɢ")
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^vstream:"))
async def cb_vstream(_, query):
    try:
        vid = query.data.split(":", 1)[1]
        if not vid:
            return await query.answer("ᴘʟᴀʏ ᴀ ᴠɪᴅᴇᴏ ғɪʀsᴛ", show_alert=True)
        item = await resolve(vid)
        item["media_type"] = "video"
        await music.add(query.message.chat.id, item)
        await query.answer("🎬 ᴠɪᴅᴇᴏ sᴛʀᴇᴀᴍɪɴɢ")
    except Exception as exc:
        await query.answer(str(exc)[:180], show_alert=True)

@app.on_callback_query(filters.regex("^close$"))
async def cb_close(_, query):
    await query.answer()
    try:
        await query.message.delete()
    except Exception:
        pass

@app.on_callback_query(filters.regex("^noop$"))
async def cb_noop(_, query):
    await query.answer("ᴜsᴇ /stream <sᴏɴɢ> ᴛᴏ sᴛᴀʀᴛ ᴀ ᴠᴄ sᴛʀᴇᴀᴍ", show_alert=True)

@app.on_message(filters.command("stats") & owner_only)
async def stats(_, message):
    users = await db.count("users")
    chats = await db.count("chats")
    groups = await db.chat_ids_by_kind(str(ChatType.GROUP))
    supergroups = await db.chat_ids_by_kind(str(ChatType.SUPERGROUP))
    channels = await db.chat_ids_by_kind(str(ChatType.CHANNEL))
    await message.reply_text(
        "📊 <b>ʙᴏᴛ sᴛᴀᴛs</b>\n\n"
        f"👤 ᴜsᴇʀs: <code>{users}</code>\n"
        f"👥 ɢʀᴏᴜᴘs: <code>{len(groups) + len(supergroups)}</code>\n"
        f"📣 ᴄʜᴀɴɴᴇʟs: <code>{len(channels)}</code>\n"
        f"🗃️ ᴛᴏᴛᴀʟ ᴄʜᴀᴛs: <code>{chats}</code>"
    )

@app.on_message(filters.command("exportstats") & owner_only)
async def exportstats(_, message):
    status = await message.reply_text("📦 <b>ᴘʀᴇᴘᴀʀɪɴɢ sᴛᴀᴛs ᴇxᴘᴏʀᴛ…</b>")
    try:
        data = await build_stats_export(db)
        await message.reply_document(
            data,
            file_name="chikoo_stats_export.zip",
            caption=(
                "📊 <b>ᴄʜɪᴋᴏᴏ sᴛᴀᴛs ᴇxᴘᴏʀᴛ</b>\n"
                "⚠️ ᴛʜɪs ᴄᴏɴᴛᴀɪɴs ᴛᴇʟᴇɢʀᴀᴍ ɪᴅs, ᴜsᴇʀɴᴀᴍᴇs ᴀɴᴅ ᴄʜᴀᴛ ᴍᴇᴛᴀᴅᴀᴛᴀ. ᴋᴇᴇᴘ ɪᴛ ᴘʀɪᴠᴀᴛᴇ."
            ),
        )
        await status.delete()
    except Exception as exc:
        await status.edit_text(
            f"❌ <code>{html.escape(str(exc)[:700])}</code>"
        )

@app.on_message(filters.command("settings") & owner_only)
async def settings(_, message):
    welcome = await db.get_setting("welcome")
    playmsg = await db.get_setting("playmsg")
    await message.reply_text(
        "⚙️ <b>sᴇᴛᴛɪɴɢs</b>\n\n"
        f"<b>ᴡᴇʟᴄᴏᴍᴇ:</b> <code>{html.escape(welcome[:400])}</code>\n"
        f"<b>ᴘʟᴀʏᴍsɢ:</b> <code>{html.escape(playmsg[:400])}</code>\n"
        f"<b>ᴀᴜᴅɪᴏ:</b> <code>{CFG.audio_quality}</code>"
    )

@app.on_message(filters.command("setwelcome") & owner_only)
async def setwelcome(_, message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text("ᴜsᴀɢᴇ: <code>/setwelcome your text</code>")
    await db.set_setting("welcome", parts[1])
    await message.reply_text("✅ ᴡᴇʟᴄᴏᴍᴇ ᴜᴘᴅᴀᴛᴇᴅ — ɴᴏ ʀᴇᴅᴇᴘʟᴏʏ.")

@app.on_message(filters.command("setplaymsg") & owner_only)
async def setplaymsg(_, message):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text(
            "ᴜsᴀɢᴇ: <code>/setplaymsg text with {title} and {duration}</code>"
        )
    await db.set_setting("playmsg", parts[1])
    await message.reply_text("✅ ᴘʟᴀʏ ᴍsɢ ᴜᴘᴅᴀᴛᴇᴅ — ɴᴏ ʀᴇᴅᴇᴘʟᴏʏ.")

@app.on_message(filters.command("broadcast") & owner_only)
async def broadcast_cmd(_, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "📢 ʀᴇᴘʟʏ ᴛᴏ ᴛʜᴇ ᴍᴇᴅɪᴀ/ᴍsɢ ᴛʜᴇɴ sᴇɴᴅ /broadcast."
        )
    status = await message.reply_text("📤 <b>ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ…</b>")
    sent, failed, total = await broadcast(
        app, db, message.reply_to_message, CFG.broadcast_concurrency
    )
    await status.edit_text(
        f"✅ <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴅᴏɴᴇ</b>\n"
        f"📨 sᴇɴᴛ: <code>{sent}</code>\n"
        f"❌ ғᴀɪʟᴇᴅ: <code>{failed}</code>\n"
        f"📊 ᴛᴏᴛᴀʟ: <code>{total}</code>"
    )

async def text_broadcast(message, targets):
    parts = message.text.split(None, 1)
    if len(parts) < 2:
        return await message.reply_text("ᴜsᴀɢᴇ: <code>/notify your message</code>")
    sent = failed = 0
    for chat_id in targets:
        try:
            await app.send_message(chat_id, parts[1])
            sent += 1
        except Exception:
            failed += 1
    await message.reply_text(
        f"🔔 ᴅᴏɴᴇ · sᴇɴᴛ <code>{sent}</code> · ғᴀɪʟᴇᴅ <code>{failed}</code>"
    )

@app.on_message(filters.command("notify") & owner_only)
async def notify(_, message):
    await text_broadcast(message, await db.ids("users") + await db.ids("chats"))

@app.on_message(filters.command("notifygroup") & owner_only)
async def notifygroup(_, message):
    await text_broadcast(
        message,
        await db.chat_ids_by_kind(str(ChatType.GROUP))
        + await db.chat_ids_by_kind(str(ChatType.SUPERGROUP))
    )

@app.on_message(filters.command("notifychannel") & owner_only)
async def notifychannel(_, message):
    await text_broadcast(
        message,
        await db.chat_ids_by_kind(str(ChatType.CHANNEL))
    )

async def main():
    await health_server.start()
    try:
        await db.start()
        streamer.set_on_end(music.on_stream_end)
        await app.start()
        health_server.bot_ready = True
        await streamer.start()
        health_server.assistant_ready = streamer.ready
        me = await app.get_me()
        print(f"ᴄʜɪᴋᴏᴏ ᴍᴜsɪᴄ ʀᴜɴɴɪɴɢ ᴀs @{me.username}")
        await log(f"🟢 <b>ʙᴏᴛ sᴛᴀʀᴛᴇᴅ</b> · @{me.username}")
        await asyncio.Event().wait()
    finally:
        health_server.bot_ready = False
        health_server.assistant_ready = False
        try:
            await streamer.stop()
        except Exception:
            pass
        try:
            await app.stop()
        except Exception:
            pass
        try:
            await db.close()
        except Exception:
            pass
        await health_server.stop()

if __name__ == "__main__":
    asyncio.run(main())
