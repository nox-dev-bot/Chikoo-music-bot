from datetime import datetime, timezone
import os

from pymongo import ASCENDING
from pymongo import AsyncMongoClient

DEFAULTS = {
    "welcome": "🎧 <b>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴄʜɪᴋᴏᴏ ᴍᴜsɪᴄ</b>\n\nsᴇɴᴅ <code>/play</code> ᴡɪᴛʜ ᴀ sᴏɴɢ ɴᴀᴍᴇ ᴏʀ ʏᴏᴜᴛᴜʙᴇ ᴜʀʟ.",
    "playmsg": "🎧 <b>ɴᴏᴡ ᴘʟᴀʏɪɴɢ</b>\n🎵 <b>{title}</b>\n⏱️ {duration}",
}


class Database:
    """Async MongoDB-backed persistence for users, chats, and settings."""

    def __init__(self):
        self.client = None
        self.db = None
        self.users = None
        self.chats = None
        self.settings = None

    async def start(self):
        uri = os.getenv("MONGODB_URI", "").strip()
        if not uri:
            raise RuntimeError("Set MONGODB_URI in .env")

        db_name = os.getenv("MONGODB_DATABASE", "chikoo_music").strip() or "chikoo_music"
        self.client = AsyncMongoClient(uri, serverSelectionTimeoutMS=10000)
        await self.client.admin.command("ping")

        self.db = self.client[db_name]
        self.users = self.db["users"]
        self.chats = self.db["chats"]
        self.settings = self.db["settings"]

        await self.users.create_index([("user_id", ASCENDING)], unique=True)
        await self.chats.create_index([("chat_id", ASCENDING)], unique=True)
        await self.settings.create_index([("key", ASCENDING)], unique=True)

        for key, value in DEFAULTS.items():
            await self.settings.update_one(
                {"key": key},
                {"$setOnInsert": {"key": key, "value": value}},
                upsert=True,
            )

    async def add_user(self, user):
        if not user:
            return
        await self.users.update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "username": user.username or "",
                    "first_name": user.first_name or "",
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "user_id": user.id,
                    "joined_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )

    async def add_chat(self, chat):
        if not chat:
            return
        kind = str(getattr(chat, "type", "unknown"))
        title = getattr(chat, "title", None) or getattr(chat, "first_name", "") or ""
        await self.chats.update_one(
            {"chat_id": chat.id},
            {
                "$set": {
                    "title": title,
                    "kind": kind,
                    "updated_at": datetime.now(timezone.utc),
                },
                "$setOnInsert": {
                    "chat_id": chat.id,
                    "added_at": datetime.now(timezone.utc),
                },
            },
            upsert=True,
        )

    async def ids(self, table):
        collection = self.users if table == "users" else self.chats
        field = "user_id" if table == "users" else "chat_id"
        cursor = collection.find({}, {field: 1, "_id": 0})
        return [doc[field] async for doc in cursor]

    async def chat_ids_by_kind(self, kind):
        cursor = self.chats.find({"kind": kind}, {"chat_id": 1, "_id": 0})
        return [doc["chat_id"] async for doc in cursor]

    async def count(self, table):
        collection = self.users if table == "users" else self.chats
        return await collection.count_documents({})

    async def get_setting(self, key):
        doc = await self.settings.find_one({"key": key}, {"value": 1, "_id": 0})
        return doc["value"] if doc else DEFAULTS.get(key, "")

    async def set_setting(self, key, value):
        await self.settings.update_one(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True,
        )

    async def close(self):
        if self.client is not None:
            await self.client.close()
            self.client = None
            self.db = None
            self.users = None
            self.chats = None
            self.settings = None
