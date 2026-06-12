import asyncio
import random
import sys
import time
import logging
from datetime import datetime, timezone, timedelta
from pyrogram import Client, filters, enums
from pyrogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from pyrogram.enums import ChatType
from . import database as db
import config
from .texts import START_CAPTION, ABOUT_TEXT

log = logging.getLogger(__name__)
START_TIME: float = time.time()

HELP_TEXT = (
    "<b>ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ</b>\n"
    "<blockquote>"
    "/start — ꜱᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ ᴀɴᴅ ᴏᴘᴇɴ ᴛʜᴇ ᴍᴀɪɴ ᴍᴇɴᴜ\n"
    "/ping — ᴄʜᴇᴄᴋ ʙᴏᴛ ʟᴀᴛᴇɴᴄʏ ᴀɴᴅ ᴜᴘᴛɪᴍᴇ\n"
    "/autoapprove — ᴛᴏɢɢʟᴇ ᴀᴜᴛᴏ-ᴀᴘᴘʀᴏᴠᴇ ᴏɴ/ᴏꜰꜰ ɪɴ ᴀ ɢʀᴏᴜᴘ ᴏʀ ᴄʜᴀɴɴᴇʟ\n"
    "/approve_all — ʙᴜʟᴋ ᴀᴘᴘʀᴏᴠᴇ ᴀʟʟ ᴘᴇɴᴅɪɴɢ ᴊᴏɪɴ ʀᴇqᴜᴇꜱᴛꜱ (ʀᴇqᴜɪʀᴇꜱ /login)\n"
    "/leave_noti — ᴛᴏɢɢʟᴇ ᴅᴍ ɴᴏᴛɪꜰɪᴄᴀᴛɪᴏɴ ᴡʜᴇɴ ᴀ ᴍᴇᴍʙᴇʀ ʟᴇᴀᴠᴇꜱ"
    "</blockquote>\n\n"
    "<b>ᴜꜱᴇʀʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅꜱ</b>\n"
    "<blockquote>"
    "/login — ʟᴏɢ ɪɴ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ ꜰᴏʀ ʙᴜʟᴋ ᴀᴘᴘʀᴏᴠᴇ\n"
    "/logout — ʟᴏɢ ᴏᴜᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ\n"
    "/cancel — ᴄᴀɴᴄᴇʟ ᴀɴʏ ᴀᴄᴛɪᴠᴇ ʟᴏɢɪɴ ᴘʀᴏᴄᴇꜱꜱ"
    "</blockquote>\n\n"
    "<b>ʜᴏᴡ ᴛᴏ ᴜꜱᴇ</b>\n"
    "<blockquote>"
    "1. ᴀᴅᴅ ᴍᴇ ᴀꜱ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴏʀ ᴄʜᴀɴɴᴇʟ\n"
    "2. ɢɪᴠᴇ <b>\"ɪɴᴠɪᴛᴇ ᴜꜱᴇʀꜱ ᴠɪᴀ ʟɪɴᴋ\"</b> ᴀᴅᴍɪɴ ᴘᴇʀᴍɪꜱꜱɪᴏɴ\n"
    "3. ᴇɴᴀʙʟᴇ ᴊᴏɪɴ ʀᴇqᴜᴇꜱᴛꜱ ᴏɴ ʏᴏᴜʀ ɪɴᴠɪᴛᴇ ʟɪɴᴋ\n"
    "4. ʀᴜɴ /autoapprove ɪɴ ᴛʜᴇ ᴄʜᴀᴛ ᴀɴᴅ ᴘʀᴇꜱꜱ ✅ ᴇɴᴀʙʟᴇ\n"
    "5. ꜰᴏʀ /approve_all: ꜰɪʀꜱᴛ /login ɪɴ ᴘᴍ, ᴛʜᴇɴ ʀᴜɴ ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ\n"
    "6. ᴏᴛᴘ ꜰᴏʀᴍᴀᴛ: ꜱᴇɴᴅ ᴅɪɢɪᴛꜱ ᴡɪᴛʜ ꜱᴘᴀᴄᴇꜱ ᴇ.ɢ. <code>1 2 3 4 5</code>"
    "</blockquote>\n\n"
    "<b>ɪᴍᴘᴏʀᴛᴀɴᴛ:</b> ᴛʜᴇ ɪɴᴠɪᴛᴇ ʟɪɴᴋ ᴍᴜꜱᴛ ʜᴀᴠᴇ\n"
    "<b>\"ᴀᴘᴘʀᴏᴠᴀʟ ʀᴇqᴜɪʀᴇᴅ\"</b> ᴛᴜʀɴᴇᴅ ᴏɴ ꜰᴏʀ ᴊᴏɪɴ ʀᴇqᴜᴇꜱᴛꜱ ᴛᴏ ꜰɪʀᴇ."
)


