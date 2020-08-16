# -*- coding:utf-8 -*-
import datetime
from pyrogram import Client
import os, re
from tqdm import tqdm
################################### config ###############################################
black_list = ['7z', 'rar', 'zip']               # 过滤黑名单，列表中的文件格式不下载。
save_path = f'E:\\tmp\\{channel_name}'          # 文件保存路径 Linux 系统 一般路径格式为 '/tmp/download'
chat_id = '@example'                            # 频道名称或群组名称
offset_id = 0                                   # 消息偏移量， int类型，从指定的消息ID开始遍历。
reverse = False                                 # 从新的消息往旧的消息遍历，如果改为True则从旧消息往后遍历
limit = 0                                       # 限制返回消息数量
##########################################################################################



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
    for message in app.iter_history(chat_id=chat_id, offset_id=offset_id, reverse=reverse, limit=limit):
        if message.media:
            # print(message)
            # 标题
            caption = message.caption.replace(':', '：') if message.caption != None else ""

            # 相册ID
            group_id = message.media_group_id if message.media_group_id != None else ""

            # 文件夹名
            dir_name = datetime.datetime.fromtimestamp(message.date).strftime("%Y年%m月")
            file_save_path = os.path.join(save_path, dir_name)

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

            file_name = validateTitle(file_name)  # 去掉文件名称中的特殊字符

            if file_name in os.listdir(file_save_path):
                continue
            elif file_name.split('.')[-1] in black_list:
                continue
            else:
                t = TqdmUpTo(total=total, desc=file_name, unit='B', unit_scale=True)
                message.download(file_name=os.path.join(file_save_path, file_name), progress=t.my_update)
                t.close()

if __name__ == '__main__':
    app = Client("my_account")
    app.start()
    # chat_id = "@MRHXPJ"
    # chat_id = "@mengxinsetu" -5506
    # chat_id =   "@ONEPIECETHKyoto" # - 69985
    # chat_id = '@okjfresh' # 6850
    main()
