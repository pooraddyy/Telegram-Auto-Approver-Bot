import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
import config
log = logging.getLogger(__name__)
mongo_client: AsyncIOMotorClient | None = None
chat_coll: AsyncIOMotorCollection | None = None
user_coll: AsyncIOMotorCollection | None = None
disable_coll: AsyncIOMotorCollection | None = None
session_coll: AsyncIOMotorCollection | None = None
leave_noti_coll: AsyncIOMotorCollection | None = None
peer_hash_coll: AsyncIOMotorCollection | None = None

async def connect() -> None:
    global mongo_client, chat_coll, user_coll, disable_coll, session_coll, leave_noti_coll, peer_hash_coll
    mongo_client = AsyncIOMotorClient(config.DB_URL, serverSelectionTimeoutMS=5000)
    await mongo_client.admin.command('ping')
    db = mongo_client[config.DB_NAME]
    chat_coll = db['chats']
    user_coll = db['users']
    disable_coll = db['disabled']
    session_coll = db['sessions']
    leave_noti_coll = db['leave_noti']
    peer_hash_coll = db['peer_cache']
    await chat_coll.create_index('chat_id', unique=True, background=True)
    await user_coll.create_index('user_id', unique=True, background=True)
    await disable_coll.create_index('chat_id', unique=True, background=True)
    await session_coll.create_index('user_id', unique=True, background=True)
    await leave_noti_coll.create_index('chat_id', unique=True, background=True)
    log.info('MongoDB connected — database: %s', config.DB_NAME)

async def get_served_chats() -> list[dict]:
    cursor = chat_coll.find({'chat_id': {'$lt': 0}})
    return await cursor.to_list(length=None)

async def is_served_chat(chat_id: int) -> bool:
    return await chat_coll.find_one({'chat_id': chat_id}) is not None

async def add_served_chat(chat_id: int) -> None:
    if not await is_served_chat(chat_id):
        try:
            await chat_coll.insert_one({'chat_id': chat_id})
        except Exception:
            pass

async def get_chat_count() -> int:
    return await chat_coll.count_documents({})

async def get_served_users() -> list[dict]:
    cursor = user_coll.find({'user_id': {'$gt': 0}})
    return await cursor.to_list(length=None)

async def is_served_user(user_id: int) -> bool:
    return await user_coll.find_one({'user_id': user_id}) is not None

async def add_served_user(user_id: int) -> None:
    if not await is_served_user(user_id):
        try:
            await user_coll.insert_one({'user_id': user_id})
        except Exception:
            pass

async def get_user_count() -> int:
    return await user_coll.count_documents({})

async def is_approve_enabled(chat_id: int) -> bool:
    result = await disable_coll.find_one({'chat_id': chat_id})
    return result is None

async def disable_approve(chat_id: int) -> None:
    if await is_approve_enabled(chat_id):
        try:
            await disable_coll.insert_one({'chat_id': chat_id})
        except Exception:
            pass

async def enable_approve(chat_id: int) -> None:
    if not await is_approve_enabled(chat_id):
        await disable_coll.delete_one({'chat_id': chat_id})

async def save_session(user_id: int, session_string: str) -> None:
    await session_coll.update_one(
        {'user_id': user_id},
        {'$set': {'user_id': user_id, 'session': session_string}},
        upsert=True,
    )

async def get_session(user_id: int) -> str | None:
    doc = await session_coll.find_one({'user_id': user_id})
    return doc['session'] if doc else None

async def delete_session(user_id: int) -> None:
    await session_coll.delete_one({'user_id': user_id})

async def is_leave_noti_enabled(chat_id: int) -> bool:
    return await leave_noti_coll.find_one({'chat_id': chat_id}) is not None

async def enable_leave_noti(chat_id: int) -> None:
    if not await is_leave_noti_enabled(chat_id):
        try:
            await leave_noti_coll.insert_one({'chat_id': chat_id})
        except Exception:
            pass

async def disable_leave_noti(chat_id: int) -> None:
    await leave_noti_coll.delete_one({'chat_id': chat_id})

async def save_peer_hash(user_id: int, access_hash: int) -> None:
    try:
        await peer_hash_coll.update_one(
            {'_id': user_id},
            {'$set': {'access_hash': access_hash}},
            upsert=True,
        )
    except Exception:
        pass

