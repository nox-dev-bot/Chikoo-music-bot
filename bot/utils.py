import html

def mention(user):
    if not user:
        return "ᴜɴᴋɴᴏᴡɴ"
    return (
        f'<a href="tg://user?id={user.id}">'
        f'{html.escape(user.first_name or "ᴜsᴇʀ")}</a>'
    )
