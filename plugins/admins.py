import asyncio
import os
import sys
import logging
from pyrogram import Client, filters, enums
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
import config
from . import database as db

log = logging.getLogger(__name__)
owner_filter = filters.user(config.OWNER_ID)


def build_autoapprove_text(chat_id: int, enabled: bool) -> str:
    status_str = 'ᴇɴᴀʙʟᴇᴅ' if enabled else 'ᴅɪꜱᴀʙʟᴇᴅ'
    return (
        '<b>ᴀᴜᴛᴏ-ᴀᴘᴘʀᴏᴠᴇ ꜱᴇᴛᴛɪɴɢꜱ</b>\n'
        '<blockquote>'
        f'ᴄᴜʀʀᴇɴᴛ ꜱᴛᴀᴛᴜꜱ: <b>{status_str}</b>\n\n'
        'ᴜꜱᴇ ᴛʜᴇ ʙᴜᴛᴛᴏɴꜱ ʙᴇʟᴏᴡ ᴛᴏ ᴛᴏɢɢʟᴇ:'
        '</blockquote>\n'
        'ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀᴅᴍɪɴ ᴡɪᴛʜ\n'
        '"ɪɴᴠɪᴛᴇ ᴜꜱᴇʀꜱ ᴠɪᴀ ʟɪɴᴋ" ᴘᴇʀᴍɪꜱꜱɪᴏɴ.'
    )


def autoapprove_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton('ᴇɴᴀʙʟᴇ', callback_data=f'app_enable:{chat_id}'),
            InlineKeyboardButton('ᴅɪꜱᴀʙʟᴇ', callback_data=f'app_disable:{chat_id}'),
        ]
    ])


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


@Client.on_message(filters.command('autoapprove'))
async def auto_approve(client: Client, message: Message) -> None:
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

    enabled = await db.is_approve_enabled(chat.id)
    text = build_autoapprove_text(chat.id, enabled)
    keyboard = autoapprove_keyboard(chat.id)
    await client.send_message(chat.id, text, reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)


@Client.on_callback_query(filters.regex(r'^app_(enable|disable):(-?\d+)$'))
async def auto_approve_callback(client: Client, callback_query: CallbackQuery) -> None:
    parts = callback_query.data.split(':')
    action = parts[0]
    chat_id = int(parts[1])

    user = callback_query.from_user

    admin_ok = (user.id == config.OWNER_ID) or await is_admin(client, chat_id, user.id)
    if not admin_ok:
        await callback_query.answer('ʏᴏᴜ ᴍᴜꜱᴛ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ᴛᴏ ᴄʜᴀɴɢᴇ ᴛʜɪꜱ ꜱᴇᴛᴛɪɴɢ.', show_alert=True)
        return

    if action == 'app_enable':
        await db.enable_approve(chat_id)
        answer_text = 'ᴀᴜᴛᴏ-ᴀᴘᴘʀᴏᴠᴇ ʜᴀꜱ ʙᴇᴇɴ ᴇɴᴀʙʟᴇᴅ ꜰᴏʀ ᴛʜɪꜱ ᴄʜᴀᴛ.'
    else:
        await db.disable_approve(chat_id)
        answer_text = 'ᴀᴜᴛᴏ-ᴀᴘᴘʀᴏᴠᴇ ʜᴀꜱ ʙᴇᴇɴ ᴅɪꜱᴀʙʟᴇᴅ ꜰᴏʀ ᴛʜɪꜱ ᴄʜᴀᴛ.'

    await callback_query.answer(answer_text, show_alert=True)
    try:
        await callback_query.message.delete()
    except Exception:
        pass


@Client.on_message(filters.command('stats') & owner_filter)
async def stats(client: Client, message: Message) -> None:
    chat_count = await db.get_chat_count()
    user_count = await db.get_user_count()
    py_version = sys.version.split()[0]
    text = (
        '<b>ʙᴏᴛ ꜱᴛᴀᴛɪꜱᴛɪᴄꜱ</b>\n'
        '<blockquote>'
        f'ᴜꜱᴇʀꜱ ꜱᴇʀᴠᴇᴅ : <code>{user_count:,}</code>\n'
        f'ᴄʜᴀᴛꜱ ꜱᴇʀᴠᴇᴅ  : <code>{chat_count:,}</code>\n'
        f'ᴘʏᴛʜᴏɴ ᴠᴇʀꜱɪᴏɴ : <code>{py_version}</code>'
        '</blockquote>'
    )
    reply = await message.reply(text, parse_mode=enums.ParseMode.HTML)
    await asyncio.sleep(5)
    try:
        await message.delete()
    except Exception:
        pass
    try:
        await reply.delete()
    except Exception:
        pass


