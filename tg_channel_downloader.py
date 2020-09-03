# !/usr/bin/env python3
import asyncio
import difflib
import os
import re
import subprocess
import time
import redis
from telethon import TelegramClient, errors, events
from tqdm import tqdm
import logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING)
#-----------------------------------------------------------------------------------------------------------------#
api_id = 1234567                                               # 你的telegram API ID  --必填
api_hash = '141e1403**********4d525d6c54f542'                  # 你的telegram API hash -- 必填
drive_id = '0ANGBw*****GSUk9PVA'                               # 要上传到的网盘ID  如果 upload_file_set 设置为True 为必填
drive_name = 'gc'                                              # 配置文件中的网盘名称 如果 upload_file_set 设置为True 为必填
save_path = '/usr/download'                                    # 文件保存路径 -- 选填
chat = 'https://t.me/AnchorPorn'                               # 对话，可以是ID,群组名，分享链接都支持
bot_token = '1234567890:AAGZ3cbe1i***************-p63T_hiBo'   # bot_token 用于发送消息。 必填
admin_id = 888888888                                           # 你自己的telegram用户ID  可以使用@get_id_bot 找到 必填
upload_file_set = False                                        # 是否上传GD 必填， True 或者 False
maximum_seconds_per_download = 1500                            # 超时时间 可选
filter_list = ['',
               '',
               '\n']                                           #消息中的广告过滤 可选
#--------------------------------------------------------------------------------------------------------------------#



# 进度条封装
class tqdm_up_to(tqdm):
    last_block = 0

    def my_update(self, total, current):
        return self.update_to(total, current)

    def update_to(self, current, total):
        self.update(current - self.last_block)
        self.last_block = current


# 文件夹/文件名称处理
def validateTitle(title):
    r_str = r"[\/\\\:\*\?\"\<\>\|\n]"  # '/ \ : * ? " < > |'
    new_title = re.sub(r_str, "_", title)  # 替换为下划线
    return new_title


# 获取相册标题
async def get_group_caption(message):
    group_caption = ""
    entity = await client.get_entity(message.to_id)
    async for msg in client.iter_messages(entity=entity, reverse=True, offset_id=message.id - 9, limit=10):
        if msg.grouped_id == message.grouped_id:
            if msg.text != "":
                group_caption = msg.text
                return group_caption
    return group_caption


# 获取本地时间
def get_local_time():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


# 判断相似率
def get_equal_rate(str1, str2):
    return difflib.SequenceMatcher(None, str1, str2).quick_ratio()


# 返回文件大小
def bytes_to_string(byte_count):
    suffix_index = 0
    while byte_count >= 1024:
        byte_count /= 1024
        suffix_index += 1

    return '{:.2f}{}'.format(
        byte_count, [' bytes', 'KB', 'MB', 'GB', 'TB'][suffix_index]
    )


# 上传
async def upload_file(cmd, total, file_name, entity_url, message, chat_title):
    ret = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8',
                           universal_newlines=True, bufsize=1, errors='ignore')
    while True:
        try:
            output = ret.stdout.readline()
        except:
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

    text = "<b>上传{}：</b>\n" \
           "当前时间：<code>{}</code>\n" \
           "文件大小：<code>{}</code>\n" \
           "文件名称：<code>{}</code>\n\n" \
           "消息直链：<a href={}>{}</a>".format(
        '成功✅' if ret.returncode == 0 else "失败❎",
        get_local_time(),
        bytes_to_string(total),
        file_name,
        '{}/{}'.format(entity_url, message.id),
        "👉点击直达👈"
    )
    await bot.send_message(admin_id, text, parse_mode='html', link_preview=False)
    print(f'\n{get_local_time()} - {file_name} - 上传{"成功✅" if ret.returncode == 0 else "失败❎"}')
    if ret.returncode == 0:
        r.hset('tg_channel_downloader', chat_title, message.id)
    return


