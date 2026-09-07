import asyncio
from pyrogram.errors import FloodWait

async def broadcast(app, db, source_message, concurrency=8):
    targets = await db.ids("users")
    targets += await db.ids("chats")
    semaphore = asyncio.Semaphore(max(1, concurrency))
    sent = failed = 0

    async def send_one(chat_id):
        nonlocal sent, failed
        async with semaphore:
            try:
                await app.copy_message(
                    chat_id, source_message.chat.id, source_message.id
                )
                sent += 1
            except FloodWait as exc:
                await asyncio.sleep(exc.value)
                try:
                    await app.copy_message(
                        chat_id, source_message.chat.id, source_message.id
                    )
                    sent += 1
                except Exception:
                    failed += 1
            except Exception:
                failed += 1

    await asyncio.gather(*(send_one(x) for x in targets))
    return sent, failed, len(targets)
