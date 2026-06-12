import asyncio
import time
import logging
from pyrogram import Client, filters, enums, raw
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import CallbackQuery, ChatMemberUpdated, InlineKeyboardButton, InlineKeyboardMarkup, Message
from . import database as db

log = logging.getLogger(__name__)

LEAVE_PHOTO = 'https://i.ibb.co/jPrXjYVR/file-4262.jpg'

recent_dms: dict[int, float] = {}
DM_COOLDOWN = 10.0

ACTIVE_PARTICIPANT_TYPES = (
    raw.types.ChannelParticipant,
    raw.types.ChannelParticipantSelf,
    raw.types.ChannelParticipantAdmin,
    raw.types.ChannelParticipantCreator,
)


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def get_chat_link(client: Client, chat_id: int, username: str | None) -> str | None:
    if username:
        return f'https://t.me/{username}'
    try:
        link = await client.export_chat_invite_link(chat_id)
        return link
    except Exception:
        return None


async def send_leave_dm(
    client: Client,
    user_id: int,
    dm_text: str,
    keyboard: InlineKeyboardMarkup | None,
) -> None:
    now = time.monotonic()
    if now - recent_dms.get(user_id, 0.0) < DM_COOLDOWN:
        return
    recent_dms[user_id] = now

    try:
        await client.send_photo(
            user_id,
            LEAVE_PHOTO,
            caption=dm_text,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
        )
        return
    except Exception:
        pass

    try:
        await client.send_message(
            user_id,
            dm_text,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as exc:
        log.debug('leave: ᴄᴏᴜʟᴅ ɴᴏᴛ ᴅᴍ ᴜꜱᴇʀ %s — %s', user_id, exc)


def build_leave_dm(user_name: str, chat_name_html: str) -> str:
    return (
        f'ʜᴇʏ {user_name}! 👋\n\n'
        f'😢 ᴡᴇ ɴᴏᴛɪᴄᴇᴅ ʏᴏᴜ ʟᴇꜰᴛ {chat_name_html}\n'
        f'<blockquote>'
        f'ᴡᴇ ᴡᴏᴜʟᴅ ʟᴏᴠᴇ ᴛᴏ ʜᴀᴠᴇ ʏᴏᴜ ʙᴀᴄᴋ!\n'
        f'ᴄʟɪᴄᴋ ᴛʜᴇ ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ʀᴇᴊᴏɪɴ.\n'
        f'ᴛʏᴘᴇ /start ᴛᴏ ᴇxᴘʟᴏʀᴇ ᴡʜᴀᴛ ɪ ᴄᴀɴ ᴅᴏ!'
        f'</blockquote>'
    )


@Client.on_message(filters.command('leave_noti'))
async def leave_noti_cmd(client: Client, message: Message) -> None:
    chat = message.chat

    if chat.type == ChatType.PRIVATE:
        reply = await message.reply(
            '<b>ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴄᴀɴ ᴏɴʟʏ ʙᴇ ᴜꜱᴇᴅ ɪɴ ɢʀᴏᴜᴘꜱ ᴏʀ ᴄʜᴀɴɴᴇʟꜱ.</b>',
            parse_mode=enums.ParseMode.HTML,
        )
        await asyncio.sleep(5)
        try:
            await message.delete()
        except Exception:
            pass
        try:
            await reply.delete()
        except Exception:
            pass
        return

    if chat.type != ChatType.CHANNEL:
        if not message.from_user:
            return
        if not await is_admin(client, chat.id, message.from_user.id):
            await message.reply(
                '<b>ʏᴏᴜ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ᴜꜱᴇ ᴛʜɪꜱ ᴄᴏᴍᴍᴀɴᴅ.</b>',
                parse_mode=enums.ParseMode.HTML,
            )
            return

    try:
        await message.delete()
    except Exception:
        pass

    enabled = await db.is_leave_noti_enabled(chat.id)
    status_str = 'ᴇɴᴀʙʟᴇᴅ' if enabled else 'ᴅɪꜱᴀʙʟᴇᴅ'
    text = (
        '<b>ʟᴇᴀᴠᴇ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ꜱᴇᴛᴛɪɴɢꜱ</b>\n'
        '<blockquote>'
        f'ᴄᴜʀʀᴇɴᴛ ꜱᴛᴀᴛᴜꜱ: <b>{status_str}</b>\n\n'
        'ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴛᴏɢɢʟᴇ:'
        '</blockquote>'
    )
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton('ᴇɴᴀʙʟᴇ', callback_data=f'leave_enable:{chat.id}'),
            InlineKeyboardButton('ᴅɪꜱᴀʙʟᴇ', callback_data=f'leave_disable:{chat.id}'),
        ]
    ])
    await client.send_message(chat.id, text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex(r'^leave_(enable|disable):(-?\d+)$'))
