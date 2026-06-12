import os
import sys
from dotenv import load_dotenv
load_dotenv()
TOKEN: str = os.getenv('TOKEN', '')
API_ID: int = int(os.getenv('API_ID', '0'))
API_HASH: str = os.getenv('API_HASH', '')
OWNER_ID: int = int(os.getenv('OWNER_ID', '5938660179'))
OWNER_USERNAME: str = os.getenv('OWNER_USERNAME', '')
DB_URL: str = os.getenv('DB_URL', '')
DB_NAME: str = os.getenv('DB_NAME', 'AutoApproveBot')
START_PHOTOS: list[str] = [
    u.strip()
    for u in os.getenv(
        'START_PHOTOS',
        'https://i.ibb.co/qFDxhDfG/file-4257.jpg,'
        'https://i.ibb.co/Lz5B7sKm/file-4258.jpg,'
        'https://i.ibb.co/0RqhDkTM/file-4259.jpg,'
        'https://i.ibb.co/Q7W4Xk7X/file-4260.jpg,'
        'https://i.ibb.co/v42TMxJj/file-4261.jpg,'
        'https://i.ibb.co/jPrXjYVR/file-4262.jpg,'
        'https://i.ibb.co/2YKzKNLv/file-4263.jpg',
    ).split(',')
    if u.strip()
]
PING_PHOTO: str = os.getenv('PING_PHOTO', 'https://i.ibb.co/wFy59Fq1/file-4265.jpg')
errors = []
if not TOKEN:
    errors.append('TOKEN env variable is required (get from @BotFather)')
if not API_ID:
    errors.append('API_ID env variable is required (get from https://my.telegram.org)')
if not API_HASH:
    errors.append('API_HASH env variable is required (get from https://my.telegram.org)')
if not DB_URL:
    errors.append('DB_URL env variable is required (MongoDB connection string)')
if errors:
    for err in errors:
        print(f'[CONFIG ERROR] {err}')
    sys.exit(1)
