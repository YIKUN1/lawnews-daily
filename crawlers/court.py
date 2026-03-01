import re
from typing import Dict, List
from datetime import datetime
from urllib.parse import urljoin

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from crawlers.base import BaseCrawler
from utils.logger import get_logger

logger = get_logger(__name__)


class CourtCrawler(BaseCrawler):
    """官方法律网站爬虫"""
    
    source_type = "court"
    source_name = "法院网站"
    
    # 数据源配置
    SOURCES = [
        {
            'name': '中国法院网',
            'url': 'https://www.chinacourt.org/index.shtml',
            'list_selector': 'div.list a',
            'base_url': 'https://www.chinacourt.org'
        },
        {
            'name': '最高人民法院',
            'url': 'https://www.court.gov.cn/xinshidai/index.html',
            'list_selector': 'ul.list_dd li a',
            'base_url': 'https://www.court.gov.cn'
        }
    ]
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取法院网站新闻。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取法院网站新闻，限制: {limit}")
        
        all_results = []
        
        for source in self.SOURCES:
            try:
                results = self._fetch_source(source, limit // len(self.SOURCES) + 2)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"获取 {source['name']} 失败: {e}")
                continue
        
        # 按时间排序
        all_results.sort(key=lambda x: x.get('published_at', ''), reverse=True)
        
        logger.info(f"获取法院网站新闻完成，共 {len(all_results[:limit])} 条")
        return all_results[:limit]
    
    def _fetch_source(self, source: Dict, limit: int) -> List[Dict]:
        """
        获取单个来源的新闻。
        
        Args:
            source: 来源配置
            limit: 数量限制
        
        Returns:
            新闻列表
        """
        html = self.get_html(source['url'])
        if not html:
            return []
        
        results = []
        
        # 简单的正则提取链接
        # 匹配 <a href="...">标题</a> 模式
        pattern = r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([^<]+)</a>'
        matches = re.findall(pattern, html, re.IGNORECASE)
        
        seen_urls = set()
        
        # 无效标题关键词
        invalid_keywords = [
            '登录', '注册', '更多', 'English', 'english', '返回', '首页',
            'index', 'Index', 'HOME', 'Home', 'RSS', 'XML', '手机版',
            '联系我们', '关于我们', '版权声明', '网站地图', '导航'
        ]
        
        for href, title in matches:
            title = title.strip()
            
            # 过滤无效链接和标题
            if not title or len(title) < 5:
                continue
            if href.startswith('javascript:') or href.startswith('#'):
                continue
            
            # 过滤无效关键词
            if any(kw in title for kw in invalid_keywords):
                continue
            
            # 过滤URL中包含无效路径的
            if any(x in href.lower() for x in ['index.html', 'index.shtml', '/en/', '/english']):
                continue
            
            # 构建完整URL
            if not href.startswith('http'):
                href = urljoin(source['base_url'], href)
            
            # 去重
            if href in seen_urls:
                continue
            seen_urls.add(href)
            
            news = {
                'title': title,
                'url': href,
                'summary': f"来源：{source['name']} - {title}",
                'source': source['name'],
                'source_type': self.source_type,
                'published_at': datetime.now().isoformat(),
                'hot_score': 50,  # 官方来源给予基础热度分
                'keywords': [],
                'collected_at': datetime.now().isoformat()
            }
            
            results.append(news)
            
            if len(results) >= limit:
                break
        
        return results
