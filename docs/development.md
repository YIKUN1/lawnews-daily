# 开发规范文档

## 1. 项目结构

```
D:\wwwroot\news\
├── config/                     # 配置文件目录
│   ├── config.yaml            # 主配置文件
│   ├── config.example.yaml    # 配置模板
│   └── keywords.txt           # 法律关键词库
│
├── crawlers/                   # 爬虫模块
│   ├── __init__.py
│   ├── base.py                # 爬虫基类
│   ├── court.py               # 官方法律网站
│   ├── weibo.py               # 微博热搜
│   ├── zhihu.py               # 知乎热榜
│   ├── news_portal.py         # 新闻门户
│   └── wechat_mp.py           # 微信公众号
│
├── processors/                 # 内容处理模块
│   ├── __init__.py
│   ├── filter.py              # 关键词过滤
│   └── dedup.py               # 去重处理
│
├── summarizer/                 # AI摘要模块
│   ├── __init__.py
│   └── ai_summary.py          # AI摘要服务
│
├── pushers/                    # 推送模块
│   ├── __init__.py
│   ├── base.py                # 推送器基类
│   ├── wechat_work.py         # 企业微信机器人
│   ├── pushplus.py            # PushPlus推送
│   └── wechaty.py             # Wechaty机器人
│
├── scheduler/                  # 定时任务模块
│   ├── __init__.py
│   └── tasks.py               # 任务调度
│
├── storage/                    # 存储模块
│   ├── __init__.py
│   └── cache.py               # 本地缓存
│
├── utils/                      # 工具模块
│   ├── __init__.py
│   ├── logger.py              # 日志工具
│   └── helpers.py             # 通用工具函数
│
├── logs/                       # 日志目录
│   └── .gitkeep
│
├── data/                       # 数据目录
│   └── .gitkeep
│
├── docs/                       # 文档目录
│   ├── requirements.md        # 需求文档
│   └── development.md         # 开发规范
│
├── main.py                     # 主入口文件
├── requirements.txt            # 依赖列表
└── README.md                   # 项目说明
```

---

## 2. 命名规范

### 2.1 文件命名
- 模块文件：小写字母 + 下划线，如 `ai_summary.py`
- 配置文件：小写字母 + 下划线，如 `config.yaml`
- 文档文件：小写字母 + 下划线，如 `requirements.md`

### 2.2 类命名
- 大驼峰命名法（PascalCase）
- 示例：`BaseCrawler`、`WeiboCrawler`、`PushPlusPusher`

### 2.3 函数/方法命名
- 小写字母 + 下划线（snake_case）
- 动词开头，表示行为
- 示例：`fetch_news()`、`filter_by_keywords()`、`send_message()`

### 2.4 变量命名
- 普通变量：小写字母 + 下划线，如 `news_list`
- 常量：全大写 + 下划线，如 `MAX_RETRY_COUNT`
- 私有变量：单下划线前缀，如 `_cache_data`

### 2.5 配置项命名
- 小写字母 + 下划线，层级结构
- 示例：
  ```yaml
  push:
    method: pushplus
    pushplus:
      token: xxx
  ```

---

## 3. 代码规范

### 3.1 编码风格
- 遵循 PEP 8 规范
- 使用 4 空格缩进
- 行宽不超过 100 字符
- 文件编码统一 UTF-8

### 3.2 导入顺序
```python
# 1. 标准库
import os
import sys
from typing import List, Dict, Optional

# 2. 第三方库
import requests
import yaml

# 3. 本地模块
from crawlers.base import BaseCrawler
from utils.logger import get_logger
```

### 3.3 文档字符串
```python
def fetch_news(self, keyword: str, limit: int = 10) -> List[Dict]:
    """
    获取新闻列表。
    
    Args:
        keyword: 搜索关键词
        limit: 返回数量限制，默认10条
    
    Returns:
        新闻字典列表，每个字典包含 title、url、summary 等字段
    
    Raises:
        NetworkError: 网络请求失败时抛出
    """
    pass
```

### 3.4 类型注解
- 所有公开函数必须添加类型注解
- 使用 typing 模块的类型

```python
from typing import List, Dict, Optional, Union

def process_news(
    news_list: List[Dict],
    keywords: List[str],
    max_count: Optional[int] = None
) -> List[Dict]:
    pass
```

### 3.5 异常处理
- 不使用裸 `except`
- 指定具体异常类型
- 记录异常日志

```python
# 正确
try:
    response = requests.get(url, timeout=10)
except requests.Timeout:
    logger.error(f"请求超时: {url}")
    return None
except requests.RequestException as e:
    logger.error(f"请求失败: {url}, 错误: {e}")
    return None

# 错误
try:
    response = requests.get(url)
except:
    pass
```

### 3.6 日志规范
```python
from utils.logger import get_logger

logger = get_logger(__name__)

# 日志级别使用
logger.debug("调试信息")
logger.info("常规信息")
logger.warning("警告信息")
logger.error("错误信息")
```

---

## 4. 模块设计原则

### 4.1 单一职责
- 每个模块只负责一个功能领域
- 爬虫模块只负责采集，不处理推送逻辑

### 4.2 依赖注入
- 通过配置文件注入依赖
- 不在代码中硬编码配置