def get_start_keyboard(username: str, cmd_msg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ⇆', url=f'https://t.me/{username}?startgroup=true')],
        [
            InlineKeyboardButton('ᴀʙᴏᴜᴛ', callback_data=f'about:{cmd_msg_id}'),
            InlineKeyboardButton('ʜᴇʟᴘ', callback_data=f'help:{cmd_msg_id}'),
        ],
        [InlineKeyboardButton('⇆ ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ⇆', url=f'https://t.me/{username}?startchannel=true')],
    ])


def get_about_keyboard(cmd_msg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data=f'back:{cmd_msg_id}'),
            InlineKeyboardButton('✕ ᴄʟᴏꜱᴇ', callback_data=f'close:{cmd_msg_id}'),
        ],
    ])


def get_help_keyboard(cmd_msg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('ᴄʜᴀɴɴᴇʟ', url='https://t.me/+FzvCeGO-2ac0Njdl'),
            InlineKeyboardButton('ᴄᴏɴᴛᴀᴄᴛ', user_id=config.OWNER_ID),
        ],
        [
            InlineKeyboardButton('« ʙᴀᴄᴋ', callback_data=f'back:{cmd_msg_id}'),
            InlineKeyboardButton('✕ ᴄʟᴏꜱᴇ', callback_data=f'close:{cmd_msg_id}'),
        ],
    ])


async def flash_transition(query: CallbackQuery, caption: str, keyboard: InlineKeyboardMarkup) -> None:
    msg = await query.message.edit_media(
        InputMediaPhoto(media=random.choice(config.START_PHOTOS), caption='\u200b'),
        reply_markup=None,
    )
    await asyncio.sleep(0)
    await msg.edit_caption(caption, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command('start'))
