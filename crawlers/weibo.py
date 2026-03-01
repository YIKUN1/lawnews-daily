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
    
    # 微博热搜API
    HOT_SEARCH_API = "https://weibo.com/ajax/side/hotSearch"
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取微博热搜榜。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取微博热搜，限制: {limit}")
        
        try:
            # 尝试获取热搜数据
            data = self.get_json(self.HOT_SEARCH_API)
            
            if not data or 'data' not in data:
                logger.warning("微博热搜API返回数据格式异常，使用备用方案")
                return self._fetch_backup(limit)
            
            hot_list = data.get('data', {}).get('realtime', [])
            
            results = []
            for item in hot_list[:limit * 2]:  # 多获取一些用于过滤
                try:
                    news = self._parse_item(item)
                    if news:
                        results.append(news)
                except Exception as e:
                    logger.debug(f"解析微博热搜条目失败: {e}")
                    continue
                
                if len(results) >= limit:
                    break
            
            logger.info(f"获取微博热搜完成，共 {len(results)} 条")
            return results
            
        except Exception as e:
            logger.error(f"获取微博热搜失败: {e}")
            return self._fetch_backup(limit)
    
    def _fetch_backup(self, limit: int) -> List[Dict]:
        """
        备用获取方案（使用公开热搜榜单）。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        # 备用API列表（按优先级）
        backup_apis = [
            "https://api.vvhan.com/api/hotlist/wbHot",
            "https://tenapi.cn/v2/weibohot",
            "https://api.oioweb.cn/api/common/weiboHotSearch"
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
                    title = item.get('title') or item.get('name') or item.get('keyword', '')
                    url = item.get('url') or item.get('link', '')
                    hot = item.get('hot') or item.get('count') or item.get('hotValue', 0)
                    
                    if not title:
                        continue
                    
                    # 如果没有URL，构建搜索链接
                    if not url:
                        encoded_title = title.replace('#', '').replace(' ', '')
                        url = f"https://s.weibo.com/weibo?q=%23{encoded_title}%23"
                    
                    news = {
                        'title': title,
                        'url': url,
                        'summary': f"微博热搜：{title}",
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
        解析热搜条目。
        
        Args:
            item: 原始数据
        
        Returns:
            标准化数据
        """
        if not item:
            return None
        
        title = item.get('word', '') or item.get('note', '')
        if not title:
            return None
        
        # 构建搜索链接
        encoded_title = title.replace('#', '').replace(' ', '')
        url = f"https://s.weibo.com/weibo?q=%23{encoded_title}%23"
        
        return {
            'title': title,
            'url': url,
            'summary': item.get('desc', '') or f"微博热搜：{title}",
            'source': self.source_name,
            'source_type': self.source_type,
            'published_at': datetime.now().isoformat(),
            'hot_score': item.get('raw_hot', 0) or item.get('num', 0),
            'keywords': [],
            'collected_at': datetime.now().isoformat()
        }