@Client.on_message(filters.command('restart') & owner_filter)
async def restart(client: Client, message: Message) -> None:
    await message.reply('<b>ʀᴇꜱᴛᴀʀᴛɪɴɢ ʙᴏᴛ...</b>', parse_mode=enums.ParseMode.HTML)
    os.execv(sys.executable, [sys.executable, 'main.py'])


@Client.on_message(filters.command('checkperms') & owner_filter)
async def check_perms(client: Client, message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.reply(
            '<b>ᴜꜱᴀɢᴇ:</b> <code>/checkperms &lt;chat_id&gt;</code>\n\n'
            '<i>ᴄʜᴀᴛ ɪᴅ ᴄᴀɴ ʙᴇ ɴᴇɢᴀᴛɪᴠᴇ ꜰᴏʀ ɢʀᴏᴜᴘꜱ, ᴇ.ɢ. -1001234567890</i>',
            parse_mode=enums.ParseMode.HTML,
        )
        return

    try:
        chat_id = int(args[1])
    except ValueError:
        await message.reply('<b>❌ ɪɴᴠᴀʟɪᴅ ᴄʜᴀᴛ ɪᴅ. ᴍᴜꜱᴛ ʙᴇ ᴀɴ ɪɴᴛᴇɢᴇʀ.</b>', parse_mode=enums.ParseMode.HTML)
        return

    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        status = member.status

        is_admin_status = status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
        privs = getattr(member, 'privileges', None)

        can_invite = True
        if privs is not None:
            can_invite = getattr(privs, 'can_invite_users', False)

        status_icon = '✅' if is_admin_status else '❌'
        invite_icon = '✅' if can_invite else '❌'

        approve_enabled = await db.is_approve_enabled(chat_id)
        approve_icon = '✅' if approve_enabled else '❌'

        lines = [
            f'<b>ʙᴏᴛ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ɪɴ <code>{chat_id}</code></b>\n',
            f'<blockquote>',
            f'{status_icon} ᴀᴅᴍɪɴ ꜱᴛᴀᴛᴜꜱ  : <b>{status.name}</b>\n',
            f'{invite_icon} ɪɴᴠɪᴛᴇ ᴜꜱᴇʀꜱ  : <b>{"ʏᴇꜱ" if can_invite else "ɴᴏ"}</b>\n',
            f'{approve_icon} ᴀᴜᴛᴏ-ᴀᴘᴘʀᴏᴠᴇ : <b>{"ᴇɴᴀʙʟᴇᴅ" if approve_enabled else "ᴅɪꜱᴀʙʟᴇᴅ"}</b>',
            f'</blockquote>',
        ]

        if not is_admin_status:
            lines.append('\n⚠️ <b>ʙᴏᴛ ɪꜱ ɴᴏᴛ ᴀɴ ᴀᴅᴍɪɴ!</b> ᴀᴅᴅ ɪᴛ ᴀꜱ ᴀᴅᴍɪɴ ꜰɪʀꜱᴛ.')
        elif not can_invite:
            lines.append('\n⚠️ <b>ᴍɪꜱꜱɪɴɢ "ɪɴᴠɪᴛᴇ ᴜꜱᴇʀꜱ ᴠɪᴀ ʟɪɴᴋ" ᴘᴇʀᴍɪꜱꜱɪᴏɴ!</b>\nᴇɴᴀʙʟᴇ ɪᴛ ɪɴ ᴀᴅᴍɪɴ ꜱᴇᴛᴛɪɴɢꜱ.')
        else:
            lines.append('\n✅ <b>ᴀʟʟ ᴘᴇʀᴍɪꜱꜱɪᴏɴꜱ ᴏᴋ!</b>')

        await message.reply(''.join(lines), parse_mode=enums.ParseMode.HTML)

    except Exception as exc:
        await message.reply(
            f'<b>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ᴄʜᴇᴄᴋ:</b> <code>{exc}</code>\n\n'
            '<i>ᴍᴀᴋᴇ ꜱᴜʀᴇ ᴛʜᴇ ʙᴏᴛ ɪꜱ ᴀ ᴍᴇᴍʙᴇʀ/ᴀᴅᴍɪɴ ᴏꜰ ᴛʜᴀᴛ ᴄʜᴀᴛ.</i>',
            parse_mode=enums.ParseMode.HTML,
        )
