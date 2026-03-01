#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LawNews Daily - 法律新闻日报收集系统

功能：
- 自动收集多来源法律资讯
- 智能过滤和去重
- AI生成摘要
- 推送到微信群

使用方法：
    python main.py              # 运行定时任务
    python main.py --now        # 立即执行一次
    python main.py --morning    # 立即执行早报
    python main.py --evening    # 立即执行晚报
    python main.py --test       # 测试模式（不推送）
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.logger import get_logger
from utils.helpers import load_config, get_data_dir, get_log_dir
from storage.cache import Cache
from processors.filter import KeywordFilter
from processors.dedup import Deduplicator
from summarizer import AISummarizer
from pushers import create_pusher
from scheduler import Scheduler
from crawlers import (
    CourtCrawler,
    WeiboCrawler,
    ZhihuCrawler,
    NewsPortalCrawler,
    WeChatMPCrawler,
    RSSCrawler
)

logger = get_logger(__name__)


class LawNewsCollector:
    """法律新闻收集器"""
    
    def __init__(self, config: Dict = None):
        """
        初始化收集器。
        
        Args:
            config: 配置字典，默认从文件加载
        """
        self.config = config or load_config()
        
        # 初始化各模块
        self._init_storage()
        self._init_processors()
        self._init_summarizer()
        self._init_pusher()
        self._init_crawlers()
    
    def _init_storage(self) -> None:
        """初始化存储模块"""
        data_dir = get_data_dir()
        expire_days = self.config.get('system', {}).get('cache_expire_days', 7)
        self.cache = Cache(data_dir, expire_days)
    
    def _init_processors(self) -> None:
        """初始化处理器"""
        # 关键词过滤
        self.filter = KeywordFilter()
        
        # 去重器
        threshold = self.config.get('processor', {}).get('dedup_threshold', 0.8)
        self.dedup = Deduplicator(threshold)
    
    def _init_summarizer(self) -> None:
        """初始化AI摘要"""
        summarizer_config = self.config.get('summarizer', {})
        self.summarizer = AISummarizer(summarizer_config)
    
    def _init_pusher(self) -> None:
        """初始化推送器"""
        push_config = self.config.get('push', {})
        self.pusher = create_pusher(push_config)
    
    def _init_crawlers(self) -> None:
        """初始化爬虫"""
        crawler_config = self.config.get('crawler', {})
        sources = crawler_config.get('sources', {})
        
        self.crawlers = []
        
        # RSS源（最可靠，可从国外访问）
        if sources.get('rss', True):
            self.crawlers.append(RSSCrawler(crawler_config))
        
        if sources.get('court', True):
            self.crawlers.append(CourtCrawler(crawler_config))
        
        if sources.get('weibo', True):
            self.crawlers.append(WeiboCrawler(crawler_config))
        
        if sources.get('zhihu', True):
            self.crawlers.append(ZhihuCrawler(crawler_config))
        
        if sources.get('news_portal', True):
            self.crawlers.append(NewsPortalCrawler(crawler_config))
        
        if sources.get('wechat_mp', False):
            self.crawlers.append(WeChatMPCrawler(crawler_config))
        
        logger.info(f"已加载 {len(self.crawlers)} 个爬虫")
    
    def collect(self) -> List[Dict]:
        """
        收集新闻。
        
        Returns:
            新闻列表
        """
        all_news = []
        
        for crawler in self.crawlers:
            try:
                logger.info(f"开始采集: {crawler.source_name}")
                news_list = crawler.fetch(limit=20)
                
                # 标准化数据
                news_list = [crawler.normalize(n) for n in news_list]
                
                all_news.extend(news_list)
                logger.info(f"采集完成: {crawler.source_name}, 获取 {len(news_list)} 条")
                
            except Exception as e:
                logger.error(f"采集失败: {crawler.source_name}, 错误: {e}")
        
        logger.info(f"总共采集 {len(all_news)} 条新闻")
        return all_news
    
    def process(self, news_list: List[Dict]) -> List[Dict]:
        """
        处理新闻（过滤、去重）。
        
        Args:
            news_list: 原始新闻列表
        
        Returns:
            处理后的新闻列表
        """
        if not news_list:
            return []
        
        # 1. 关键词过滤
        filtered = self.filter.filter_batch(news_list, min_matches=1)
        
        # 2. URL去重（基于缓存）
        url_filtered = []
        for news in filtered:
            url = news.get('url', '')
            if url and self.cache.exists(url):
                logger.debug(f"URL缓存命中: {news.get('title', '')[:30]}")
                continue
            url_filtered.append(news)
        
        # 3. 内容去重
        deduped = self.dedup.dedup_batch(url_filtered)
        
        # 4. 热度排序
        deduped.sort(key=lambda x: x.get('hot_score', 0), reverse=True)
        
        # 5. 数量限制
        max_items = self.config.get('processor', {}).get('max_items', 10)
        result = deduped[:max_items]
        
        logger.info(f"处理完成: {len(news_list)} -> {len(result)} 条")
        return result
    
    def summarize(self, news_list: List[Dict]) -> List[Dict]:
        """
        生成摘要。
        
        Args:
            news_list: 新闻列表
        
        Returns:
            更新后的新闻列表
        """
        return self.summarizer.summarize_batch(news_list)
    
    def push(self, news_list: List[Dict], report_type: str = "早报") -> Dict:
        """
        推送新闻。
        
        Args:
            news_list: 新闻列表
            report_type: 报告类型
        
        Returns:
            推送结果
        """
        if not news_list:
            logger.warning("没有新闻可推送")
            return {'success': False, 'message': '没有新闻'}
        
        # 推送
        result = self.pusher.push_news(news_list, report_type)
        
        # 记录到缓存
        if result.get('success'):
            for news in news_list:
                url = news.get('url', '')
                if url:
                    self.cache.add(
                        url,
                        news.get('title', ''),
                        news.get('summary', '')
                    )
        
        return result
    
    def run(self, report_type: str = "早报", dry_run: bool = False) -> Dict:
        """
        执行完整流程。
        
        Args:
            report_type: 报告类型（早报/晚报）
            dry_run: 测试模式（不推送）
        
        Returns:
            执行结果
        """
        logger.info(f"开始执行: {report_type}")
        
        # 1. 收集
        news_list = self.collect()
        
        # 2. 处理
        news_list = self.process(news_list)
        
        # 3. 生成摘要
        news_list = self.summarize(news_list)
        
        # 4. 推送（或测试）
        if dry_run:
            logger.info("[测试模式] 跳过推送")
            result = {
                'success': True,
                'message': '测试模式完成',
                'news_count': len(news_list),
                'news_list': news_list
            }
        else:
            result = self.push(news_list, report_type)
            result['news_count'] = len(news_list)
        
        logger.info(f"执行完成: {report_type}, 新闻数: {len(news_list)}")
        return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='LawNews Daily - 法律新闻日报收集系统'
    )
    parser.add_argument(
        '--now', '-n',
        action='store_true',
        help='立即执行一次'
    )
    parser.add_argument(
        '--morning', '-m',
        action='store_true',
        help='立即执行早报'
    )
    parser.add_argument(
        '--evening', '-e',
        action='store_true',
        help='立即执行晚报'
    )
    parser.add_argument(
        '--auto', '-a',
        action='store_true',
        help='自动模式：根据时间自动判断早报/晚报（上午发早报，下午发晚报）'
    )
    parser.add_argument(
        '--test', '-t',
        action='store_true',
        help='测试模式（不推送）'
    )
    parser.add_argument(
        '--daemon', '-d',
        action='store_true',
        help='守护进程模式（定时任务）'
    )
    parser.add_argument(
        '--config', '-c',
        type=str,
        default=None,
        help='配置文件路径'
    )
    
    args = parser.parse_args()
    
    # 加载配置
    config = load_config(args.config)
    
    # 创建收集器
    collector = LawNewsCollector(config)
    
    # 执行模式
    if args.test:
        # 测试模式
        result = collector.run(dry_run=True)
        print(f"\n测试完成，获取 {result.get('news_count', 0)} 条新闻")
        
        # 显示新闻列表
        for i, news in enumerate(result.get('news_list', []), 1):
            print(f"\n{i}. {news.get('title', '')}")
            print(f"   来源: {news.get('source', '')}")
            print(f"   摘要: {news.get('summary', '')[:50]}...")
    
    elif args.auto:
        # 自动模式：根据时间判断早报/晚报
        from datetime import datetime
        hour = datetime.now().hour
        if hour < 12:
            report_type = "早报"
        else:
            report_type = "晚报"
        result = collector.run(report_type)
        print(f"\n{report_type}执行完成: {result.get('message', '')}")
    
    elif args.now or args.morning:
        # 立即执行早报
        result = collector.run("早报")
        print(f"\n早报执行完成: {result.get('message', '')}")
    
    elif args.evening:
        # 立即执行晚报
        result = collector.run("晚报")
        print(f"\n晚报执行完成: {result.get('message', '')}")
    
    else:
        # 默认：定时任务模式
        scheduler = Scheduler(config.get('scheduler', {}))
        
        # 添加任务
        scheduler.add_job(collector.run, 'morning')
        scheduler.add_job(collector.run, 'evening')
        
        print("\n法律新闻日报系统已启动")
        print(f"早报时间: {config.get('scheduler', {}).get('morning', {}).get('hour', 8):02d}:00")
        print(f"晚报时间: {config.get('scheduler', {}).get('evening', {}).get('hour', 18):02d}:00")
        print("\n按 Ctrl+C 停止\n")
        
        try:
            scheduler.start()
        except KeyboardInterrupt:
            scheduler.stop()
            print("\n系统已停止")


if __name__ == '__main__':
    main()
