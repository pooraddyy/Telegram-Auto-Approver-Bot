import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.enums import ChatType, ChatMemberStatus
from pyrogram.errors import SessionPasswordNeeded
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
import config
from . import database as db

log = logging.getLogger(__name__)

login_state: dict[int, dict] = {}
active_tasks: dict[int, asyncio.Event] = {}


async def is_admin(client: Client, chat_id: int, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


def stop_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton('ꜱᴛᴏᴘ', callback_data=f'stop_approve:{chat_id}')],
    ])


@Client.on_message(filters.command('login') & filters.private)
async def login_cmd(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if await db.get_session(uid):
        await message.reply(
            '<b>✅ ᴀᴄᴄᴏᴜɴᴛ ᴀʟʀᴇᴀᴅʏ ʟᴏɢɢᴇᴅ ɪɴ.</b>\n\nᴜꜱᴇ /logout ᴛᴏ ʟᴏɢ ᴏᴜᴛ ꜰɪʀꜱᴛ.',
            parse_mode=enums.ParseMode.HTML,
        )
        return
    prompt = await message.reply(
        '<b>ꜱᴇɴᴅ ʏᴏᴜʀ ᴘʜᴏɴᴇ ɴᴜᴍʙᴇʀ</b>\n\n<i>ᴇxᴀᴍᴘʟᴇ: +91XXXXXXXXXX</i>\n<blockquote>Use /cancel to stop the process.</blockquote>',
        parse_mode=enums.ParseMode.HTML,
    )
    login_state[uid] = {'step': 'phone', 'prompt_msg': prompt, 'login_msg': message}


@Client.on_message(filters.command('logout') & filters.private)
async def logout_cmd(client: Client, message: Message) -> None:
    uid = message.from_user.id
    if not await db.get_session(uid):
        reply = await message.reply(
            '<b>ɴᴏ ᴀᴄᴄᴏᴜɴᴛ ɪꜱ ʟᴏɢɢᴇᴅ ɪɴ.</b>',
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
    await db.delete_session(uid)
    login_state.pop(uid, None)
    await message.reply(
        '<b>✅ ᴀᴄᴄᴏᴜɴᴛ ʟᴏɢɢᴇᴅ ᴏᴜᴛ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.</b>',
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(filters.command('cancel') & filters.private)
async def cancel_cmd(client: Client, message: Message) -> None:
    uid = message.from_user.id
    state = login_state.pop(uid, None)
    if state is None:
        reply = await message.reply(
            '<b>ɴᴏ ᴀᴄᴛɪᴠᴇ ᴘʀᴏᴄᴇꜱꜱ ᴛᴏ ᴄᴀɴᴄᴇʟ.</b>',
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
    tmp: Client | None = state.get('tmp')
    if tmp:
        try:
            await tmp.disconnect()
        except Exception:
            pass
    for msg in (state.get('login_msg'), state.get('prompt_msg'), message):
        if msg:
            try:
                await msg.delete()
            except Exception:
                pass
    await client.send_message(
        uid,
        '<b>✅ ᴘʀᴏᴄᴇꜱꜱ ᴄᴀɴᴄᴇʟʟᴇᴅ.</b>',
        parse_mode=enums.ParseMode.HTML,
    )


@Client.on_message(
    filters.private & ~filters.command([
        'login', 'logout', 'cancel', 'approve_all', 'start', 'ping',
        'broadcast', 'pbroadcast', 'stats', 'restart', 'autoapprove', 'leave_noti',
        'checkperms',
    ]),
    group=10,
)
async def handle_login_input(client: Client, message: Message) -> None:
    if not message.from_user:
        return
    uid = message.from_user.id
    if uid not in login_state:
        return
    state = login_state[uid]

    if state['step'] == 'phone':
        phone = message.text.strip() if message.text else ''
        if not phone:
            return

        prompt_msg = state.get('prompt_msg')
        if prompt_msg:
            try:
                await prompt_msg.delete()
            except Exception:
                pass
        try:
            await message.delete()
        except Exception:
            pass

        wait_msg = await client.send_message(
            uid,
            '<b>ᴘʟᴇᴀꜱᴇ ᴡᴀɪᴛ...</b>',
            parse_mode=enums.ParseMode.HTML,
        )

        tmp = Client(':memory:', api_id=config.API_ID, api_hash=config.API_HASH)
        await tmp.connect()
        try:
            sent = await tmp.send_code(phone)
        except Exception as exc:
            await tmp.disconnect()
            del login_state[uid]
            await wait_msg.edit_text(
                f'<b>❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇɴᴅ ᴄᴏᴅᴇ:</b> <code>{exc}</code>',
                parse_mode=enums.ParseMode.HTML,
            )
            return

        login_state[uid] = {
            'step': 'code',
            'phone': phone,
            'phone_code_hash': sent.phone_code_hash,
            'tmp': tmp,
            'otp_msg': wait_msg,
        }

        await wait_msg.edit_text(
            '<b>ᴏᴛᴘ ꜱᴇɴᴛ!</b>\n\n'
            'ᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ᴛʜᴇ ᴄᴏᴅᴇ ʏᴏᴜ ʀᴇᴄᴇɪᴠᴇᴅ ᴏɴ ᴛᴇʟᴇɢʀᴀᴍ.\n\n'
            '<i>ɪꜰ ᴏᴛᴘ ɪꜱ 12345, ꜱᴇɴᴅ ɪᴛ ᴀꜱ: <code>1 2 3 4 5</code></i>',
            parse_mode=enums.ParseMode.HTML,
        )

    elif state['step'] == 'code':
        raw_code = message.text.strip() if message.text else ''
        if not raw_code:
            return
        code = raw_code.replace(' ', '')

        otp_msg = state.get('otp_msg')
        try:
            await message.delete()
        except Exception:
            pass
        if otp_msg:
            try:
                await otp_msg.delete()
            except Exception:
                pass

        tmp: Client = state['tmp']
        try:
            await tmp.sign_in(state['phone'], state['phone_code_hash'], code)
        except SessionPasswordNeeded:
            new_msg = await client.send_message(
                uid,
                '<b>2ꜰᴀ ᴇɴᴀʙʟᴇᴅ.</b>\n\nᴘʟᴇᴀꜱᴇ ꜱᴇɴᴅ ʏᴏᴜʀ 2ꜰᴀ ᴘᴀꜱꜱᴡᴏʀᴅ.',
                parse_mode=enums.ParseMode.HTML,
            )
            login_state[uid] = {**state, 'step': 'password', 'otp_msg': new_msg}
            return
        except Exception as exc:
            await tmp.disconnect()
            del login_state[uid]
            await client.send_message(
                uid,
                f'<b>❌ ʟᴏɢɪɴ ꜰᴀɪʟᴇᴅ:</b> <code>{exc}</code>',
                parse_mode=enums.ParseMode.HTML,
            )
            return

        session_string = await tmp.export_session_string()
        await tmp.disconnect()
        await db.save_session(uid, session_string)
        del login_state[uid]
        await client.send_message(
            uid,
            '<b>✅ ʟᴏɢɪɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ!</b>\n\nʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ /approve_all ɪɴ ᴀɴʏ ɢʀᴏᴜᴘ ᴏʀ ᴄʜᴀɴɴᴇʟ.',
            parse_mode=enums.ParseMode.HTML,
        )

    elif state['step'] == 'password':
        password = message.text.strip() if message.text else ''
        if not password:
            return

        otp_msg = state.get('otp_msg')
        try:
            await message.delete()
        except Exception:
            pass
        if otp_msg:
            try:
                await otp_msg.delete()
            except Exception:
                pass

        tmp: Client = state['tmp']
        try:
            await tmp.check_password(password)
            session_string = await tmp.export_session_string()
            await tmp.disconnect()
            await db.save_session(uid, session_string)
            del login_state[uid]
            await client.send_message(
                uid,
                '<b>✅ ʟᴏɢɪɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ!</b>\n\nʏᴏᴜ ᴄᴀɴ ɴᴏᴡ ᴜꜱᴇ /approve_all ɪɴ ᴀɴʏ ɢʀᴏᴜᴘ ᴏʀ ᴄʜᴀɴɴᴇʟ.',
                parse_mode=enums.ParseMode.HTML,
            )
        except Exception as exc:
            await tmp.disconnect()
            del login_state[uid]
            await client.send_message(
                uid,
                f'<b>❌ ᴘᴀꜱꜱᴡᴏʀᴅ ɪɴᴄᴏʀʀᴇᴄᴛ:</b> <code>{exc}</code>',
                parse_mode=enums.ParseMode.HTML,
            )


@Client.on_callback_query(filters.regex(r'^stop_approve:(-?\d+)$'))
async def stop_approve_callback(client: Client, callback_query: CallbackQuery) -> None:
    chat_id = int(callback_query.data.split(':')[1])
    user_id = callback_query.from_user.id
    if user_id != config.OWNER_ID and not await is_admin(client, chat_id, user_id):
        await callback_query.answer('ɴᴏ ᴘᴇʀᴍɪꜱꜱɪᴏɴ.', show_alert=True)
        return
    if chat_id in active_tasks:
        active_tasks[chat_id].set()
        await callback_query.answer('ᴀᴘᴘʀᴏᴠᴇ ᴀʟʟ ꜱᴛᴏᴘᴘᴇᴅ!', show_alert=True)
    else:
        await callback_query.answer('ɴᴏ ᴀᴄᴛɪᴠᴇ ᴛᴀꜱᴋ ꜰᴏᴜɴᴅ.', show_alert=True)


@Client.on_message(filters.command('approve_all'))
async def approve_all_cmd(client: Client, message: Message) -> None:
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

    requester_id = message.from_user.id if message.from_user else config.OWNER_ID
    notify_id = requester_id

    session = await db.get_session(requester_id)
    if not session and requester_id != config.OWNER_ID:
        session = await db.get_session(config.OWNER_ID)

    if not session:
        await client.send_message(
            notify_id,
            '<b>ᴘʟᴇᴀꜱᴇ /login ꜰɪʀꜱᴛ ᴛᴏ ᴜꜱᴇ /approve_all.</b>',
            parse_mode=enums.ParseMode.HTML,
        )
        return

    stop_event = asyncio.Event()
    active_tasks[chat.id] = stop_event

    userbot = Client(
        ':memory:',
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        session_string=session,
    )

    status_msg = None
    try:
        await userbot.start()

        status_msg = await client.send_message(
            notify_id,
            f'<b>ꜰᴇᴛᴄʜɪɴɢ ᴘᴇɴᴅɪɴɢ ʀᴇqᴜᴇꜱᴛꜱ ꜰʀᴏᴍ {chat.title}...</b>',
            parse_mode=enums.ParseMode.HTML,
        )

        pending = [req async for req in userbot.get_chat_join_requests(chat.id)]
        total = len(pending)

        if total == 0:
            await status_msg.edit_text(
                f'<b>✅ ɴᴏ ᴘᴇɴᴅɪɴɢ ʀᴇqᴜᴇꜱᴛꜱ ɪɴ {chat.title}.</b>',
                parse_mode=enums.ParseMode.HTML,
            )
            return

        await status_msg.edit_text(
            f'<b>ᴀᴘᴘʀᴏᴠɪɴɢ {total} ʀᴇqᴜᴇꜱᴛꜱ ɪɴ {chat.title}...</b>',
            parse_mode=enums.ParseMode.HTML,
            reply_markup=stop_keyboard(chat.id),
        )

        while not stop_event.is_set():
            try:
                await userbot.approve_all_chat_join_requests(chat.id)
            except Exception as exc:
                log.debug('approve_all: batch error — %s', exc)

            await asyncio.sleep(1)

            remaining = [req async for req in userbot.get_chat_join_requests(chat.id)]
            approved = total - len(remaining)

            if len(remaining) == 0:
                break

            bars = int(approved / total * 10) if total else 10
            bar = '█' * bars + '░' * (10 - bars)
            pct = int(approved / total * 100) if total else 100
            try:
                await status_msg.edit_text(
                    f'<b>⚙️ ᴀᴘᴘʀᴏᴠɪɴɢ — {chat.title}</b>\n\n'
                    f'<code>[{bar}] {pct}%</code>\n\n'
                    f'<blockquote>'
                    f'✅ ᴀᴘᴘʀᴏᴠᴇᴅ : {approved}\n'
                    f'⏳ ʀᴇᴍᴀɪɴɪɴɢ : {len(remaining)}\n'
                    f'📊 ᴛᴏᴛᴀʟ    : {total}'
                    f'</blockquote>',
                    parse_mode=enums.ParseMode.HTML,
                    reply_markup=stop_keyboard(chat.id),
                )
            except Exception:
                pass

        stopped_early = stop_event.is_set()
        header = '<b>ᴀᴘᴘʀᴏᴠᴇ ꜱᴛᴏᴘᴘᴇᴅ!</b>' if stopped_early else '<b>✅ ᴀᴘᴘʀᴏᴠᴇ ᴀʟʟ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>'

        remaining_final = [req async for req in userbot.get_chat_join_requests(chat.id)]
        approved_final = total - len(remaining_final)
        failed_final = len(remaining_final) if stopped_early else 0

        await status_msg.edit_text(
            f'{header}\n\n'
            f'<blockquote>'
            f'ᴄʜᴀᴛ : {chat.title}\n'
            f'✅ ᴀᴘᴘʀᴏᴠᴇᴅ : {approved_final}\n'
            f'❌ ꜰᴀɪʟᴇᴅ    : {failed_final}\n'
            f'📊 ᴛᴏᴛᴀʟ    : {total}'
            f'</blockquote>',
            parse_mode=enums.ParseMode.HTML,
        )

    except Exception as exc:
        log.error('approve_all: error — %s', exc)
        if status_msg:
            try:
                await status_msg.edit_text(
                    f'<b>❌ ᴇʀʀᴏʀ:</b> <code>{exc}</code>',
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass
        else:
            try:
                await client.send_message(
                    notify_id,
                    f'<b>❌ ᴇʀʀᴏʀ:</b> <code>{exc}</code>',
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass
    finally:
        active_tasks.pop(chat.id, None)
        try:
            await userbot.stop()
        except Exception:
            pass
