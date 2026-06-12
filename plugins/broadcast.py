import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.raw.functions.messages import UpdatePinnedMessage
from pyrogram.types import Message
import config
from . import database as db

log = logging.getLogger(__name__)
owner_filter = filters.private & filters.user(config.OWNER_ID)
PM = enums.ParseMode.DISABLED


async def send_msg(client: Client, chat_id: int, msg: Message) -> None:
    cap = msg.caption or ""
    cents = msg.caption_entities

    if msg.text:
        await client.send_message(
            chat_id,
            text=msg.text,
            entities=msg.entities,
            parse_mode=PM,
            disable_web_page_preview=not getattr(msg, 'web_page', None),
        )
    elif msg.photo:
        await client.send_photo(
            chat_id,
            photo=msg.photo.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.document:
        await client.send_document(
            chat_id,
            document=msg.document.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.video:
        await client.send_video(
            chat_id,
            video=msg.video.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.audio:
        await client.send_audio(
            chat_id,
            audio=msg.audio.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.voice:
        await client.send_voice(
            chat_id,
            voice=msg.voice.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.animation:
        await client.send_animation(
            chat_id,
            animation=msg.animation.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.sticker:
        await client.send_sticker(chat_id, sticker=msg.sticker.file_id)
    elif msg.video_note:
        await client.send_video_note(chat_id, video_note=msg.video_note.file_id)
    else:
        await client.copy_message(
            chat_id=chat_id,
            from_chat_id=msg.chat.id,
            message_id=msg.id,
        )


async def send_and_pin(client: Client, chat_id: int, msg: Message) -> bool:
    cap = msg.caption or ""
    cents = msg.caption_entities
    sent = None

    if msg.text:
        sent = await client.send_message(
            chat_id,
            text=msg.text,
            entities=msg.entities,
            parse_mode=PM,
            disable_web_page_preview=not getattr(msg, 'web_page', None),
        )
    elif msg.photo:
        sent = await client.send_photo(
            chat_id,
            photo=msg.photo.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.document:
        sent = await client.send_document(
            chat_id,
            document=msg.document.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.video:
        sent = await client.send_video(
            chat_id,
            video=msg.video.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.audio:
        sent = await client.send_audio(
            chat_id,
            audio=msg.audio.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.voice:
        sent = await client.send_voice(
            chat_id,
            voice=msg.voice.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.animation:
        sent = await client.send_animation(
            chat_id,
            animation=msg.animation.file_id,
            caption=cap,
            caption_entities=cents,
            parse_mode=PM,
        )
    elif msg.sticker:
        sent = await client.send_sticker(chat_id, sticker=msg.sticker.file_id)
    elif msg.video_note:
        sent = await client.send_video_note(chat_id, video_note=msg.video_note.file_id)
    else:
        sent = await client.copy_message(
            chat_id=chat_id,
            from_chat_id=msg.chat.id,
            message_id=msg.id,
        )

    if not sent:
        return False

    try:
        peer = await client.resolve_peer(chat_id)
        await client.invoke(UpdatePinnedMessage(
            peer=peer,
            id=sent.id,
            silent=True,
            unpin=False,
            pm_oneside=False,
        ))
        return True
    except Exception as exc:
        log.debug('pbroadcast: ᴄᴏᴜʟᴅ ɴᴏᴛ ᴘɪɴ ɪɴ %s — %s', chat_id, exc)
        return False


@Client.on_message(filters.command('broadcast') & owner_filter)
async def broadcast(client: Client, message: Message) -> None:
    reply = message.reply_to_message
    if not reply:
        await message.reply('<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪᴛ.</b>', parse_mode=enums.ParseMode.HTML)
        return

    status = await message.reply('<b>ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...</b>', parse_mode=enums.ParseMode.HTML)

    served_users = await db.get_served_users()
    total = len(served_users)
    su, fu = 0, 0
    for i, doc in enumerate(served_users, 1):
        uid = doc.get('user_id')
        if not uid:
            continue
        try:
            await send_msg(client, int(uid), reply)
            su += 1
        except Exception as exc:
            log.debug('broadcast: skip user %s — %s', uid, exc)
            fu += 1
        if i % 10 == 0:
            try:
                await status.edit_text(
                    f'<b>ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...</b>\n<blockquote>ꜱᴇɴᴛ : {su}/{total}</blockquote>',
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    result = (
        '<b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n'
        '<blockquote>'
        f'ᴛᴏᴛᴀʟ   : {total}\n'
        f'ꜱᴇɴᴛ    : {su}\n'
        f'ʙʟᴏᴄᴋᴇᴅ : {fu}'
        '</blockquote>'
    )
    await status.edit_text(result, parse_mode=enums.ParseMode.HTML)


@Client.on_message(filters.command('pbroadcast') & owner_filter)
async def pbroadcast(client: Client, message: Message) -> None:
    reply = message.reply_to_message
    if not reply:
        await message.reply('<b>ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ ᴘɪɴɴᴇᴅ ʙʀᴏᴀᴅᴄᴀꜱᴛ ɪᴛ.</b>', parse_mode=enums.ParseMode.HTML)
        return

    status = await message.reply('<b>ᴘɪɴɴᴇᴅ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...</b>', parse_mode=enums.ParseMode.HTML)

    served_users = await db.get_served_users()
    total = len(served_users)
    su, fu, pinned = 0, 0, 0
    for i, doc in enumerate(served_users, 1):
        uid = doc.get('user_id')
        if not uid:
            continue
        try:
            was_pinned = await send_and_pin(client, int(uid), reply)
            su += 1
            if was_pinned:
                pinned += 1
        except Exception as exc:
            log.debug('pbroadcast: skip user %s — %s', uid, exc)
            fu += 1
        if i % 10 == 0:
            try:
                await status.edit_text(
                    f'<b>ᴘɪɴɴᴇᴅ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...</b>\n<blockquote>ꜱᴇɴᴛ : {su}/{total}</blockquote>',
                    parse_mode=enums.ParseMode.HTML,
                )
            except Exception:
                pass
        await asyncio.sleep(0.05)

    result = (
        '<b>ᴘɪɴɴᴇᴅ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n'
        '<blockquote>'
        f'ᴛᴏᴛᴀʟ   : {total}\n'
        f'ꜱᴇɴᴛ    : {su}\n'
        f'ᴘɪɴɴᴇᴅ  : {pinned}\n'
        f'ʙʟᴏᴄᴋᴇᴅ : {fu}'
        '</blockquote>'
    )
    await status.edit_text(result, parse_mode=enums.ParseMode.HTML)
