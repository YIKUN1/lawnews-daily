#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
微信群列表查看工具
用于查看机器人加入的所有微信群
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from pushers.wechat_group import WechatGroupPusher

def main():
    print("=" * 50)
    print("微信群列表查看工具")
    print("=" * 50)
    print("\n即将登录微信，请使用小号扫码...\n")
    
    pusher = WechatGroupPusher({'group_names': []})
    
    # 登录并获取群列表
    chatrooms = pusher.get_chatrooms()
    
    if not chatrooms:
        print("\n未找到任何群聊")
        print("可能原因：")
        print("1. 登录失败")
        print("2. 该微信号没有加入任何群")
        return
    
    print(f"\n找到 {len(chatrooms)} 个群聊：")
    print("-" * 50)
    
    for i, chatroom in enumerate(chatrooms, 1):
        name = chatroom['name']
        count = chatroom['member_count']
        print(f"{i}. {name} ({count}人)")
    
    print("-" * 50)
    print("\n请将群名称复制到配置文件 config/config.yaml 中")
    print("配置示例：")
    print("""
push:
  method: wechat_group
  wechat_group:
    group_names:
      - "群名称1"
      - "群名称2"
""")

if __name__ == '__main__':
    main()
