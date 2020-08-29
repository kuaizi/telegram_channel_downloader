import os
import re
import subprocess
import time
import redis
from telethon import TelegramClient
from tqdm import tqdm
import logging

#---------------------------------------------------------------------------#
api_id = 1234567                                  # 你的telegram API ID
api_hash = '141e1403**********4d525d6c54f542'     # 你的telegram API hash
drive_id = '0ANGBw*****GSUk9PVA'                  # 要上传到的网盘ID
drive_name = 'gc'                                 # 配置文件中的网盘名称
save_path = '/usr/download'                       # 文件保存路径
chat = 'https://t.me/AnchorPorn'                  # 对话，可以是ID,群组名，分享链接都支持
bot_token = ''                                    # 用于发送消息。不填关闭功能
#-------------------------------------------------------------------------#

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
client = TelegramClient('anon', api_id, api_hash)
pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
if bot_token != '':
    bot = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)


class tqdm_up_to(tqdm):
    last_block = 0

    def my_update(self, total, current):
        return self.update_to(total, current)

    def update_to(self, current, total):
        self.update(current - self.last_block)
        self.last_block = current


def validateTitle(title):
    r_str = r"[\/\\\:\*\?\"\<\>\|\n]"  # '/ \ : * ? " < > |'
    new_title = re.sub(r_str, "_", title)  # 替换为下划线
    return new_title


async def get_group_caption(message):
    group_caption = ""
    entity = await client.get_entity(message.to_id)
    async for msg in client.iter_messages(entity=entity, reverse=True, offset_id=message.id - 9, limit=10):
        if msg.grouped_id == message.grouped_id:
            if msg.text != "":
                group_caption = msg.text
                return group_caption
    return group_caption


def get_local_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


async def main():
    me = await client.get_me()
    entity = await client.get_entity(chat)
    chat_title = entity.title
    if r.hexists('tg_channel_downloader', chat_title):
        offset_id = int(r.hget('tg_channel_downloader', chat_title))
    else:
        # 如果 redis没有缓存对话标题，设置offset_id 为0从最新开始的下载。
        offset_id = 0
    chat_id = int('-100' + str(f'{entity.id}'))
    print(f'{get_local_time()} - 开始下载：{chat_title}({chat_id})')
    dirname = validateTitle(f'{chat_title}({chat_id})')
    async for message in client.iter_messages(entity=chat, reverse=True, offset_id=offset_id, limit=None):
        file_name = ''
        # 判断是否是媒体文件。包含各种文件和视频、图片。
        if message.media:
            # 判断媒体文件是否有附加文本 还要限制文本长度并处理特殊符号
            if message.grouped_id:  # 如果是一组媒体
                if message.text == "":
                    group_caption = await get_group_caption(message)
                    # print(group_caption)
                    caption = group_caption if group_caption == "" else f"{validateTitle(group_caption)[:100]} - "
                else:
                    caption = f"{validateTitle(message.text)[:100]} - "
            else:
                caption = message.text if message.text == "" else f"{validateTitle(message.text)[:100]} - "
            # 如果是文件
            if message.document:
                for i in message.document.attributes:
                    try:
                        file_name = i.file_name
                    except:
                        continue
                if file_name == '':
                    file_name = f'{message.id} - {caption}{message.document.id}.{message.document.mime_type.split("/")[-1]}'
                elif file_name == 'video.mp4':
                    file_name = f'{message.id} - {caption}{message.document.id}.mp4'
                elif file_name == 'sticker.webp':
                    continue
                elif file_name == 'animation.gif.mp4':
                    continue
                elif file_name == 'AnimatedSticker.tgs':
                    continue
                else:
                    file_name = f'{message.id} - {caption}{file_name}'
                total = message.document.size
            elif message.photo:
                file_name = f'{message.id} - {caption}{message.photo.id}.jpg'
                total = message.photo.sizes[-1].size
            else:
                continue
            datetime_dir_name = message.date.strftime("%Y年%m月")
            # 如果文件夹不存在则创建文件夹
            file_save_path = os.path.join(save_path, dirname, datetime_dir_name)
            if not os.path.exists(file_save_path):
                os.makedirs(file_save_path)
            # 判断文件是否在本地存在
            if file_name in os.listdir(file_save_path):
                if os.path.getsize(os.path.join(file_save_path, file_name)) == total:
                    pass
                else:
                    os.remove(os.path.join(file_save_path, file_name))
                    td = tqdm_up_to(total=total,
                                    desc=f'{get_local_time()} - 正在下载: {file_name}',
                                    unit='B',
                                    unit_scale=True)
                    await message.download_media(file=os.path.join(file_save_path, file_name),
                                                 progress_callback=td.my_update)
                    td.close()
            else:
                td = tqdm_up_to(total=total,
                                desc=f'{get_local_time()} - 正在下载: {file_name}',
                                unit='B',
                                unit_scale=True)
                await message.download_media(file=os.path.join(file_save_path, file_name),
                                             progress_callback=td.my_update)
                td.close()
            cmd = ['gclone', 'move', os.path.join(file_save_path, file_name),
                   f"{drive_name}:{{{drive_id}}}/{dirname}/{datetime_dir_name}", '-P', '--stats', '1s', '--ignore-existing']
            ret = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8',
                                   universal_newlines=True,bufsize=1, errors='ignore')
            while True:
                try:
                    output = ret.stdout.readline()
                except Exception as e:
                    continue
                if output == '' and ret.poll() is not None:
                    break
                if output:
                    regex_total_size = r'Transferred:[\s]+([\d.]+\s*[kMGTP]?) / ([\d.]+[\s]?[kMGTP]?Bytes),' \
                                       r'\s*(?:\-|(\d+)\%),\s*([\d.]+\s*[kMGTP]?Bytes/s),\s*ETA\s*([\-0-9hmsdwy]+)'
                    match_total_size = re.search(regex_total_size, output)
                    if match_total_size:
                        # 已上传数据大小
                        transferred_size = match_total_size.group(1)
                        total_size = match_total_size.group(2)
                        progress = match_total_size.group(3)
                        speed = match_total_size.group(4)
                        eta = match_total_size.group(5)
                        try:
                            bar = (int(progress) // 5) * '█' + (20 - int(progress) // 5) * '░'
                        except TypeError:
                            continue
                        print(f'\r上传进度 - |{bar}{progress}% | '
                              f'{transferred_size}/{total_size} | {speed} | ETA: {eta}', end="")
            ret.stdout.close()
            ret.kill()
            if ret.returncode == 0:
                print(f'\r{get_local_time()} - {file_name} - 上传成功')
                r.hset('tg_channel_downloader', chat_title, message.id)
                if bot_token != '':
                    await bot.send_message(me.username,f'{file_name}上传成功')
            else:
                if bot_token != '':
                    await bot.send_message(me.username,f'{file_name}上传失败')
                logging.warning(f'\r{get_local_time()} - {file_name} - 上传失败 - code: {ret.returncode}')
                with open(f'{chat_title}_failed.text', 'w+') as f:
                    f.write(f'{get_local_time()} - {file_name}')


with client:
    client.loop.run_until_complete(main())
