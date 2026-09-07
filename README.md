# ᴄʜɪᴋᴏᴏ ᴍᴜsɪᴄ ʙᴏᴛ — streaming build

Telegram music/video-chat bot using the supplied YouTube resolver and the configured Yuki stream API.

## Voice/video streaming
- `/stream <song name|YouTube URL>` — stream audio in the active Telegram voice/video chat.
- `/vstream <video name|YouTube URL>` — stream video + audio in the active Telegram video chat.
- `/vplay <video name|YouTube URL>` — alias for `/vstream`.
- Search names are resolved through the bundled YouTube search helper; YouTube links are resolved directly.
- `/play <song name|YouTube URL>` still sends an audio file to the chat.

The assistant user account must already be able to join/speak in the relevant active voice/video chat. PyTgCalls accepts remote media streams; this build passes the Yuki stream URL directly rather than downloading the entire track first.

### Video quality note
`VIDEO_QUALITY=1080` controls the requested upstream Yuki video source. The Telegram/PyTgCalls call output is negotiated through the installed PyTgCalls `VideoQuality`; depending on the library/client version, the actual call output can be lower (for example 720p).

## Controls
The player uses Telegram's native `primary`, `success`, and `danger` button styles. It includes audio/video stream buttons plus pause/resume/seek/next/previous/replay/volume/queue/stop/end controls.

## Setup
1. Put your credentials in `.env`.
2. Install requirements.
3. Start the bot with `python -m bot`.
4. Start a Telegram voice/video chat in the target group/channel.
5. Use `/stream` for audio or `/vstream` for video.

Do not commit `.env`, bot tokens, API hashes, Yuki keys, or assistant StringSessions to a public repository.

## Render Web Service
This project includes a small HTTP health server so it can run as a Render Web Service.

- Binds to `0.0.0.0`.
- Uses Render's `PORT` environment variable, defaulting to `10000` locally.
- `GET /` returns service status.
- `GET /health` and `GET /healthz` are health endpoints.
- `render.yaml` contains the Web Service build/start/health-check configuration.

For Render, set the required secrets as Environment Variables in the dashboard. Do not commit `.env` to GitHub. The included `.gitignore` excludes it.

## MongoDB persistence
This build uses MongoDB instead of SQLite for persistent users, chats, and settings.

- `MONGODB_URI` — MongoDB/Atlas connection string.
- `MONGODB_DATABASE` — database name; defaults to `chikoo_music`.
- The bot pings MongoDB during startup and fails fast if the connection cannot be established.
- `/stats` and `/exportstats` read from MongoDB.

The application uses PyMongo's asynchronous `AsyncMongoClient`, so database operations are awaited instead of blocking the bot's event loop.
