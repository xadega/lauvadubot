import json
import os
from telethon.sessions import StringSession
from telethon import TelegramClient
from dotenv import load_dotenv, set_key, get_key

load_dotenv("config.env")


api_id = int(os.environ.get("API_ID"))
api_hash = os.environ.get("API_HASH")
target = os.environ.get("TARGET")
delay = int(os.environ.get("DELAY"))
owner = int(os.environ.get("OWNER"))
sticker_pack = os.environ.get("STICKER_PACK")
tmp_bot = []
for i in range(1, 50):
    session = os.environ.get(f"SESSION{i}")
    if session:
        client = TelegramClient(StringSession(session), api_id, api_hash)
        tmp_bot.append(client)
print(len(tmp_bot), "SESSION Terdeteksi")
bots = tmp_bot.copy()


def up_conf(key, value):
    return set_key("config.env", key, value)

def get_conf(key):
    return get_key("config.env", key)
