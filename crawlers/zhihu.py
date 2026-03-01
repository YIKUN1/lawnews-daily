from typing import Dict, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from crawlers.base import BaseCrawler
from utils.logger import get_logger

logger = get_logger(__name__)


class ZhihuCrawler(BaseCrawler):
    """知乎热榜爬虫"""
    
    source_type = "zhihu"
    source_name = "知乎热榜"
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取知乎热榜。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取知乎热榜，限制: {limit}")
        
        # 使用可用的API
        apis = [
            # RSSHub 知乎热榜（国内镜像）
            {
                'url': 'https://rsshub.rssforever.com/zhihu/hotlist',
                'type': 'rss',
                'timeout': 10
            },
            # 热榜API
            {
                'url': 'https://api.vvhan.com/api/hotlist/zhihuHot',
                'type': 'json',
                'timeout': 10
            },
        ]
        
        for api in apis:
            try:
                if api['type'] == 'rss':
                    results = self._fetch_rss(api, limit)
                else:
                    results = self._fetch_json(api, limit)
                
                if results:
                    logger.info(f"获取知乎热榜完成，共 {len(results)} 条")
                    return results
            except Exception as e:
                logger.debug(f"API {api['url']} 失败: {e}")
                continue
        
        logger.warning("所有知乎API均失败")
        return []
    
    def _fetch_rss(self, api: Dict, limit: int) -> List[Dict]:
        """通过RSS获取"""
        import feedparser
        
        response = self.get(api['url'], timeout=api.get('timeout', 10))
        if not response:
            return []
        
        feed = feedparser.parse(response.text)
        if not feed.entries:
            return []
        
        results = []
        for entry in feed.entries[:limit]:
            title = entry.get('title', '')
            if not title:
                continue
            
            results.append({
                'title': title,
                'url': entry.get('link', ''),
                'summary': '',
                'source': '知乎热榜',
                'source_type': self.source_type,
                'published_at': datetime.now().isoformat(),
                'hot_score': 50,
                'keywords': [],
                'collected_at': datetime.now().isoformat()
            })
        
        return results
    
    def _fetch_json(self, api: Dict, limit: int) -> List[Dict]:
        """通过JSON API获取"""
        data = self.get_json(api['url'], timeout=api.get('timeout', 10))
        
        if not data:
            return []
        
        items = []
        # 兼容不同API格式
        if data.get('success') and data.get('data'):
            items = data.get('data', [])
        elif data.get('code') == 200 and data.get('data'):
            items = data.get('data', [])
        elif isinstance(data.get('data'), list):
            items = data.get('data', [])
        elif isinstance(data, list):
            items = data
        
        results = []
        for item in items[:limit]:
            title = item.get('title') or item.get('name') or item.get('question', '')
            if not title:
                continue
            
            url = item.get('url') or item.get('link', '')
            if not url:
                url = f"https://www.zhihu.com/search?q={title}"
            
            hot = item.get('hot') or item.get('count') or item.get('hotValue', 0)
            summary = item.get('desc') or item.get('excerpt') or item.get('summary', '')
            
            results.append({
                'title': title,
                'url': url,
                'summary': summary,
                'source': '知乎热榜',
                'source_type': self.source_type,
                'published_at': datetime.now().isoformat(),
                'hot_score': hot if isinstance(hot, int) else 0,
                'keywords': [],
                'collected_at': datetime.now().isoformat()
            })
        
        return results
