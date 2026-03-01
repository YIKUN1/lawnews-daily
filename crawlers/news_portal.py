from typing import Dict, List
from datetime import datetime
import xml.etree.ElementTree as ET

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from crawlers.base import BaseCrawler
from utils.logger import get_logger

logger = get_logger(__name__)


class NewsPortalCrawler(BaseCrawler):
    """新闻门户爬虫"""
    
    source_type = "news_portal"
    source_name = "新闻门户"
    
    # RSS源配置
    RSS_SOURCES = [
        {
            'name': '新浪法治',
            'url': 'https://news.sina.com.cn/rss/law.xml',
        },
        {
            'name': '网易法律',
            'url': 'https://news.163.com/special/0001120H/news_law.xml',
        }
    ]
    
    # 备用API
    BACKUP_API = "https://api.vvhan.com/api/hotlist/news"
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取新闻门户法律资讯。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取新闻门户资讯，限制: {limit}")
        
        all_results = []
        
        # 尝试RSS源
        for source in self.RSS_SOURCES:
            try:
                results = self._fetch_rss(source, limit // len(self.RSS_SOURCES) + 2)
                all_results.extend(results)
            except Exception as e:
                logger.debug(f"获取 {source['name']} RSS失败: {e}")
                continue
        
        # 如果RSS获取失败，使用备用API
        if not all_results:
            logger.info("RSS获取失败，使用备用API")
            all_results = self._fetch_backup(limit)
        
        logger.info(f"获取新闻门户资讯完成，共 {len(all_results[:limit])} 条")
        return all_results[:limit]
    
    def _fetch_rss(self, source: Dict, limit: int) -> List[Dict]:
        """
        获取RSS源。
        
        Args:
            source: 来源配置
            limit: 数量限制
        
        Returns:
            新闻列表
        """
        response = self.request(source['url'])
        if not response:
            return []
        
        results = []
        
        try:
            # 解析XML
            root = ET.fromstring(response.text)
            
            # 查找所有item
            for item in root.iter('item'):
                title = self._get_element_text(item, 'title')
                link = self._get_element_text(item, 'link')
                description = self._get_element_text(item, 'description')
                pub_date = self._get_element_text(item, 'pubDate')
                
                if not title or not link:
                    continue
                
                news = {
                    'title': title,
                    'url': link,
                    'summary': description or title,
                    'source': source['name'],
                    'source_type': self.source_type,
                    'published_at': pub_date or datetime.now().isoformat(),
                    'hot_score': 30,  # 新闻门户基础热度
                    'keywords': [],
                    'collected_at': datetime.now().isoformat()
                }
                
                results.append(news)
                
                if len(results) >= limit:
                    break
            
        except ET.ParseError as e:
            logger.error(f"RSS解析失败: {source['name']}, 错误: {e}")
        
        return results
    
    def _fetch_backup(self, limit: int) -> List[Dict]:
        """
        备用获取方案。
        
        Args:
            limit: 数量限制
        
        Returns:
            新闻列表
        """
        try:
            data = self.get_json(self.BACKUP_API)
            
            if not data or not data.get('success'):
                return []
            
            results = []
            for item in data.get('data', [])[:limit]:
                news = {
                    'title': item.get('title', ''),
                    'url': item.get('url', ''),
                    'summary': item.get('desc', ''),
                    'source': '新闻热榜',
                    'source_type': self.source_type,
                    'published_at': datetime.now().isoformat(),
                    'hot_score': item.get('hot', 0),
                    'keywords': [],
                    'collected_at': datetime.now().isoformat()
                }
                results.append(news)
            
            return results
            
        except Exception as e:
            logger.error(f"备用API获取失败: {e}")
            return []
    
    def _get_element_text(self, parent: ET.Element, tag: str) -> str:
        """
        获取元素文本。
        
        Args:
            parent: 父元素
            tag: 标签名
        
        Returns:
            文本内容
        """
        element = parent.find(tag)
        if element is not None and element.text:
            return element.text.strip()
        return ''
