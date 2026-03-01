import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class Cache:
    """本地缓存管理"""
    
    def __init__(self, cache_dir: Path, expire_days: int = 7):
        """
        初始化缓存。
        
        Args:
            cache_dir: 缓存目录
            expire_days: 过期天数
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.expire_days = expire_days
        self.cache_file = self.cache_dir / "news_cache.json"
        self._cache: Dict[str, Dict] = self._load()
    
    def _load(self) -> Dict[str, Dict]:
        """加载缓存文件"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}")
        return {}
    
    def _save(self) -> None:
        """保存缓存文件"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def _get_url_hash(self, url: str) -> str:
        """计算URL哈希值"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def exists(self, url: str) -> bool:
        """
        检查URL是否已缓存。
        
        Args:
            url: 新闻链接
        
        Returns:
            是否存在
        """
        url_hash = self._get_url_hash(url)
        if url_hash not in self._cache:
            return False
        
        # 检查是否过期
        item = self._cache[url_hash]
        cached_time = datetime.fromisoformat(item.get('cached_at', '2000-01-01'))
        if datetime.now() - cached_time > timedelta(days=self.expire_days):
            del self._cache[url_hash]
            self._save()
            return False
        
        return True
    
    def add(self, url: str, title: str = "", content: str = "") -> None:
        """
        添加到缓存。
        
        Args:
            url: 新闻链接
            title: 标题
            content: 内容
        """
        url_hash = self._get_url_hash(url)
        self._cache[url_hash] = {
            'url': url,
            'title': title,
            'content': content,
            'cached_at': datetime.now().isoformat()
        }
        self._save()
    
    def get(self, url: str) -> Optional[Dict]:
        """
        获取缓存内容。
        
        Args:
            url: 新闻链接
        
        Returns:
            缓存内容或None
        """
        url_hash = self._get_url_hash(url)
        return self._cache.get(url_hash)
    
    def clear_expired(self) -> int:
        """
        清理过期缓存。
        
        Returns:
            清理的条目数
        """
        expired_keys = []
        threshold = datetime.now() - timedelta(days=self.expire_days)
        
        for key, item in self._cache.items():
            cached_time = datetime.fromisoformat(item.get('cached_at', '2000-01-01'))
            if cached_time < threshold:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            self._save()
            logger.info(f"清理过期缓存 {len(expired_keys)} 条")
        
        return len(expired_keys)
    
    def get_all_urls(self) -> List[str]:
        """获取所有已缓存的URL"""
        return [item.get('url', '') for item in self._cache.values()]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            'total_items': len(self._cache),
            'cache_file': str(self.cache_file),
            'expire_days': self.expire_days
        }
