import time
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseCrawler(ABC):
    """爬虫基类"""
    
    # 来源类型标识
    source_type: str = "unknown"
    # 来源名称
    source_name: str = "未知来源"
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化爬虫。
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.timeout = config.get('timeout', 30)
        self.max_retry = config.get('max_retry', 3)
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """创建带重试机制的请求会话"""
        session = requests.Session()
        
        retry_strategy = Retry(
            total=self.max_retry,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # 默认请求头
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        })
        
        return session
    
    def request(
        self,
        url: str,
        method: str = "GET",
        **kwargs
    ) -> Optional[requests.Response]:
        """
        发送HTTP请求。
        
        Args:
            url: 请求URL
            method: 请求方法
            **kwargs: 其他请求参数
        
        Returns:
            响应对象或None
        """
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            logger.debug(f"请求: {method} {url}")
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.Timeout:
            logger.error(f"请求超时: {url}")
        except requests.RequestException as e:
            logger.error(f"请求失败: {url}, 错误: {e}")
        
        return None
    
    def get_json(self, url: str, **kwargs) -> Optional[Dict]:
        """
        获取JSON数据。
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数
        
        Returns:
            JSON字典或None
        """
        response = self.request(url, **kwargs)
        if response:
            try:
                return response.json()
            except ValueError as e:
                logger.error(f"JSON解析失败: {url}, 错误: {e}")
        return None
    
    def get_html(self, url: str, **kwargs) -> Optional[str]:
        """
        获取HTML内容。
        
        Args:
            url: 请求URL
            **kwargs: 其他请求参数
        
        Returns:
            HTML字符串或None
        """
        response = self.request(url, **kwargs)
        if response:
            return response.text
        return None
    
    @abstractmethod
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取数据（子类必须实现）。
        
        Args:
            limit: 返回数量限制
        
        Returns:
            标准化的新闻列表
        """
        pass
    
    def normalize(self, raw_data: Dict) -> Dict:
        """
        标准化数据格式。
        
        Args:
            raw_data: 原始数据
        
        Returns:
            标准化的数据字典
        """
        return {
            'title': raw_data.get('title', ''),
            'url': raw_data.get('url', ''),
            'summary': raw_data.get('summary', ''),
            'source': raw_data.get('source', self.source_name),
            'source_type': raw_data.get('source_type', self.source_type),
            'published_at': raw_data.get('published_at', ''),
            'hot_score': raw_data.get('hot_score', 0),
            'keywords': [],
            'collected_at': datetime.now().isoformat()
        }
    
    def close(self) -> None:
        """关闭会话"""
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
