import hashlib
from typing import Dict, List, Tuple
from datetime import datetime
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class Deduplicator:
    """去重处理器"""
    
    def __init__(self, threshold: float = 0.8):
        """
        初始化去重器。
        
        Args:
            threshold: 相似度阈值，超过此值视为重复
        """
        self.threshold = threshold
        self.seen_hashes: set = set()
        self.seen_titles: List[str] = []
    
    def _get_url_hash(self, url: str) -> str:
        """计算URL哈希"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_title_hash(self, title: str) -> str:
        """计算标题哈希"""
        # 简单的字符级哈希
        return hashlib.md5(title.encode()).hexdigest()
    
    def _similarity(self, text1: str, text2: str) -> float:
        """
        计算两个文本的相似度。
        使用简单的Jaccard相似度。
        
        Args:
            text1: 文本1
            text2: 文本2
        
        Returns:
            相似度 (0-1)
        """
        if not text1 or not text2:
            return 0.0
        
        # 分词（简单按字符分割）
        set1 = set(text1)
        set2 = set(text2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def is_duplicate_url(self, url: str) -> bool:
        """
        检查URL是否重复。
        
        Args:
            url: 新闻链接
        
        Returns:
            是否重复
        """
        url_hash = self._get_url_hash(url)
        return url_hash in self.seen_hashes
    
    def is_duplicate_title(self, title: str) -> Tuple[bool, float]:
        """
        检查标题是否重复。
        
        Args:
            title: 新闻标题
        
        Returns:
            (是否重复, 最高相似度)
        """
        max_similarity = 0.0
        
        for seen_title in self.seen_titles:
            sim = self._similarity(title, seen_title)
            max_similarity = max(max_similarity, sim)
            
            if sim >= self.threshold:
                return True, sim
        
        return False, max_similarity
    
    def add_url(self, url: str) -> None:
        """添加URL到已见集合"""
        url_hash = self._get_url_hash(url)
        self.seen_hashes.add(url_hash)
    
    def add_title(self, title: str) -> None:
        """添加标题到已见列表"""
        self.seen_titles.append(title)
    
    def dedup(self, news: Dict) -> Tuple[bool, str]:
        """
        检查新闻是否重复。
        
        Args:
            news: 新闻字典
        
        Returns:
            (是否重复, 原因)
        """
        url = news.get('url', '')
        title = news.get('title', '')
        
        # URL去重
        if url and self.is_duplicate_url(url):
            return True, "URL重复"
        
        # 标题相似度去重
        is_dup, sim = self.is_duplicate_title(title)
        if is_dup:
            return True, f"标题相似度 {sim:.2%}"
        
        return False, ""
    
    def dedup_batch(
        self,
        news_list: List[Dict],
        keep_first: bool = True
    ) -> List[Dict]:
        """
        批量去重。
        
        Args:
            news_list: 新闻列表
            keep_first: 是否保留第一条（否则保留最后一条）
        
        Returns:
            去重后的新闻列表
        """
        unique = []
        duplicate_count = 0
        
        for news in news_list:
            is_dup, reason = self.dedup(news)
            
            if is_dup:
                duplicate_count += 1
                logger.debug(f"去重: {news.get('title', '')[:30]}... - {reason}")
            else:
                # 添加到已见集合
                if news.get('url'):
                    self.add_url(news['url'])
                if news.get('title'):
                    self.add_title(news['title'])
                unique.append(news)
        
        logger.info(f"去重完成: {len(news_list)} -> {len(unique)} 条 (移除 {duplicate_count} 条重复)")
        return unique
    
    def clear(self) -> None:
        """清空已见集合"""
        self.seen_hashes.clear()
        self.seen_titles.clear()
        logger.info("去重缓存已清空")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'seen_urls': len(self.seen_hashes),
            'seen_titles': len(self.seen_titles),
            'threshold': self.threshold
        }
