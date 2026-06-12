import logging
import random
from pyrogram import Client, enums
from pyrogram.types import ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup
from . import database as db
import config

log = logging.getLogger(__name__)

CHANNEL_1_URL = 'https://t.me/+FzvCeGO-2ac0Njdl'
CHANNEL_2_URL = 'https://t.me/+11UUkzagOGhkMjU1'

me_cache: dict = {}


async def get_chat_link(client: Client, chat_id: int, username: str | None) -> str | None:
    if username:
        return f'https://t.me/{username}'
    try:
        return await client.export_chat_invite_link(chat_id)
    except Exception:
        return None


async def notify_owner(client: Client, text: str) -> None:
    try:
        await client.send_message(
            config.OWNER_ID,
            text,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as exc:
        log.warning('join_request: could not notify owner — %s', exc)


@Client.on_chat_join_request()
async def join_request_handler(client: Client, chat_join_request: ChatJoinRequest) -> None:
    user = chat_join_request.from_user
    if not user or user.is_bot:
        return

    chat = chat_join_request.chat
    chat_id = chat.id
    user_id = user.id

    raw_user_chat_id = getattr(chat_join_request, 'user_chat_id', None)
    user_chat_id: int = raw_user_chat_id if raw_user_chat_id else user_id

    enabled = await db.is_approve_enabled(chat_id)
    if not enabled:
        log.debug('join_request: auto-approve disabled for chat %s, skipping user %s', chat_id, user_id)
        return

    if 'me' not in me_cache:
        me_cache['me'] = await client.get_me()
    me = me_cache['me']

    chat_username = chat.username
    chat_title = chat.title or str(chat_id)
    chat_link = await get_chat_link(client, chat_id, chat_username)
    chat_name_html = f'<a href="{chat_link}">{chat_title}</a>' if chat_link else f'<b>{chat_title}</b>'

    first_name = user.first_name or str(user_id)
    mention = f'<a href="tg://user?id={user_id}">{first_name}</a>'

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ᴀ ɢʀᴏᴜᴘ ⇆', url=f'https://t.me/{me.username}?startgroup=true')],
        [
            InlineKeyboardButton('ᴄʜᴀɴɴᴇʟ 1', url=CHANNEL_1_URL),
            InlineKeyboardButton('ᴄʜᴀɴɴᴇʟ 2', url=CHANNEL_2_URL),
        ],
        [InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ᴀ ᴄʜᴀɴɴᴇʟ ⇆', url=f'https://t.me/{me.username}?startchannel=true')],
    ])

    dm_text = (
        f'ʜᴇʏ {mention}! 👋\n\n'
        f'<blockquote>'
        f'✅ ʏᴏᴜʀ ʀᴇqᴜᴇꜱᴛ ᴛᴏ ᴊᴏɪɴ {chat_name_html} ʜᴀꜱ ʙᴇᴇɴ\n'
        f'<b>ᴀᴘᴘʀᴏᴠᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ</b>\n\n'
        f'ʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴀᴄᴄᴇꜱꜱ ᴀʟʟ ᴄᴏɴᴛᴇɴᴛ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ.\n'
        f'ᴛʏᴘᴇ /start ᴛᴏ ᴇxᴘʟᴏʀᴇ ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ!'
        f'</blockquote>'
    )

    dm_sent = False
    try:
        await client.send_photo(
            user_chat_id,
            random.choice(config.START_PHOTOS),
            caption=dm_text,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
        )
        dm_sent = True
    except Exception as exc:
        log.warning(
            'join_request: send_photo failed for user %s (chat_id=%s, user_chat_id=%s) — %s',
            user_id, chat_id, user_chat_id, exc,
        )
        try:
            await client.send_message(
                user_chat_id,
                dm_text,
                reply_markup=keyboard,
                parse_mode=enums.ParseMode.HTML,
            )
            dm_sent = True
        except Exception as exc2:
            log.error(
                'join_request: could not DM user %s in chat %s (user_chat_id=%s) — %s',
                user_id, chat_id, user_chat_id, exc2,
            )

    try:
        await client.approve_chat_join_request(chat_id, user_id)
        await db.add_served_chat(chat_id)
        log.info(
            'join_request: approved user %s in chat %s (dm_sent=%s)',
            user_id, chat_id, dm_sent,
        )
    except Exception as exc:
        log.error(
            'join_request: FAILED to approve user %s in chat %s — %s',
            user_id, chat_id, exc,
        )
        await notify_owner(
            client,
            f'<b>⚠️ ᴀᴘᴘʀᴏᴠᴇ ꜰᴀɪʟᴇᴅ</b>\n\n'
            f'<blockquote>'
            f'ᴄʜᴀᴛ  : <code>{chat_id}</code> ({chat_title})\n'
            f'ᴜꜱᴇʀ  : <code>{user_id}</code>\n'
            f'ᴇʀʀᴏʀ : <code>{exc}</code>'
            f'</blockquote>\n\n'
            f'<b>ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀᴅᴍɪɴ ᴡɪᴛʜ "ɪɴᴠɪᴛᴇ ᴜꜱᴇʀꜱ" ᴘᴇʀᴍɪꜱꜱɪᴏɴ.</b>',
        )
