import re
from typing import Dict, List, Set
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from utils.helpers import load_keywords

logger = get_logger(__name__)


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
