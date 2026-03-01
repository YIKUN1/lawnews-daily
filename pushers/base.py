from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class BasePusher(ABC):
    """推送器基类"""
    
    # 推送方式名称
    name: str = "base"
    
    def __init__(self, config: Dict):
        """
        初始化推送器。
        
        Args:
            config: 配置字典
        """
        self.config = config
    
    @abstractmethod
    def send(self, content: str, title: str = "") -> Dict:
        """
        发送消息。
        
        Args:
            content: 消息内容
            title: 消息标题
        
        Returns:
            发送结果
        """
        pass
    
    def format_news(self, news_list: List[Dict], report_type: str = "早报") -> str:
        """
        格式化新闻为推送内容（纯文本）。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型（早报/晚报）
        
        Returns:
            格式化后的内容
        """
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        
        # 构建内容
        lines = [
            f"⚖️ 法律日报 · {date_str} {report_type}",
            ""
        ]
        
        for i, news in enumerate(news_list, 1):
            title = news.get('title', '')
            summary = news.get('summary', '')
            source = news.get('source', '')
            
            # 标题
            lines.append(f"【{i}】{title}")
            
            # 摘要（如果有有效内容）
            if summary and len(summary) > 10:
                lines.append(f"    {summary}")
            
            # 来源（如果有）
            if source and source not in ['Google法律新闻', 'RSS订阅', '百度法律热搜']:
                lines.append(f"    📰 {source}")
            
            lines.append("")
        
        lines.extend([
            "━━━━━━━━━━━━━━━",
            f"📅 {now.strftime('%Y-%m-%d %H:%M')}",
            "",
            "信息整理：王德林律师",
            "个人名片：#小程序://滇才翼/8IOhdnFbszBqodl"
        ])
        
        return "\n".join(lines)
    
    def format_html(self, news_list: List[Dict], report_type: str = "早报") -> str:
        """
        格式化为HTML格式（支持链接点击）。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
        
        Returns:
            HTML格式内容
        """
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        
        lines = [
            f"<h2>⚖️ 法律日报 · {date_str} {report_type}</h2>",
            "<hr/>",
            "<ol>"
        ]
        
        for news in news_list:
            title = news.get('title', '')
            summary = news.get('summary', '')
            source = news.get('source', '')
            url = news.get('url', '')
            
            # 标题带链接
            if url:
                lines.append(f"<li><a href=\"{url}\"><b>{title}</b></a></li>")
            else:
                lines.append(f"<li><b>{title}</b></li>")
            
            # 摘要
            if summary and len(summary) > 10:
                lines.append(f"<p style=\"color:#666;font-size:14px;\">{summary}</p>")
            
            # 来源
            if source and source not in ['Google法律新闻', 'RSS订阅', '百度法律热搜']:
                lines.append(f"<p style=\"color:#999;font-size:12px;\">📰 {source}</p>")
        
        lines.extend([
            "</ol>",
            "<hr/>",
            f"<p style=\"color:#999;font-size:12px;\">📅 {now.strftime('%Y-%m-%d %H:%M')}</p>",
            "<br/>",
            "<p>信息整理：王德林律师</p>",
            "<p>个人名片：#小程序://滇才翼/8IOhdnFbszBqodl</p>"
        ])
        
        return "\n".join(lines)
    
    def push_news(
        self,
        news_list: List[Dict],
        report_type: str = "早报",
        use_html: bool = True
    ) -> Dict:
        """
        推送新闻。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
            use_html: 是否使用HTML格式（支持链接点击）
        
        Returns:
            推送结果
        """
        if not news_list:
            logger.warning("新闻列表为空，跳过推送")
            return {
                'success': False,
                'message': '新闻列表为空'
            }
        
        if use_html:
            content = self.format_html(news_list, report_type)
        else:
            content = self.format_news(news_list, report_type)
        
        title = f"法律日报 - {report_type}"
        
        return self.send(content, title)