async def start(client: Client, message: Message) -> None:
    me = await client.get_me()
    keyboard = get_start_keyboard(me.username or '', message.id)
    name = message.from_user.first_name if message.from_user else 'ᴜꜱᴇʀ'
    caption = START_CAPTION.format(name=name)
    photo_url = random.choice(config.START_PHOTOS)
    try:
        await client.send_photo(
            message.chat.id,
            photo_url,
            caption=caption,
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.HTML,
        )
    except Exception as e:
        log.error('send_photo failed (url=%s): %s', photo_url, e)
        await message.reply(caption, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
    if message.chat.type == ChatType.PRIVATE:
        if message.from_user:
            await db.add_served_user(message.from_user.id)
    else:
        await db.add_served_chat(message.chat.id)


@Client.on_callback_query(filters.regex(r'^help:(-?\d+)$'))
async def help_callback(client: Client, callback_query: CallbackQuery) -> None:
    await callback_query.answer()
    cmd_msg_id = int(callback_query.data.split(':')[1])
    await flash_transition(callback_query, HELP_TEXT, get_help_keyboard(cmd_msg_id))


@Client.on_callback_query(filters.regex(r'^about:(-?\d+)$'))
async def about_callback(client: Client, callback_query: CallbackQuery) -> None:
    await callback_query.answer()
    cmd_msg_id = int(callback_query.data.split(':')[1])
    await flash_transition(callback_query, ABOUT_TEXT, get_about_keyboard(cmd_msg_id))


@Client.on_callback_query(filters.regex(r'^back:(-?\d+)$'))
async def back_callback(client: Client, callback_query: CallbackQuery) -> None:
    await callback_query.answer()
    cmd_msg_id = int(callback_query.data.split(':')[1])
    me = await client.get_me()
    keyboard = get_start_keyboard(me.username or '', cmd_msg_id)
    name = callback_query.from_user.first_name if callback_query.from_user else 'ᴜꜱᴇʀ'
    caption = START_CAPTION.format(name=name)
    await flash_transition(callback_query, caption, keyboard)


@Client.on_callback_query(filters.regex(r'^close:(-?\d+)$'))
async def close_callback(client: Client, callback_query: CallbackQuery) -> None:
    await callback_query.answer()
    cmd_msg_id = int(callback_query.data.split(':')[1])
    chat_id = callback_query.message.chat.id
    for mid in (callback_query.message.id, cmd_msg_id):
        try:
            await client.delete_messages(chat_id, mid)
        except Exception:
            pass


def plural(n: int, unit: str) -> str:
    return f'{n} {unit}' if n == 1 else f'{n} {unit}s'


def format_uptime(seconds: int) -> str:
    parts: list[str] = []
    months, seconds = divmod(seconds, 30 * 24 * 3600)
    weeks, seconds = divmod(seconds, 7 * 24 * 3600)
    days, seconds = divmod(seconds, 24 * 3600)
    hours, seconds = divmod(seconds, 3600)
    minutes, secs = divmod(seconds, 60)
    if months:
        parts.append(plural(months, 'month'))
    if weeks:
        parts.append(plural(weeks, 'week'))
    if days:
        parts.append(plural(days, 'day'))
    if hours:
        parts.append(plural(hours, 'hour'))
    if minutes:
        parts.append(plural(minutes, 'minute'))
    if secs or not parts:
        parts.append(plural(secs, 'second'))
    return ' '.join(parts)


def build_ping_text(latency_ms: float, uptime_str: str, now_ist: str) -> str:
    py_ver = sys.version.split()[0]
    return (
        f'<b>ʟᴀᴛᴇɴᴄʏ  :</b> <code>{latency_ms:.2f} ms</code>\n'
        f'<b>ᴜᴘᴛɪᴍᴇ   :</b> <code>{uptime_str}</code>\n'
        f'<b>ᴛɪᴍᴇ     :</b> <code>{now_ist}</code>\n'
        f'<b>ᴘʏᴛʜᴏɴ  :</b> <code>{py_ver}</code>'
    )


def ping_keyboard(cmd_msg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('✕ ᴄʟᴏꜱᴇ', callback_data=f'ping_close:{cmd_msg_id}')],
    ])


@Client.on_callback_query(filters.regex(r'^ping_close:(-?\d+)$'))
async def ping_close_callback(client: Client, callback_query: CallbackQuery) -> None:
    await callback_query.answer()
    cmd_msg_id = int(callback_query.data.split(':')[1])
    chat_id = callback_query.message.chat.id
    for mid in (callback_query.message.id, cmd_msg_id):
        try:
            await client.delete_messages(chat_id, mid)
        except Exception:
            pass


@Client.on_message(filters.command('ping'))
async def ping(client: Client, message: Message) -> None:
    t0 = time.monotonic()
    keyboard = ping_keyboard(message.id)
    try:
        sent = await client.send_photo(
            message.chat.id,
            config.PING_PHOTO,
            caption='<code>...</code>',
            parse_mode=enums.ParseMode.HTML,
            reply_markup=keyboard,
        )
    except Exception:
        sent = await message.reply('<code>...</code>', parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        latency_ms = (time.monotonic() - t0) * 1000
        ist = timezone(timedelta(hours=5, minutes=30))
        now_ist = datetime.now(ist).strftime('%a, %d %b %Y %H:%M:%S UTC+05:30')
        uptime_str = format_uptime(int(time.time() - START_TIME))
        await sent.edit_text(build_ping_text(latency_ms, uptime_str, now_ist), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
        return
    latency_ms = (time.monotonic() - t0) * 1000
    ist = timezone(timedelta(hours=5, minutes=30))
    now_ist = datetime.now(ist).strftime('%a, %d %b %Y %H:%M:%S UTC+05:30')
    uptime_str = format_uptime(int(time.time() - START_TIME))
    await sent.edit_caption(build_ping_text(latency_ms, uptime_str, now_ist), parse_mode=enums.ParseMode.HTML, reply_markup=keyboard)
