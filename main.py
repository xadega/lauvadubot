import asyncio
import pickle
import sys
import traceback

from telethon import events, types
from telethon.errors import FloodWaitError
from telethon.tl import functions
from telethon.tl.functions.messages import GetStickerSetRequest
import atexit
from init import *

loop = asyncio.get_event_loop()
spam_task = None
allowed_event = []
is_running = False
sticker_ready = False
sticker_data = None
stop_list = []
banned_list = []
bots_ready = []

class Sticker:
    sticker_id: int
    access_hash: int
    file_reference: bytes
    pack_id: int
    pack_access_hash: int
    document: types.Document

    def __init__(self, sticker_id, access_hash, file_reference, pack_id, pack_access_hash, document):
        self.sticker_id = sticker_id
        self.access_hash = access_hash
        self.file_reference = file_reference
        self.pack_id = pack_id
        self.pack_access_hash = pack_access_hash
        self.document = document
class Banned:
    user_id: int
    username: str
    first_name: str

    def __init__(self, user_id, username, first_name):
        self.user_id = user_id
        self.username = username
        self.first_name = first_name

async def bdrl_spam():
    global is_running
    while is_running:
        print("Spamming...")
        if not is_running:
            break
        try:
            for client in bots_ready:
                if not is_running:
                    break
                if client.is_run != True:
                    continue
                if client.meid in stop_list:
                    continue
                try:
                    await client.send_file(target, sticker_data.document)
                    await asyncio.sleep(1.5)
                    await client.send_message(target, "/next")
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except BaseException as e:
                    #e = traceback.format_exc()
                    #print(e)
                    continue
            await asyncio.sleep(delay)
        except Exception as e:
            #e = traceback.format_exc()
            #print(e)
            continue

def is_allowed(event, bdrl):
    global owner
    tmp_owner = [owner, bdrl.meid]
    if event.chat_id in tmp_owner or event.sender_id in tmp_owner:
        return True
    return False

async def check_sticker(bdrl):
    global sticker_data, sticker_ready
    try:
        if sticker_pack is None:
            return False
        pack = sticker_pack.split("#")
        try:
            get_sticker = await bdrl(
                GetStickerSetRequest(
                    types.InputStickerSetID(
                        id=int(pack[1]),
                        access_hash=int(pack[2]),
                    ),
                    hash=0,
                )
            )
        except Exception as e:
            return False
        for stik in get_sticker.documents:
            if stik.id == int(pack[0]):
                sticker_data = Sticker(
                    stik.id,
                    stik.access_hash,
                    stik.file_reference,
                    get_sticker.set.id,
                    get_sticker.set.access_hash,
                    stik
                )
                sticker_ready = True
                up_conf("STICKER_PACK", f"{stik.id}#{get_sticker.set.id}#{get_sticker.set.access_hash}")
                return True
    except Exception as e:
        print(e)
    return False


async def bdrl_helper(bdrl):
    global bots_ready
    async with bdrl:
        @bdrl.on(events.NewMessage(pattern=r'^!stop$'))
        async def _(event):
            global stop_list, is_running, spam_task
            if is_allowed(event, bdrl):
                stop_list.append(bdrl.meid)
                if len(stop_list) == 0:
                    is_running = False
                    bdrl.is_run = False
                    if spam_task is not None:
                        spam_task.cancel()
                await event.reply(f'Stopped current client')
        @bdrl.on(events.NewMessage(pattern=r'^!stopall$'))
        async def _(event):
            global stop_list, is_running, spam_task
            if is_allowed(event, bdrl):
                stop_list.clear()
                is_running = False
                for client in bots_ready:
                    client.is_run = False
                if spam_task is not None:
                    spam_task.cancel()
                    spam_task = None
                await event.reply(f'Stop all')

        @bdrl.on(events.NewMessage(pattern=r'^!runall$'))
        async def _(event):
            global is_running, stop_list, spam_task, sticker_data
            if is_allowed(event, bdrl):
                if sticker_data is None:
                    return await event.reply(f'Please set sticker first.')
                is_running = True
                for client in bots_ready:
                    client.is_run = True
                stop_list.clear()
                if spam_task is None:
                    spam_task = asyncio.create_task(bdrl_spam())
                await event.reply(f'Started')

        @bdrl.on(events.NewMessage(pattern=r'^!run$'))
        async def _(event):
            global is_running, stop_list, spam_task, sticker_data, bots_ready
            if is_allowed(event, bdrl):
                if sticker_data is None:
                    return await event.reply(f'Please set sticker first.')
                is_running = True
                bdrl.is_run = True
                if bdrl.meid in stop_list:
                    stop_list.remove(bdrl.meid)
                if spam_task is None:
                    spam_task = asyncio.create_task(bdrl_spam())
                await event.reply(f'Started')

        @bdrl.on(events.NewMessage(pattern=r'^!get'))
        async def _(event):
            global sticker_ready, sticker_data
            if not is_allowed(event, bdrl):
                return
            if not sticker_ready and not sticker_data:
                #await check_sticker(bdrl)
                return await event.reply(f'Please set sticker first.')
            await event.client.send_file(event.chat_id, sticker_data.document)

        @bdrl.on(events.NewMessage(pattern=r'^!set$'))
        async def _(event):
            global sticker_ready, sticker_data
            if not is_allowed(event, bdrl):
                return
            reply = await event.get_reply_message()
            if not reply.sticker:
                return await event.reply(f'Please reply to a sticker.')

            try:
                sticker_attr = reply.document.attributes[1]
            except BaseException as e:
                print(e)
                return await event.reply(event, "Not valid sticker, reply to a sticker.")

            try:
                get_sticker = await event.client(
                    GetStickerSetRequest(
                        types.InputStickerSetID(
                            id=sticker_attr.stickerset.id,
                            access_hash=sticker_attr.stickerset.access_hash,
                        ),
                        hash=0,
                    )
                )
                tmp_doc_id = reply.sticker.id
            except Exception as e:
                print(e)
                return await event.reply("Not valid sticker, reply to a sticker.")


            for stik in get_sticker.documents:
                if tmp_doc_id == stik.id:
                    sticker_ready = True
                    sticker_data = Sticker(
                        stik.id,
                        stik.access_hash,
                        stik.file_reference,
                        get_sticker.set.id,
                        get_sticker.set.access_hash,
                        stik
                    )
                    up_conf("STICKER_PACK", f"{stik.id}#{get_sticker.set.id}#{get_sticker.set.access_hash}")
                    await event.client.send_file(event.chat_id, stik)


        try:
            me = await bdrl.get_me()
            bdrl.meid = me.id
            bdrl.is_run = False
            print(me.first_name, 'Started')
            bots_ready.append(bdrl)
            if not sticker_ready and sticker_pack is not None:
                print("Detected sticker pack in config.env, load first")
                isLoaded = await check_sticker(bdrl)
                if isLoaded:
                    print("Sticker loaded")
            await bdrl.run_until_disconnected()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(e)
            pass


async def main():
    bdrl_jobs = [bdrl_helper(bdrl) for bdrl in bots]
    print("Starting ", len(bots), " client")
    print("Target: ", target)
    print("Delay: ", delay)
    try:
        await asyncio.gather(*bdrl_jobs)
    except KeyboardInterrupt:
        print("Stopping")
        sys.exit(0)
    except Exception as e:
        pass


if __name__ == '__main__':
    if not bots:
        print("Please add bots to the list in config.env")
        exit(1)
    try:
        asyncio.run(main())
        # loop.run_until_complete(main())
    except KeyboardInterrupt:
        sys.exit(0)
        pass
