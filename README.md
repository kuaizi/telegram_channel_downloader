# telegram_channel_downloader
Telegram 频道/群组 文件下载脚本

脚本需要python3环境，具体安装教程自行搜索。

测试环境  Ubuntu 18.04.5 LTS & Python 3.6.9

目前脚本能够进行工作，但是还是有很多bug需要解决
所以希望大家使用过后填写一下这个调查问卷，方便找到合适的VPS区域和配置，加快下载速度
[问卷地址](https://forms.gle/8q91pqrS3WEZwBL69)

**1. 前提**
 
 - 安装redis
 
   安装教程参考 [Redis 安装 | 菜鸟教程](https://www.runoob.com/redis/redis-install.html)
 
 
 - 从 https://my.telegram.org/apps 获取自己的Telegram API密钥。

 - 下载脚本
 ```
 git clone https://github.com/snow922841/telegram_channel_downloader.git
 ```

**2. 使用**

 - 进入脚本目录
 ```
 cd telegram_channel_downloader
 ```
 - 安装依赖 
 
 ```
 pip3 install -r requirements.txt
 ```

 - 修改telegram_channel_downloader.py文件内的 api_id 和 api_hash 为你自己的

 - 修改脚本内的频道名称、保存路径、 bot_token 、 admin_id 、 chat 等必填配置
 
 - 鉴于网友需要上传GD，特添加了使用gclone自动上传到团队盘的功能，需要在配置区域设置。具体查看脚本内注释
   
 - 运行  
 ```
 python3 tg_channel_downloader.py
 ```
 - 按照提示输入telegram绑定的手机号获取验证码并输入
 
 - 配置完成后需要给bot发送 /start 才会正式开始运行脚本，否则无法启动
 
 - 给bot发送 /ping 如果回复 peng 表示脚本正在运行，但是是否在下载还需要自己判断
 
 - 如果30分钟内未收到bot发送的下载消息可能脚本未下载或下载完成，可以重新发送 /start 继续下载 （待优化）
 
 - 可以手动配置消息偏移 给bot 发送 ‘ /change 123 ’ 代表从第123条消息开始下载，请自行修改数字。
 
 - 异步请求会受到telegram的限制，而且任务失败在redis缓存比较麻烦，等有办法解决后在提交代码

<details>
  <summary>点击查看更新日志</summary>
    
  2020-09-01更新
  
   - 使用bot启动，并使脚本持久化，
   
   - 优化代码
   
   - 修复一些bug
  
  2020-08-29更新
  
   - 更换telegram的第三方库
  
   - 默认上传到GD，目前未配置不上传，所以需要安装gclone
  
   - 默认过滤贴纸、动态贴纸、gif格式文件
  
   - 优化了下载和上传进度条的显示
  
   - 上传失败后会把消息ID保存在脚本所在的文件夹，方便以后可以手动下载
  
  2020-08-19更新
     
   - 添加自动上传到Googledrive的功能
     
   - 使用redis缓存已经遍历的消息ID
 
</details>
