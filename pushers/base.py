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
        格式化新闻为推送内容。
        
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
            f"⚖️ 法律日报 - {date_str} {report_type}",
            "",
            "━━━━━━━━━━━━━━━",
            "",
            "📌 热门法律事件",
            ""
        ]
        
        for i, news in enumerate(news_list, 1):
            title = news.get('title', '')
            summary = news.get('summary', '')
            source = news.get('source', '')
            url = news.get('url', '')
            
            lines.append(f"{i}️⃣ {title}")
            if summary:
                # 限制摘要长度
                if len(summary) > 100:
                    summary = summary[:100] + "..."
                lines.append(f"   {summary}")
            if source:
                lines.append(f"   来源: {source}")
            lines.append("")
        
        lines.extend([
            "━━━━━━━━━━━━━━━",
            f"共收录 {len(news_list)} 条法律资讯",
            "",
            f"更新时间: {now.strftime('%H:%M')}"
        ])
        
        return "\n".join(lines)
    
    def format_markdown(self, news_list: List[Dict], report_type: str = "早报") -> str:
        """
        格式化为Markdown格式。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
        
        Returns:
            Markdown格式内容
        """
        now = datetime.now()
        date_str = now.strftime("%Y年%m月%d日")
        
        lines = [
            f"## ⚖️ 法律日报 - {date_str} {report_type}",
            "",
            "---",
            "",
            "### 📌 热门法律事件",
            ""
        ]
        
        for i, news in enumerate(news_list, 1):
            title = news.get('title', '')
            summary = news.get('summary', '')
            source = news.get('source', '')
            url = news.get('url', '')
            
            lines.append(f"**{i}. [{title}]({url})**")
            if summary:
                if len(summary) > 100:
                    summary = summary[:100] + "..."
                lines.append(f"> {summary}")
            if source:
                lines.append(f"*来源: {source}*")
            lines.append("")
        
        lines.extend([
            "---",
            f"*共收录 {len(news_list)} 条法律资讯*",
            f"*更新时间: {now.strftime('%H:%M')}*"
        ])
        
        return "\n".join(lines)
    
    def push_news(
        self,
        news_list: List[Dict],
        report_type: str = "早报",
        use_markdown: bool = False
    ) -> Dict:
        """
        推送新闻。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
            use_markdown: 是否使用Markdown格式
        
        Returns:
            推送结果
        """
        if not news_list:
            logger.warning("新闻列表为空，跳过推送")
            return {
                'success': False,
                'message': '新闻列表为空'
            }
        
        if use_markdown:
            content = self.format_markdown(news_list, report_type)
        else:
            content = self.format_news(news_list, report_type)
        
        title = f"法律日报 - {report_type}"
        
        return self.send(content, title)