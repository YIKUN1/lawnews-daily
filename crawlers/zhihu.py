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
    
    # 知乎热榜API
    HOT_LIST_API = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取知乎热榜。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取知乎热榜，限制: {limit}")
        
        try:
            # 尝试获取热榜数据
            params = {
                'limit': limit * 2,
                'desktop': 'true'
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            
            data = self.get_json(self.HOT_LIST_API, params=params, headers=headers)
            
            if not data or 'data' not in data:
                logger.warning("知乎热榜API返回数据格式异常，使用备用方案")
                return self._fetch_backup(limit)
            
            hot_list = data.get('data', [])
            
            results = []
            for item in hot_list[:limit * 2]:
                try:
                    news = self._parse_item(item)
                    if news:
                        results.append(news)
                except Exception as e:
                    logger.debug(f"解析知乎热榜条目失败: {e}")
                    continue
                
                if len(results) >= limit:
                    break
            
            logger.info(f"获取知乎热榜完成，共 {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"获取知乎热榜失败: {e}")
            return self._fetch_backup(limit)
    
    def _fetch_backup(self, limit: int) -> List[Dict]:
        """
        备用获取方案。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        # 备用API列表（按优先级）
        backup_apis = [
            "https://api.vvhan.com/api/hotlist/zhihuHot",
            "https://tenapi.cn/v2/zhihuhot",
            "https://api.oioweb.cn/api/common/zhihuHotSearch"
        ]
        
        for backup_api in backup_apis:
            try:
                data = self.get_json(backup_api, timeout=10)
                
                if not data:
                    continue
                
                results = []
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
                
                for item in items[:limit * 2]:
                    # 兼容不同字段名
                    title = item.get('title') or item.get('name') or item.get('question', '')
                    url = item.get('url') or item.get('link', '')
                    hot = item.get('hot') or item.get('count') or item.get('hotValue', 0)
                    summary = item.get('desc') or item.get('excerpt') or item.get('summary', '')
                    
                    if not title:
                        continue
                    
                    # 如果没有URL，构建知乎链接
                    if not url:
                        url = f"https://www.zhihu.com/search?q={title}"
                    
                    news = {
                        'title': title,
                        'url': url,
                        'summary': summary or f"知乎热榜：{title}",
                        'source': self.source_name,
                        'source_type': self.source_type,
                        'published_at': datetime.now().isoformat(),
                        'hot_score': hot if isinstance(hot, int) else 0,
                        'keywords': [],
                        'collected_at': datetime.now().isoformat()
                    }
                    results.append(news)
                    
                    if len(results) >= limit:
                        break
                
                if results:
                    logger.info(f"使用备用API成功: {backup_api}")
                    return results
                    
            except Exception as e:
                logger.debug(f"备用API {backup_api} 失败: {e}")
                continue
        
        logger.error("所有备用API均失败")
        return []
    
    def _parse_item(self, item: Dict) -> Dict:
        """
        解析热榜条目。
        
        Args:
            item: 原始数据
        
        Returns:
            标准化数据
        """
        if not item:
            return None
        
        target = item.get('target', {}) or item
        title = target.get('title', '') or target.get('titleArea', {}).get('text', '')
        
        if not title:
            return None
        
        url = target.get('url', '') or target.get('link', {}).get('url', '')
        if url and not url.startswith('http'):
            url = f"https://www.zhihu.com{url}"
        
        # 获取摘要
        excerpt = target.get('excerpt', '') or target.get('excerptArea', {}).get('text', '')
        
        # 获取热度
        hot_score = 0
        if 'detailText' in item:
            hot_text = item.get('detailText', '')
            # 解析热度数字
            import re
            match = re.search(r'(\d+)', hot_text.replace(',', ''))
            if match:
                hot_score = int(match.group(1))
        
        return {
            'title': title,
            'url': url,
            'summary': excerpt or f"知乎热榜：{title}",
            'source': self.source_name,
            'source_type': self.source_type,
            'published_at': datetime.now().isoformat(),
            'hot_score': hot_score,
            'keywords': [],
            'collected_at': datetime.now().isoformat()
        }
