# -*- coding:utf-8 -*-
import time

from pyrogram import Client
import os
from tqdm import tqdm
################################### config ###############################################

save_path = 'E:\\tmp'          # 文件保存路径 Linux 系统 一般路径格式为 '/tmp/download'
channel_name = '@example'      # 频道名称或 群组数字ID 如果为数字 则不需要单引号 如 123456
offset_id = 0                  # 消息偏移量， int类型，从指定的消息ID开始遍历。
reverse = False                # 从新的消息往旧的消息遍历，如果改为True则从旧消息往后遍历

##########################################################################################

app = Client("my_account")
app.start()


class TqdmUpTo(tqdm):
    last_block = 0

    def my_update(self, total, current):
        return self.update_to(total, current)

    def update_to(self, current, total):
        self.update(current - self.last_block)
        self.last_block = current


for message in app.iter_history(chat_id=channel_name, offset_id=offset_id, reverse = reverse):
    try:
        if message.document.file_name in os.listdir(save_path):
            pass
        else:
            if message.document.file_name.endswith('.7z'): #过滤指定类型文件。
                continue
            #elif message.document.file_name.endswith('.zip'):
            #    continue
            #elif message.document.file_name.endswith('.rar'):
            #    continue
            else:
                tqdm = TqdmUpTo(total=message.document.file_size,
                                desc=f'{message.message_id} - {message.document.file_name}',
                                unit='B', unit_scale=True)
                message.download(file_name=os.path.join(save_path, message.document.file_name),
                                 progress=tqdm.my_update,
                                 block=True)
                tqdm.close()
                time.sleep(0.01)

    except Exception as e:
        continue
