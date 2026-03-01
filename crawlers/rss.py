import re
import feedparser
from typing import Dict, List
from datetime import datetime
from urllib.parse import urljoin

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from crawlers.base import BaseCrawler
from utils.logger import get_logger

logger = get_logger(__name__)


class RSSCrawler(BaseCrawler):
    """RSS源爬虫（可从国外访问）"""
    
    source_type = "rss"
    source_name = "RSS订阅"
    
    # RSS源列表（可从国外访问）
    RSS_SOURCES = [
        # 百度法律热搜 - RSSHub
        {
            'name': '百度法律热搜',
            'url': 'https://rsshub.app/baidu/hotword/法律',
            'type': 'rsshub'
        },
        # 热点新闻 - RSSHub
        {
            'name': '热点新闻',
            'url': 'https://rsshub.app/weibo/search/hot/法律',
            'type': 'rsshub'
        },
        # Google News 法律
        {
            'name': 'Google法律新闻',
            'url': 'https://news.google.com/rss/search?q=中国法律&hl=zh-CN&gl=CN&ceid=CN:zh-Hans',
            'type': 'google'
        },
    ]
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取RSS新闻。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取RSS新闻，限制: {limit}")
        
        all_results = []
        
        for source in self.RSS_SOURCES:
            try:
                results = self._fetch_rss(source, limit // len(self.RSS_SOURCES) + 3)
                all_results.extend(results)
                logger.info(f"获取 {source['name']}: {len(results)} 条")
            except Exception as e:
                logger.error(f"获取 {source['name']} 失败: {e}")
                continue
        
        # 按时间排序
        all_results.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        logger.info(f"获取RSS新闻完成，共 {len(all_results[:limit])} 条")
        return all_results[:limit]
    
    def _fetch_rss(self, source: Dict, limit: int) -> List[Dict]:
        """
        获取单个RSS源。
        
        Args:
            source: 来源配置
            limit: 数量限制
        
        Returns:
            新闻列表
        """
        try:
            feed = feedparser.parse(source['url'])
            
            if not feed.entries:
                logger.warning(f"RSS源 {source['name']} 没有条目")
                return []
            
            results = []
            for entry in feed.entries[:limit]:
                try:
                    news = self._parse_entry(entry, source)
                    if news:
                        results.append(news)
                except Exception as e:
                    logger.debug(f"解析RSS条目失败: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"解析RSS失败 {source['name']}: {e}")
            return []
    
    def _parse_entry(self, entry, source: Dict) -> Dict:
        """
        解析RSS条目。
        
        Args:
            entry: RSS条目
            source: 来源配置
        
        Returns:
            新闻字典
        """
        title = entry.get('title', '')
        if not title or len(title) < 5:
            return None
        
        # 获取链接
        url = entry.get('link', '')
        if not url:
            return None
        
        # 从标题中提取来源（格式：标题 - 来源）
        real_source = source['name']
        if ' - ' in title:
            parts = title.rsplit(' - ', 1)
            if len(parts) == 2 and len(parts[1]) < 20:  # 来源名通常较短
                title = parts[0].strip()
                real_source = parts[1].strip()
        
        # 获取摘要
        summary = ''
        if 'summary' in entry:
            summary = entry.get('summary', '')
        elif 'description' in entry:
            summary = entry.get('description', '')
        
        # 清理HTML标签
        summary = re.sub(r'<[^>]+>', '', summary)
        # 清理空白字符
        summary = re.sub(r'\s+', ' ', summary).strip()
        
        # 如果摘要无效（与标题重复、太短、以标题开头），置空让AI生成
        if summary == title or len(summary) < 10 or summary.startswith(title):
            summary = ''
        
        # 获取发布时间
        published_at = datetime.now().isoformat()
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                published_at = datetime(*entry.published_parsed[:6]).isoformat()
            except:
                pass
        
        return {
            'title': title,
            'url': url,
            'summary': summary,
            'source': real_source,  # 真实来源
            'source_type': self.source_type,
            'published_at': published_at,
            'hot_score': 30,
            'keywords': [],
            'collected_at': datetime.now().isoformat()
        }
