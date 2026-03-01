#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Wechaty微信群推送器"""

import asyncio
import os
from typing import List, Dict, Optional
from datetime import datetime

from wechaty import Wechaty, Room, Message, FileBox
from wechaty_puppet import ScanEvent

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from pushers.base import BasePusher
from utils.logger import get_logger

logger = get_logger(__name__)


class WechatyPusher(BasePusher):
    """Wechaty微信群推送器（iPad协议）"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.token = config.get('token', os.environ.get('WECHATY_PUPPET_SERVICE_TOKEN'))
        self.room_names = config.get('room_names', [])  # 要推送的群名称列表
        self.bot = None
        self._ready = False
        self._rooms_cache = []
    
    async def init_bot(self):
        """初始化机器人"""
        if not self.token:
            raise ValueError("请配置 WECHATY_PUPPET_SERVICE_TOKEN 或在config.yaml中设置token")
        
        os.environ['WECHATY_PUPPET_SERVICE_TOKEN'] = self.token
        
        self.bot = Wechaty()
        
        @self.bot.on('scan')
        async def on_scan(payload: ScanEvent):
            """扫码登录"""
            qrcode_url = f"https://wechaty.js.org/qrcode/{payload.qrcode}"
            logger.info(f"请扫码登录: {qrcode_url}")
            # 生成二维码图片
            try:
                import qrcode
                qr = qrcode.QRCode()
                qr.add_data(qrcode_url)
                qr.make(fit=True)
                qr.print_ascii(invert=True)
            except:
                pass
        
        @self.bot.on('login')
        async def on_login(user):
            """登录成功"""
            logger.info(f"登录成功: {user}")
            self._ready = True
            # 获取所有群
            rooms = await self.bot.Room.find_all()
            self._rooms_cache = rooms
            logger.info(f"获取到 {len(rooms)} 个群聊")
        
        @self.bot.on('logout')
        async def on_logout(user):
            """登出"""
            logger.info(f"已登出: {user}")
            self._ready = False
    
    async def send_to_rooms(self, message: str) -> bool:
        """发送消息到指定群"""
        if not self._ready or not self._rooms_cache:
            logger.error("机器人未就绪，请先登录")
            return False
        
        sent_count = 0
        for room in self._rooms_cache:
            try:
                topic = await room.topic()
                if not self.room_names or topic in self.room_names:
                    await room.say(message)
                    logger.info(f"已发送到群: {topic}")
                    sent_count += 1
            except Exception as e:
                logger.error(f"发送到群失败: {e}")
        
        return sent_count > 0
    
    def push(self, title: str, content: str, items: List[Dict] = None) -> bool:
        """推送消息（同步接口）"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self._push_async(title, content, items))
    
    async def _push_async(self, title: str, content: str, items: List[Dict] = None) -> bool:
        """异步推送"""
        if not self.bot:
            await self.init_bot()
        
        # 构建消息
        message = self._format_message(title, content, items)
        
        return await self.send_to_rooms(message)
    
    def _format_message(self, title: str, content: str, items: List[Dict] = None) -> str:
        """格式化消息"""
        lines = [f"📋 {title}", ""]
        
        if items:
            for i, item in enumerate(items, 1):
                title_text = item.get('title', '')[:50]
                summary = item.get('summary', '')[:100]
                url = item.get('url', '')
                
                lines.append(f"{i}. {title_text}")
                if summary:
                    lines.append(f"   {summary}...")
                if url:
                    lines.append(f"   🔗 {url}")
                lines.append("")
        
        lines.append(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append("📊 法律日报 - 自动推送")
        
        return "\n".join(lines)
    
    async def list_rooms(self) -> List[str]:
        """列出所有群"""
        if not self.bot:
            await self.init_bot()
            # 等待登录
            import asyncio
            for _ in range(30):
                if self._ready:
                    break
                await asyncio.sleep(1)
        
        rooms = []
        for room in self._rooms_cache:
            try:
                topic = await room.topic()
                rooms.append(topic)
            except:
                pass
        return rooms


async def main():
    """测试入口"""
    import sys
    
    token = os.environ.get('WECHATY_PUPPET_SERVICE_TOKEN')
    if not token:
        print("请设置环境变量 WECHATY_PUPPET_SERVICE_TOKEN")
        print("或访问 https://wechaty.js.org/docs/puppet-services/ 购买token")
        sys.exit(1)
    
    pusher = WechatyPusher({'token': token})
    
    if len(sys.argv) > 1 and sys.argv[1] == '--list':
        # 列出群
        rooms = await pusher.list_rooms()
        print("\n群列表:")
        for room in rooms:
            print(f"  - {room}")
    else:
        # 测试推送
        await pusher.init_bot()
        while not pusher._ready:
            await asyncio.sleep(1)
        
        # 获取群列表
        rooms = await pusher.list_rooms()
        print(f"\n找到 {len(rooms)} 个群")
        
        # 发送测试消息
        test_msg = f"测试消息 - {datetime.now()}"
        result = await pusher.send_to_rooms(test_msg)
        print(f"发送结果: {'成功' if result else '失败'}")


if __name__ == '__main__':
    asyncio.run(main())
