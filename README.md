# telegram_channel_downloader
Telegram 频道/群组 文件下载脚本

1. 安装

 - 安装依赖
 ```
 pip3 install -U pyrogram

 pip3 install tqdm
 ```
 从https://my.telegram.org/apps 获取自己的Telegram API密钥。

 - 下载脚本
 ```
 git clone https://github.com/snow922841/telegram_channel_downloader.git
 ```
2. 使用

 - 进入脚本目录

 - 修改config.ini文件内的 api_id 和 api_hash 为你自己的

 - 修改脚本内的频道名称、保存路径

 - 运行  
 ```
 python3 tg_channel_downloader.py
 ```
 - 按照提示输入telegram绑定的手机号获取验证码并输入 
