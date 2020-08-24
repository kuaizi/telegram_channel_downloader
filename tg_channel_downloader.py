# -*- coding:utf-8 -*-
import datetime
from pyrogram import Client
import os
from tqdm import tqdm
import re
import redis  # 导入redis 模块
import subprocess
import logging

######################################## config ###############################################
filter_list = ['7z', 'rar', 'zip']              # 过滤黑名单，列表中的文件格式不下载。
save_path = 'E:\\tmp'                           # 文件保存路径 Linux 系统 一般路径格式为 '/tmp/download'
chat_id = '@example'                            # 频道名称或群组名称 可以使用 -1001198577145 类型
rclone_drive_name = 'gc'                        # rclone 配置网盘名称 
rclone_drive_id = '1234567890ABCD'              # rclone 团队盘ID
upload = False                                  # 是否上传到GD盘 默认不上传，如需上传，需要设置gclone，并把此项改为True
delete_local_file = False                       # 是否删除本地文件 默认保留，如需删除，改为True
reverse = True                                  # 默认从旧消息往新消息顺序下载
###############################################################################################
logger = logging.getLogger(__name__)
# 配置redis
pool = redis.ConnectionPool(host='localhost', port=6379, decode_responses=True)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)


class TqdmUpTo(tqdm):
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


def main():
    # 如果缓存了对话标题，就取出数据
    if r.hexists('tg_channel_downloader', chat_id):
        offset_id = int(r.hget('tg_channel_downloader', chat_id))
    else:
        # 如果 redis没有缓存对话标题，设置offset_id 为0从最新开始的下载。
        offset_id = 0
    for message in app.iter_history(chat_id=chat_id, offset_id=offset_id, reverse=reverse):
        if message.media:
            # print(message)
            # 标题
            caption = message.caption.replace(':', '：') if message.caption != None else ""
            caption = caption[:100] if len(caption) > 100 else caption[:-1]
            # 相册ID
            group_id = message.media_group_id if message.media_group_id != None else ""
            # 文件夹名
            dir_name = datetime.datetime.fromtimestamp(message.date).strftime("%Y年%m月")

            # 判断chatId类型
            if type(chat_id) == int:
                title = validateTitle(message.chat.title)
                file_save_path = os.path.join(save_path, title, dir_name)
            else:
                file_save_path = os.path.join(save_path, str(chat_id), dir_name)

            # 如果文件夹不存在则创建文件夹
            if not os.path.exists(file_save_path):
                os.makedirs(file_save_path)
            # 如果是图片
            if message.photo != None:
                file_name = f'{message.message_id}-{group_id}-{caption}.jpg'
                total = message.photo.file_size
            # 如果是视频
            elif message.video != None:
                file_name = f'{message.message_id}-{group_id}-{caption}.mp4'
                total = message.video.file_size
            # 如果是文件
            elif message.document != None:
                file_name = f'{caption}-' + message.document.file_name
                total = message.document.file_size
            else:
                # print(message.message_id, '\n')
                continue
            # 去掉文件名称中的特殊字符
            file_name = validateTitle(file_name)
            # 判断文件是否在本地存在
            if file_name in os.listdir(file_save_path):
                continue
            # 判断文件类型是否在黑名单
            elif file_name.split('.')[-1] in filter_list:
                continue
            else:
                td = TqdmUpTo(total=total, desc=f'Downloading: {file_name}', unit='B', unit_scale=True)
                message.download(file_name=os.path.join(file_save_path, file_name), progress=td.my_update)
                td.close()
                # 判断是否上传文件到Google drive
                if upload:
                    cmd = ['gclone', 'copy', os.path.join(file_save_path, file_name),
                           f'{rclone_drive_name}:{{{rclone_drive_id}}}/{chat_id}/{dir_name}', '-P']
                    # 判断是否保留本地文件
                    cmd[1] = "move" if delete_local_file else "copy"
                    ret = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf-8',
                                           universal_newlines=True)
                    tl = TqdmUpTo(total=total, desc=f'--Uploading: {file_name}', unit='B', unit_scale=True)
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
                                progress_transferred_size = match_total_size.group(1)
                                if progress_transferred_size.endswith('k'):
                                    current = progress_transferred_size * 1024
                                else:
                                    current = progress_transferred_size * 1024 * 1024
                                tl.my_update(total=total, current=current)
                    tl.close()
                    if ret.returncode == 0:
                        r.hset('tg_channel_downloader', chat_id, message.message_id)
                        # print(f'{file_name} - 上传成功')
                    else:
                        logger.warning(f'{file_name} - 上传失败 - {ret}')
                else:
                    r.hset('tg_channel_downloader', chat_id, message.message_id)


if __name__ == '__main__':
    app = Client("my_account")
    app.start()
    main()
    app.stop()