async def leave_noti_callback(client: Client, callback_query: CallbackQuery) -> None:
    data = callback_query.data
    parts = data.split(':')
    action = parts[0]
    chat_id = int(parts[1])

    user = callback_query.from_user
    if not await is_admin(client, chat_id, user.id):
        await callback_query.answer(
            'ʏᴏᴜ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜɪꜱ ꜱᴇᴛᴛɪɴɢ.',
            show_alert=True,
        )
        return

    if action == 'leave_enable':
        await db.enable_leave_noti(chat_id)
        answer_text = 'ʟᴇᴀᴠᴇ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ᴇɴᴀʙʟᴇᴅ ꜰᴏʀ ᴛʜɪꜱ ᴄʜᴀᴛ.'
    else:
        await db.disable_leave_noti(chat_id)
        answer_text = 'ʟᴇᴀᴠᴇ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ʜᴀꜱ ʙᴇᴇɴ ᴅɪꜱᴀʙʟᴇᴅ ꜰᴏʀ ᴛʜɪꜱ ᴄʜᴀᴛ.'

    await callback_query.answer(answer_text, show_alert=True)
    try:
        await callback_query.message.delete()
    except Exception:
        pass


@Client.on_raw_update(group=1)
async def raw_channel_leave(client: Client, update, users, chats) -> None:
    if not isinstance(update, raw.types.UpdateChannelParticipant):
        return

    old_p = update.prev_participant
    new_p = update.new_participant

    was_active = isinstance(old_p, ACTIVE_PARTICIPANT_TYPES)
    now_left = new_p is None or isinstance(new_p, raw.types.ChannelParticipantBanned)

    if not (was_active and now_left):
        return

    channel_id = update.channel_id
    chat_id = int(f'-100{channel_id}')
    user_id = update.user_id

    enabled = await db.is_leave_noti_enabled(chat_id)
    if not enabled:
        return

    raw_user = users.get(user_id)
    if not raw_user or getattr(raw_user, 'bot', False):
        return

    min_hash = getattr(raw_user, 'access_hash', None)
    if min_hash:
        await db.save_peer_hash(user_id, min_hash)
        try:
            await client.fetch_peers([raw_user])
        except Exception:
            pass

    first_name = getattr(raw_user, 'first_name', '') or str(user_id)
    raw_chat = chats.get(channel_id)
    chat_username = getattr(raw_chat, 'username', None)
    chat_title = getattr(raw_chat, 'title', None) or str(chat_id)

    chat_link = await get_chat_link(client, chat_id, chat_username)
    chat_name_html = f'<a href="{chat_link}">{chat_title}</a>' if chat_link else f'<b>{chat_title}</b>'

    dm_text = build_leave_dm(first_name, chat_name_html)

    buttons = []
    if chat_link:
        buttons.append([InlineKeyboardButton(f'ʀᴇᴊᴏɪɴ {chat_title}', url=chat_link)])
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None

    await send_leave_dm(client, user_id, dm_text, keyboard)


@Client.on_chat_member_updated(group=1)
async def on_member_left(client: Client, update: ChatMemberUpdated) -> None:
    old = update.old_chat_member
    new = update.new_chat_member

    if not old or not new:
        return

    was_member = old.status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.RESTRICTED,
    )
    now_left = new.status == ChatMemberStatus.LEFT

    if not (was_member and now_left):
        return

    user = new.user
    chat = update.chat

    if not user or user.is_bot:
        return

    enabled = await db.is_leave_noti_enabled(chat.id)
    if not enabled:
        return

    try:
        peer = await client.resolve_peer(user.id)
        h = getattr(peer, 'access_hash', None)
        if h:
            await db.save_peer_hash(user.id, h)
    except Exception:
        pass

    name = user.first_name or 'ᴜꜱᴇʀ'
    chat_title = chat.title or 'ᴏᴜʀ ɢʀᴏᴜᴘ'
    chat_link = await get_chat_link(client, chat.id, getattr(chat, 'username', None))
    chat_name_html = f'<a href="{chat_link}">{chat_title}</a>' if chat_link else f'<b>{chat_title}</b>'

    dm_text = build_leave_dm(name, chat_name_html)

    buttons = []
    if chat_link:
        buttons.append([InlineKeyboardButton(f'↩️ ʀᴇᴊᴏɪɴ {chat_title}', url=chat_link)])
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None

    await send_leave_dm(client, user.id, dm_text, keyboard)
