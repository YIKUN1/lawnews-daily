import re
from typing import Dict, List, Set
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.helpers import load_keywords

logger = get_logger(__name__)


# 非新闻标题黑名单
NON_NEWS_PATTERNS = [
    r'^[\s\d]+$',  # 纯数字/空白
    r'公告网$',  # 网站名
    r'^网站$',  # 纯"网站"
    r'^登录',
    r'^注册',
    r'^首页$',
    r'^返回$',
    r'^更多$',
    r'^列表$',
    r'^详情$',
    r'^下载$',
    r'^联系我们',
    r'^版权所有',
    r'^\d{4}年\d{1,2}月\d{1,2}日$',  # 纯日期
]

# 非新闻关键词
NON_NEWS_KEYWORDS = [
    '公告网', '新闻网', '法院网', '检察院网',
    '版权所有', '技术支持', '联系我们',
    'ICP备', '京公网安备',
]


class KeywordFilter:
    """关键词过滤器"""
    
    def __init__(self, keywords: List[str] = None, keywords_path: str = None):
        """
        初始化关键词过滤器。
        
        Args:
            keywords: 关键词列表
            keywords_path: 关键词文件路径
        """
        if keywords:
            self.keywords = set(keywords)
        elif keywords_path:
            self.keywords = set(load_keywords(keywords_path))
        else:
            self.keywords = set(load_keywords())
        
        logger.info(f"加载关键词 {len(self.keywords)} 个")
    
    def match(self, text: str) -> List[str]:
        """
        检查文本是否包含关键词。
        
        Args:
            text: 待检查文本
        
        Returns:
            匹配的关键词列表
        """
        if not text:
            return []
        
        matched = []
        text_lower = text.lower()
        
        for keyword in self.keywords:
            if keyword.lower() in text_lower:
                matched.append(keyword)
        
        return matched
    
    def filter_news(self, news: Dict, min_matches: int = 1) -> bool:
        """
        检查新闻是否通过关键词过滤。
        
        Args:
            news: 新闻字典
            min_matches: 最少匹配关键词数量
        
        Returns:
            是否通过过滤
        """
        # 合并标题和摘要进行匹配
        text = f"{news.get('title', '')} {news.get('summary', '')}"
        matched_keywords = self.match(text)
        
        # 更新新闻的关键词列表
        news['keywords'] = matched_keywords
        
        return len(matched_keywords) >= min_matches
    
    def filter_batch(self, news_list: List[Dict], min_matches: int = 1) -> List[Dict]:
        """
        批量过滤新闻。
        
        Args:
            news_list: 新闻列表
            min_matches: 最少匹配关键词数量
        
        Returns:
            过滤后的新闻列表
        """
        filtered = []
        for news in news_list:
            if self.filter_news(news, min_matches):
                filtered.append(news)
        
        logger.info(f"关键词过滤: {len(news_list)} -> {len(filtered)} 条")
        return filtered
    
    def add_keywords(self, keywords: List[str]) -> None:
        """
        添加关键词。
        
        Args:
            keywords: 关键词列表
        """
        self.keywords.update(keywords)
    
    def remove_keywords(self, keywords: List[str]) -> None:
        """
        移除关键词。
        
        Args:
            keywords: 关键词列表
        """
        self.keywords.difference_update(keywords)
    
    def get_keywords(self) -> List[str]:
        """获取所有关键词"""
        return list(self.keywords)


class QualityFilter:
    """质量过滤器"""
    
    @staticmethod
    def is_valid_news(news: Dict) -> bool:
        """
        检查是否是有效的新闻条目。
        
        Args:
            news: 新闻字典
        
        Returns:
            是否有效
        """
        title = news.get('title', '').strip()
        
        # 标题太短
        if len(title) < 8:
            return False
        
        # 标题太长（可能是错误内容）
        if len(title) > 100:
            return False
        
        # 检查黑名单模式
        for pattern in NON_NEWS_PATTERNS:
            if re.match(pattern, title):
                return False
        
        # 检查非新闻关键词
        for keyword in NON_NEWS_KEYWORDS:
            if keyword in title:
                return False
        
        return True
    
    @staticmethod
    def filter_batch(news_list: List[Dict]) -> List[Dict]:
        """
        批量过滤非新闻内容。
        
        Args:
            news_list: 新闻列表
        
        Returns:
            过滤后的新闻列表
        """
        filtered = [news for news in news_list if QualityFilter.is_valid_news(news)]
        logger.info(f"质量过滤: {len(news_list)} -> {len(filtered)} 条")
        return filtered
