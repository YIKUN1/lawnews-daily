from typing import Dict, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from crawlers.base import BaseCrawler
from utils.logger import get_logger

logger = get_logger(__name__)


class WeiboCrawler(BaseCrawler):
    """微博热搜爬虫"""
    
    source_type = "weibo"
    source_name = "微博热搜"
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取微博热搜榜。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取微博热搜，限制: {limit}")
        
        # 使用可用的API
        apis = [
            # RSSHub 微博热搜（国内镜像）
            {
                'url': 'https://rsshub.rssforever.com/weibo/search/hot/法律',
                'type': 'rss',
                'timeout': 10
            },
            # 热榜API
            {
                'url': 'https://api.vvhan.com/api/hotlist/wbHot',
                'type': 'json',
                'timeout': 10
            },
            # 今日热榜
            {
                'url': 'https://api.toutiaopro.com/weibo/hot',
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
                    logger.info(f"获取微博热搜完成，共 {len(results)} 条")
                    return results
            except Exception as e:
                logger.debug(f"API {api['url']} 失败: {e}")
                continue
        
        logger.warning("所有微博API均失败")
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
            
            # 提取来源
            source = '微博热搜'
            if ' - ' in title:
                parts = title.rsplit(' - ', 1)
                if len(parts[1]) < 15:
                    title = parts[0].strip()
            
            results.append({
                'title': title,
                'url': entry.get('link', ''),
                'summary': '',
                'source': source,
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
            title = item.get('title') or item.get('name') or item.get('keyword', '')
            if not title:
                continue
            
            url = item.get('url') or item.get('link', '')
            if not url:
                encoded_title = title.replace('#', '').replace(' ', '')
                url = f"https://s.weibo.com/weibo?q=%23{encoded_title}%23"
            
            hot = item.get('hot') or item.get('count') or item.get('hotValue', 0)
            
            results.append({
                'title': title,
                'url': url,
                'summary': '',
                'source': '微博热搜',
                'source_type': self.source_type,
                'published_at': datetime.now().isoformat(),
                'hot_score': hot if isinstance(hot, int) else 0,
                'keywords': [],
                'collected_at': datetime.now().isoformat()
            })
        
        return results
