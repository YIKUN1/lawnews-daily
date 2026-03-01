#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""微信登录测试"""

import itchat
from itchat.content import TEXT
import sys

@itchat.msg_register(TEXT)
def text_reply(msg):
    print(f"收到消息: {msg.text}")

# 登录 - 使用enableCmdQR在命令行显示二维码
print("正在登录微信，请扫码...")
try:
    itchat.auto_login(
        enableCmdQR=2,  # 在命令行显示二维码
        hotReload=False,
        statusStorageDir='data/itchat.pkl'
    )
except Exception as e:
    print(f"登录出错: {e}")
    sys.exit(1)

# 获取群列表
print("\n正在获取群列表...")
chatrooms = itchat.get_chatrooms(update=True)
print("\n" + "="*50)
print("微信群列表:")
print("="*50)
if chatrooms:
    for room in chatrooms:
        print(f"- {room['NickName']} (成员: {room.get('MemberCount', '?')}人)")
else:
    print("未找到群聊，请确保该微信号已加入群聊")

print("\n登录成功！缓存已保存。")