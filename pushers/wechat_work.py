import requests
from typing import Dict, List
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from pushers.base import BasePusher
from utils.logger import get_logger

logger = get_logger(__name__)


class WeChatWorkPusher(BasePusher):
    """企业微信机器人推送器"""
    
    name = "wechat_work"
    
    def __init__(self, config: Dict):
        super().__init__(config)
        self.webhook = config.get('webhook', '')
    
    def send(self, content: str, title: str = "") -> Dict:
        """
        发送消息到企业微信群。
        
        Args:
            content: 消息内容
            title: 消息标题
        
        Returns:
            发送结果
        """
        if not self.webhook:
            logger.error("企业微信Webhook未配置")
            return {
                'success': False,
                'message': '企业微信Webhook未配置',
                'pushed_at': datetime.now().isoformat()
            }
        
        # 构建Markdown消息
        markdown_content = content
        if title:
            markdown_content = f"## {title}\n\n{content}"
        
        payload = {
            "msgtype": "markdown",
            "markdown": {
                "content": markdown_content
            }
        }
        
        try:
            response = requests.post(
                self.webhook,
                json=payload,
                timeout=30
            )
            
            result = response.json()
            
            if result.get('errcode') == 0:
                logger.info(f"企业微信推送成功: {title}")
                return {
                    'success': True,
                    'message': '推送成功',
                    'pushed_at': datetime.now().isoformat(),
                    'content': content
                }
            else:
                logger.error(f"企业微信推送失败: {result.get('errmsg', '未知错误')}")
                return {
                    'success': False,
                    'message': result.get('errmsg', '推送失败'),
                    'pushed_at': datetime.now().isoformat()
                }
                
        except requests.RequestException as e:
            logger.error(f"企业微信请求失败: {e}")
            return {
                'success': False,
                'message': f'请求失败: {str(e)}',
                'pushed_at': datetime.now().isoformat()
            }
    
    def send_text(self, content: str, mentioned_list: List[str] = None) -> Dict:
        """
        发送文本消息。
        
        Args:
            content: 文本内容
            mentioned_list: @成员列表
        
        Returns:
            发送结果
        """
        if not self.webhook:
            return {
                'success': False,
                'message': '企业微信Webhook未配置'
            }
        
        payload = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        if mentioned_list:
            payload["text"]["mentioned_list"] = mentioned_list
        
        try:
            response = requests.post(self.webhook, json=payload, timeout=30)
            result = response.json()
            
            return {
                'success': result.get('errcode') == 0,
                'message': result.get('errmsg', ''),
                'pushed_at': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }
    
    def push_news(
        self,
        news_list: List[Dict],
        report_type: str = "早报",
        use_markdown: bool = True
    ) -> Dict:
        """
        推送新闻（企业微信默认使用Markdown格式）。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
            use_markdown: 是否使用Markdown格式
        
        Returns:
            推送结果
        """
        return super().push_news(news_list, report_type, use_markdown=True)
