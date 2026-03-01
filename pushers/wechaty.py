from typing import Dict, List
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from pushers.base import BasePusher
from utils.logger import get_logger

logger = get_logger(__name__)


class WechatyPusher(BasePusher):
    """Wechaty推送器（个人微信机器人）"""
    
    name = "wechaty"
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.puppet = config.get('puppet', 'wechaty-puppet-wechat')
        self.room_ids = config.get('room_ids', [])
        self._bot = None
    
    def _init_bot(self):
        """初始化Wechaty机器人"""
        try:
            from wechaty import Wechaty
            
            if self._bot is None:
                self._bot = Wechaty()
            
            return self._bot
        except ImportError:
            logger.warning("wechaty未安装，请参考: https://github.com/wechaty/python-wechaty")
            return None
    
    def send(self, content: str, title: str = "") -> Dict:
        """
        发送消息（需要先启动机器人）。
        
        注意：Wechaty需要异步运行，此方法主要用于模拟。
        实际使用需要配合asyncio运行机器人。
        
        Args:
            content: 消息内容
            title: 消息标题
        
        Returns:
            发送结果
        """
        bot = self._init_bot()
        
        if bot is None:
            logger.warning("Wechaty机器人未初始化")
            return {
                'success': False,
                'message': 'Wechaty未安装或未初始化',
                'pushed_at': datetime.now().isoformat()
            }
        
        if not self.room_ids:
            logger.warning("未配置群ID")
            return {
                'success': False,
                'message': '未配置群ID',
                'pushed_at': datetime.now().isoformat()
            }
        
        # Wechaty需要异步操作，这里返回提示
        logger.info("Wechaty推送需要异步运行，请使用 send_async 方法")
        return {
            'success': False,
            'message': '请使用 send_async 方法进行异步推送',
            'pushed_at': datetime.now().isoformat()
        }
    
    async def send_async(self, content: str, title: str = "") -> Dict:
        """
        异步发送消息。
        
        Args:
            content: 消息内容
            title: 消息标题
        
        Returns:
            发送结果
        """
        bot = self._init_bot()
        
        if bot is None:
            return {
                'success': False,
                'message': 'Wechaty未安装'
            }
        
        try:
            from wechaty_puppet import FileBox
            
            # 构建完整消息
            full_content = f"## {title}\n\n{content}" if title else content
            
            success_count = 0
            
            for room_id in self.room_ids:
                try:
                    room = await bot.Room.find(room_id)
                    if room:
                        await room.say(full_content)
                        success_count += 1
                        logger.info(f"已发送到群: {room_id}")
                except Exception as e:
                    logger.error(f"发送到群 {room_id} 失败: {e}")
            
            return {
                'success': success_count > 0,
                'message': f'成功发送到 {success_count}/{len(self.room_ids)} 个群',
                'pushed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Wechaty发送失败: {e}")
            return {
                'success': False,
                'message': str(e),
                'pushed_at': datetime.now().isoformat()
            }
    
    async def push_news_async(
        self,
        news_list: List[Dict],
        report_type: str = "早报"
    ) -> Dict:
        """
        异步推送新闻。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
        
        Returns:
            推送结果
        """
        if not news_list:
            return {
                'success': False,
                'message': '新闻列表为空'
            }
        
        content = self.format_news(news_list, report_type)
        title = f"法律日报 - {report_type}"
        
        return await self.send_async(content, title)
