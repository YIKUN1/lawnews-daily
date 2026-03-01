from typing import Dict, List
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from crawlers.base import BaseCrawler
from utils.logger import get_logger

logger = get_logger(__name__)


class WeChatMPCrawler(BaseCrawler):
    """微信公众号爬虫（通过RSSHub）"""
    
    source_type = "wechat_mp"
    source_name = "微信公众号"
    
    # RSSHub地址（需要自行部署或使用公共服务）
    RSSHUB_BASE = "https://rsshub.app"
    
    # 法律相关公众号
    ACCOUNTS = [
        '最高人民法院',      # 需要配置RSSHub的biz参数
        '中国法院网',
        '法治日报',
    ]
    
    def __init__(self, config: Dict):
        super().__init__(config)
        # 可配置RSSHub地址
        self.rsshub_base = config.get('rsshub_base', self.RSSHUB_BASE)
        # 公众号配置（需要biz参数）
        self.accounts = config.get('accounts', [])
    
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取微信公众号文章。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            新闻列表
        """
        logger.info(f"开始获取微信公众号文章，限制: {limit}")
        
        # 如果没有配置公众号，返回提示
        if not self.accounts:
            logger.warning("未配置微信公众号账号，跳过获取")
            logger.info("提示：需要在配置中设置公众号biz参数才能获取文章")
            return []
        
        all_results = []
        
        for account in self.accounts:
            try:
                results = self._fetch_account(account, limit // len(self.accounts) + 2)
                all_results.extend(results)
            except Exception as e:
                logger.error(f"获取公众号 {account.get('name', 'unknown')} 失败: {e}")
                continue
        
        logger.info(f"获取微信公众号文章完成，共 {len(all_results[:limit])} 条")
        return all_results[:limit]
    
    def _fetch_account(self, account: Dict, limit: int) -> List[Dict]:
        """
        获取单个公众号的文章。
        
        Args:
            account: 公众号配置（包含name和biz）
            limit: 数量限制
        
        Returns:
            新闻列表
        """
        import xml.etree.ElementTree as ET
        
        biz = account.get('biz', '')
        name = account.get('name', '')
        
        if not biz:
            logger.warning(f"公众号 {name} 未配置biz参数")
            return []
        
        # 构建RSSHub URL
        rss_url = f"{self.rsshub_base}/wechat/mp/msgalbum/{biz}"
        
        response = self.request(rss_url)
        if not response:
            return []
        
        results = []
        
        try:
            root = ET.fromstring(response.text)
            
            for item in root.iter('item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pub_date_elem = item.find('pubDate')
                
                title = title_elem.text if title_elem is not None else ''
                link = link_elem.text if link_elem is not None else ''
                description = desc_elem.text if desc_elem is not None else ''
                pub_date = pub_date_elem.text if pub_date_elem is not None else ''
                
                if not title:
                    continue
                
                news = {
                    'title': title,
                    'url': link,
                    'summary': description[:200] if description else title,
                    'source': f"公众号:{name}",
                    'source_type': self.source_type,
                    'published_at': pub_date or datetime.now().isoformat(),
                    'hot_score': 40,
                    'keywords': [],
                    'collected_at': datetime.now().isoformat()
                }
                
                results.append(news)
                
                if len(results) >= limit:
                    break
            
        except ET.ParseError as e:
            logger.error(f"RSS解析失败: {name}, 错误: {e}")
        
        return results
