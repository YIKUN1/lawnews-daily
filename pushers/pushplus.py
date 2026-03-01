import requests
from typing import Dict
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from pushers.base import BasePusher
from utils.logger import get_logger

logger = get_logger(__name__)


class PushPlusPusher(BasePusher):
    """PushPlus推送器"""
    
    name = "pushplus"
    
    # PushPlus API
    API_URL = "http://www.pushplus.plus/send"
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.token = config.get('token', '')
        self.template = config.get('template', 'html')  # html/txt/json
        self.topic = config.get('topic', '')  # 群推送topic
    
    def send(self, content: str, title: str = "") -> Dict:
        """
        发送消息到PushPlus。
        
        Args:
            content: 消息内容
            title: 消息标题
        
        Returns:
            发送结果
        """
        if not self.token:
            logger.error("PushPlus token未配置")
            return {
                'success': False,
                'message': 'PushPlus token未配置',
                'pushed_at': datetime.now().isoformat()
            }
        
        payload = {
            'token': self.token,
            'title': title or '法律日报',
            'content': content,
            'template': self.template
        }
        
        # 如果设置了topic，进行群推送
        if self.topic:
            payload['topic'] = self.topic
        
        try:
            response = requests.post(
                self.API_URL,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('code') == 200:
                logger.info(f"PushPlus推送成功: {title}")
                return {
                    'success': True,
                    'message': '推送成功',
                    'pushed_at': datetime.now().isoformat(),
                    'content': content
                }
            else:
                logger.error(f"PushPlus推送失败: {result.get('msg', '未知错误')}")
                return {
                    'success': False,
                    'message': result.get('msg', '推送失败'),
                    'pushed_at': datetime.now().isoformat()
                }
                
        except requests.RequestException as e:
            logger.error(f"PushPlus请求失败: {e}")
            return {
                'success': False,
                'message': f'请求失败: {str(e)}',
                'pushed_at': datetime.now().isoformat()
            }
    
    def send_markdown(self, content: str, title: str = "") -> Dict:
        """
        发送Markdown格式消息。
        
        Args:
            content: Markdown内容
            title: 消息标题
        
        Returns:
            发送结果
        """
        # 临时修改template
        original_template = self.template
        self.template = 'markdown'
        result = self.send(content, title)
        self.template = original_template
        return result