### 4.3 接口抽象
- 爬虫模块：继承 `BaseCrawler` 基类
- 推送模块：继承 `BasePusher` 基类
- AI模块：继承 `BaseSummarizer` 基类

### 4.4 基类设计
```python
# crawlers/base.py
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseCrawler(ABC):
    """爬虫基类"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    @abstractmethod
    def fetch(self, limit: int = 10) -> List[Dict]:
        """
        获取数据（子类必须实现）
        
        Returns:
            标准化的新闻列表
        """
        pass
    
    def normalize(self, raw_data: Dict) -> Dict:
        """标准化数据格式"""
        return {
            'title': raw_data.get('title', ''),
            'url': raw_data.get('url', ''),
            'summary': raw_data.get('summary', ''),
            'source': raw_data.get('source', ''),
            'published_at': raw_data.get('published_at', ''),
            'hot_score': raw_data.get('hot_score', 0)
        }
```

---

## 5. 数据结构规范

### 5.1 新闻条目标准格式
```python
{
    'title': str,           # 标题
    'url': str,             # 原文链接
    'summary': str,         # 摘要（原文或AI生成）
    'source': str,          # 来源名称
    'source_type': str,     # 来源类型: court/weibo/zhihu/news/wechat
    'published_at': str,    # 发布时间 ISO格式
    'hot_score': int,       # 热度分数
    'keywords': List[str],  # 命中的关键词
    'collected_at': str     # 采集时间
}
```

### 5.2 推送结果格式
```python
{
    'success': bool,        # 是否成功
    'message': str,         # 结果消息
    'content': str,         # 推送内容
    'pushed_at': str,       # 推送时间
    'error': Optional[str]  # 错误信息
}
```

---

## 6. 配置文件规范

### 6.1 配置文件结构
```yaml
# config/config.yaml

# 系统设置
system:
  log_level: INFO
  data_dir: ./data
  cache_expire_days: 7

# 采集设置
crawler:
  timeout: 30
  max_retry: 3
  sources:
    court: true
    weibo: true
    zhihu: true
    news_portal: true
    wechat_mp: false

# 内容处理设置
processor:
  max_items: 10
  min_hot_score: 0
  dedup_threshold: 0.8

# AI摘要设置
summarizer:
  provider: qwen  # qwen/openai/wenxin/deepseek
  api_key: ${QWEN_API_KEY}  # 支持环境变量
  model: qwen-turbo
  max_tokens: 200

# 推送设置
push:
  method: pushplus  # pushplus/wechat_work/wechaty
  
  pushplus:
    token: ${PUSHPLUS_TOKEN}
  
  wechat_work:
    webhook: ${WECHAT_WORK_WEBHOOK}
  
  wechaty:
    puppet: wechaty-puppet-wechat
    room_ids: []

# 定时任务设置
scheduler:
  enabled: true
  morning:
    hour: 8
    minute: 0
  evening:
    hour: 18
    minute: 0
```

### 6.2 配置加载
```python
import os
import yaml
from string import Template

def load_config(config_path: str) -> Dict:
    """加载配置文件，支持环境变量替换"""
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换环境变量
    template = Template(content)
    content = template.safe_substitute(os.environ)
    
    return yaml.safe_load(content)
```

---

## 7. 测试规范

### 7.1 测试文件位置
```
tests/
├── test_crawlers/
│   ├── test_court.py
│   ├── test_weibo.py
│   └── ...
├── test_processors/
├── test_pushers/
└── conftest.py
```

### 7.2 测试命名
- 测试文件：`test_模块名.py`
- 测试函数：`test_功能描述`

### 7.3 测试覆盖
- 核心功能必须有测试
- 边界条件必须测试
- 异常情况必须测试

---

## 8. 版本控制规范

### 8.1 提交信息格式
```
<type>(<scope>): <subject>

<body>
```

**type 类型**:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(crawler): 添加微博热搜爬虫

- 支持获取实时热搜榜
- 自动过滤法律相关内容
- 添加热度排序功能
```

---

## 9. 依赖管理

### 9.1 requirements.txt 结构
```
# 核心依赖
requests>=2.28.0
pyyaml>=6.0
apscheduler>=3.9.0

# AI相关
openai>=1.0.0
dashscope>=1.14.0  # 通义千问

# 推送相关
# 无额外依赖，使用requests

# 开发依赖
pytest>=7.0.0
black>=23.0.0
mypy>=1.0.0
```

### 9.2 版本锁定
- 生产环境使用 `requirements.txt` 锁定版本
- 开发环境可使用宽松版本

---

## 10. 扩展指南

### 10.1 添加新的爬虫源
1. 在 `crawlers/` 下创建新文件
2. 继承 `BaseCrawler` 类
3. 实现 `fetch()` 方法
4. 在配置文件中添加开关
5. 在 `main.py` 中注册

### 10.2 添加新的推送方式
1. 在 `pushers/` 下创建新文件
2. 继承 `BasePusher` 类
3. 实现 `send()` 方法
4. 在配置文件中添加配置项
5. 在工厂方法中注册

### 10.3 添加新的AI服务
1. 在 `summarizer/` 中添加新的实现类
2. 继承 `BaseSummarizer`
3. 实现 `summarize()` 方法
4. 在配置中添加API设置