async def main():
    try:
        entity = await client.get_entity(chat)
        chat_title = entity.title
        if entity.username == None:
            entity_url = 'https://t.me/c/{}'.format(entity.id)
        else:
            entity_url = 'https://t.me/{}'.format(entity.username)
        if r.hexists('tg_channel_downloader', chat_title):
            offset_id = int(r.hget('tg_channel_downloader', chat_title))
        else:
            # 如果 redis没有缓存对话标题，设置offset_id 为0从最新开始的下载。
            offset_id = 0
        tqdm.write(f'{get_local_time()} - 开始下载：{chat_title}({entity.id})')
        await bot.send_message(admin_id, f'开始下载：{chat_title}({entity.id}) - {offset_id}')
        loop = asyncio.get_event_loop()
        async for message in client.iter_messages(entity=chat, reverse=True, offset_id=offset_id, limit=None):
            # 判断是否是媒体文件。包含各种文件和视频、图片。
            if message.media:
                # 如果是一组媒体
                caption = await get_group_caption(message) if (message.grouped_id and message.text == "") else message.text

                # 过滤文件名称中的广告等词语
                if len(filter_list) and caption != "":
                    for filter_keyword in filter_list:
                        caption = caption.replace(filter_keyword, "")

                # 如果文件文件名不是空字符串，则进行过滤和截取，避免文件名过长导致的错误
                caption = "" if caption == "" else f'{validateTitle(caption)} - '[:40]
                file_name = ''
                # 如果是文件
                if message.document:
                    # 如果是 贴纸
                    if message.media.document.mime_type == "image/webp":
                        continue
                    # 如果是动画贴纸
                    if message.media.document.mime_type == "application/x-tgsticker":
                        continue
                    for i in message.document.attributes:
                        try:
                            file_name = i.file_name
                        except:
                            continue
                    if file_name == '':
                        file_name = f'{message.id} - {caption}.{message.document.mime_type.split("/")[-1]}'
                    else:
                        # 如果文件名中已经包含了标题，则过滤标题
                        if get_equal_rate(caption, file_name) > 0.6:
                            caption = ""
                        file_name = f'{message.id} - {caption}{file_name}'
                    total = message.document.size
                elif message.photo:
                    file_name = f'{message.id} - {caption}{message.photo.id}.jpg'
                    total = message.photo.sizes[-1].size
                else:
                    continue
                # 主文件夹按对话标题和ID命名
                dirname = validateTitle(f'{chat_title}({entity.id})')
                # 分类文件夹按年月
                datetime_dir_name = message.date.strftime("%Y年%m月")
                # 如果文件夹不存在则创建文件夹
                file_save_path = os.path.join(save_path, dirname, datetime_dir_name)
                if not os.path.exists(file_save_path):
                    os.makedirs(file_save_path)
                # 判断文件是否在本地存在 存在则删除重新下载
                if file_name in os.listdir(file_save_path):
                    os.remove(os.path.join(file_save_path, file_name))
                td = tqdm_up_to(total=total,
                                desc=f'{get_local_time()} - 正在下载: {file_name}',
                                unit='B',
                                unit_scale=True)
                download_task = loop.create_task(message.download_media(file=os.path.join(file_save_path, file_name),
                                             progress_callback=td.my_update))
                await asyncio.wait_for(download_task, timeout=maximum_seconds_per_download)
                # await message.download_media(file=os.path.join(file_save_path, file_name),
                #                              progress_callback=td.my_update)
                td.close()
                if upload_file_set:
                    cmd = ['gclone', 'move', os.path.join(file_save_path, file_name),
                           f"{drive_name}:{{{drive_id}}}/{dirname}/{datetime_dir_name}", '-P', '--stats', '1s',
                           '--ignore-existing']
                    upload_task = loop.create_task(upload_file(cmd, total, file_name, entity_url, message, chat_title))
                    await asyncio.wait_for(upload_task, timeout=maximum_seconds_per_download)
                else:
                    r.hset('tg_channel_downloader', chat_title, message.id)
        tqdm.write('所有下载任务完成！')
        await bot.send_message(admin_id, f'{chat_title}({entity.id}) - 全部下载完毕！')
    except errors.FileReferenceExpiredError:
        await bot.send_message(admin_id, 'Error：\n由于telegram限制消息内媒体的file_reference时间为2小时，正在自动重试任务！')
        logging.warning('Error：\n由于telegram限制消息内媒体的file_reference时间为2小时，正在自动重试任务！')
        await main()


@events.register(events.NewMessage)
async def handler(update):
    try:
        if update.message.from_id == admin_id:
            if update.message.text.startswith('/start'):
                await bot.send_message(admin_id, '开启成功')
                await main()
            if update.message.text == '/ping':
                await bot.send_message(admin_id, 'peng')
            if update.message.text.startswith('/change'):
                offset_id = update.message.text.split(' ')[-1]
                entity = await client.get_entity(chat)
                chat_title = entity.title
                r.hset('tg_channel_downloader', chat_title, offset_id)
                await bot.send_message(admin_id, f'消息偏移已设置为：{offset_id}')
    except errors.FloodWaitError as f:
        await bot.send_message(admin_id, f'短时间内大量请求导致错误，需要等待 `{f.seconds}` 秒')
        logging.warning(f'短时间内大量请求导致错误，需要等待 `{f.seconds}` 秒')
    except Exception as e:
        await bot.send_message(admin_id, '出现异常：\n' + str(e))
        logging.warning(e)


if __name__ == '__main__':
    client = TelegramClient('anon', api_id, api_hash).start()
    pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
    r = redis.Redis(host='localhost', port=6379, decode_responses=True)
    bot = TelegramClient('test_bot', api_id, api_hash).start(bot_token=bot_token)

    bot.add_event_handler(handler)
    try:
        print('Successfully started (Press Ctrl+C to stop)')
        client.run_until_disconnected()
    finally:
        client.disconnect()
