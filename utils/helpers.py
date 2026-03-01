import os
import yaml
from pathlib import Path
from string import Template
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """获取项目根目录"""
    return Path(__file__).parent.parent


def get_data_dir() -> Path:
    """获取数据目录"""
    data_dir = get_project_root() / "data"
    ensure_dir(data_dir)
    return data_dir


def get_log_dir() -> Path:
    """获取日志目录"""
    log_dir = get_project_root() / "logs"
    ensure_dir(log_dir)
    return log_dir


def ensure_dir(path: Path) -> Path:
    """确保目录存在"""
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载配置文件，支持环境变量替换。
    
    Args:
        config_path: 配置文件路径，默认为 config/config.yaml
    
    Returns:
        配置字典
    """
    if config_path is None:
        config_path = str(get_project_root() / "config" / "config.yaml")
    
    # 检查配置文件是否存在
    if not os.path.exists(config_path):
        # 尝试加载示例配置
        example_path = str(get_project_root() / "config" / "config.example.yaml")
        if os.path.exists(example_path):
            config_path = example_path
        else:
            config = get_default_config()
            # 从环境变量覆盖配置
            _apply_env_config(config)
            return config
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换环境变量 ${VAR_NAME}
    template = Template(content)
    content = template.safe_substitute(os.environ)
    
    config = yaml.safe_load(content)
    
    # 从环境变量覆盖配置（优先级最高）
    _apply_env_config(config)
    
    return config


def _apply_env_config(config: Dict[str, Any]) -> None:
    """
    从环境变量覆盖配置（用于 GitHub Actions 等环境）。
    
    Args:
        config: 配置字典
    """
    # PushPlus 配置
    if os.environ.get('PUSHPLUS_TOKEN'):
        config.setdefault('push', {}).setdefault('pushplus', {})
        config['push']['pushplus']['token'] = os.environ['PUSHPLUS_TOKEN']
    
    if os.environ.get('PUSHPLUS_TOPIC'):
        config.setdefault('push', {}).setdefault('pushplus', {})
        config['push']['pushplus']['topic'] = os.environ['PUSHPLUS_TOPIC']
    
    # 通义千问 API Key
    if os.environ.get('QWEN_API_KEY'):
        config.setdefault('summarizer', {})
        config['summarizer']['api_key'] = os.environ['QWEN_API_KEY']
    
    # 企业微信 Webhook
    if os.environ.get('WECHAT_WORK_WEBHOOK'):
        config.setdefault('push', {}).setdefault('wechat_work', {})
        config['push']['wechat_work']['webhook'] = os.environ['WECHAT_WORK_WEBHOOK']


def get_default_config() -> Dict[str, Any]:
    """获取默认配置"""
    return {
        'system': {
            'log_level': 'INFO',
            'data_dir': './data',
            'cache_expire_days': 7
        },
        'crawler': {
            'timeout': 30,
            'max_retry': 3,
            'sources': {
                'court': True,
                'weibo': True,
                'zhihu': True,
                'news_portal': True,
                'wechat_mp': False
            }
        },
        'processor': {
            'max_items': 10,
            'min_hot_score': 0,
            'dedup_threshold': 0.8
        },
        'summarizer': {
            'provider': 'qwen',
            'api_key': '',
            'model': 'qwen-turbo',
            'max_tokens': 200
        },
        'push': {
            'method': 'pushplus',
            'pushplus': {'token': ''},
            'wechat_work': {'webhook': ''},
            'wechaty': {'puppet': '', 'room_ids': []}
        },
        'scheduler': {
            'enabled': True,
            'morning': {'hour': 8, 'minute': 0},
            'evening': {'hour': 18, 'minute': 0}
        }
    }


def load_keywords(keywords_path: Optional[str] = None) -> list:
    """
    加载关键词库。
    
    Args:
        keywords_path: 关键词文件路径
    
    Returns:
        关键词列表
    """
    if keywords_path is None:
        keywords_path = str(get_project_root() / "config" / "keywords.txt")
    
    if not os.path.exists(keywords_path):
        return []
    
    keywords = []
    with open(keywords_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if line and not line.startswith('#'):
                keywords.append(line)
    
    return keywords
