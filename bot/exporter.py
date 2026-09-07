import csv
import io
import json
import zipfile
from datetime import datetime, timezone


async def build_stats_export(db):
    users = []
    cursor = db.users.find(
        {},
        {"_id": 0, "user_id": 1, "username": 1, "first_name": 1, "joined_at": 1},
    ).sort("user_id", 1)
    async for doc in cursor:
        users.append({
            "user_id": doc.get("user_id"),
            "username": doc.get("username", ""),
            "first_name": doc.get("first_name", ""),
            "joined_at": doc.get("joined_at").isoformat() if doc.get("joined_at") else "",
        })

    chats = []
    cursor = db.chats.find(
        {},
        {"_id": 0, "chat_id": 1, "title": 1, "kind": 1, "added_at": 1},
    ).sort("chat_id", 1)
    async for doc in cursor:
        chats.append({
            "chat_id": doc.get("chat_id"),
            "title": doc.get("title", ""),
            "kind": doc.get("kind", ""),
            "added_at": doc.get("added_at").isoformat() if doc.get("added_at") else "",
        })

    settings = {}
    cursor = db.settings.find({}, {"_id": 0, "key": 1, "value": 1}).sort("key", 1)
    async for doc in cursor:
        settings[doc.get("key", "")] = doc.get("value", "")

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "users": len(users),
        "chats": len(chats),
        "database": "MongoDB",
        "warning": "Contains Telegram identifiers and profile/chat metadata. Keep private.",
    }

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("summary.json", json.dumps(summary, indent=2, ensure_ascii=False))
        archive.writestr("settings.json", json.dumps(settings, indent=2, ensure_ascii=False))

        user_csv = io.StringIO()
        writer = csv.DictWriter(
            user_csv,
            fieldnames=["user_id", "username", "first_name", "joined_at"],
        )
        writer.writeheader()
        writer.writerows(users)
        archive.writestr("users.csv", user_csv.getvalue())

        chat_csv = io.StringIO()
        writer = csv.DictWriter(
            chat_csv,
            fieldnames=["chat_id", "title", "kind", "added_at"],
        )
        writer.writeheader()
        writer.writerows(chats)
        archive.writestr("chats.csv", chat_csv.getvalue())

    buffer.seek(0)
    return buffer
