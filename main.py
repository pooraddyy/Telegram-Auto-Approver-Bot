import asyncio
import logging
import os
import sys
from aiohttp import web
from pyrogram import Client, enums
from pyrogram.errors import RPCError
import config
from plugins import database as db

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s — %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger('pyrogram').setLevel(logging.WARNING)
logging.getLogger('motor').setLevel(logging.WARNING)
log = logging.getLogger('AutoApproveBot')

PORT: int = int(os.getenv('PORT', '8080'))


async def health_handler(request: web.Request) -> web.Response:
    return web.Response(text='OK')


async def start_web_server() -> None:
    app = web.Application()
    app.router.add_get('/', health_handler)
    app.router.add_get('/health', health_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    log.info('Health server running on port %s', PORT)


def remove_conversation_handlers(app: Client) -> None:
    try:
        from pyrogram.handlers import ConversationHandler
        removed = 0
        for group in list(app.dispatcher.groups.keys()):
            before = len(app.dispatcher.groups[group])
            app.dispatcher.groups[group] = [
                h for h in app.dispatcher.groups[group]
                if not isinstance(h, ConversationHandler)
            ]
            removed += before - len(app.dispatcher.groups[group])
        if removed:
            log.info('Removed %d ConversationHandler(s)', removed)
    except (ImportError, AttributeError):
        pass


async def main() -> None:
    log.info('Connecting to MongoDB...')
    try:
        await db.connect()
    except Exception as exc:
        log.critical('Failed to connect to MongoDB: %s', exc)
        sys.exit(1)

    await start_web_server()

    app = Client(
        name='auto_approve_bot',
        bot_token=config.TOKEN,
        api_id=config.API_ID,
        api_hash=config.API_HASH,
        plugins={'root': 'plugins'},
        sleep_threshold=60,
        workers=8,
    )

    @app.on_error()
    async def on_handler_error(client: Client, update, exception: Exception) -> None:
        log.error(
            'Handler error on %s: %s — %s',
            type(update).__name__, type(exception).__name__, exception,
            exc_info=True,
        )

    log.info('Starting bot...')
    await app.start()
    await asyncio.sleep(0)

    remove_conversation_handlers(app)

    me = await app.get_me()
    log.info('Bot running as @%s (id=%s)', me.username, me.id)
    try:
        await app.send_message(
            config.OWNER_ID,
            '<blockquote><b>ʙᴏᴛ ꜱᴛᴀʀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ! ✅</b></blockquote>',
            parse_mode=enums.ParseMode.HTML,
        )
    except RPCError as exc:
        log.warning('Could not notify owner: %s', exc)

    log.info('Bot is online. Press Ctrl+C to stop.')
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        log.info('Shutting down...')
        await app.stop()
        log.info('Bot stopped.')


if __name__ == '__main__':
    asyncio.run(main())
