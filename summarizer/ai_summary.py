from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseSummarizer(ABC):
    """AI摘要基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_key = config.get('api_key', '')
        self.model = config.get('model', '')
        self.max_tokens = config.get('max_tokens', 200)
    
    @abstractmethod
    def summarize(self, title: str, content: str) -> str:
        """
        生成摘要。
        
        Args:
            title: 标题
            content: 内容
        
        Returns:
            摘要文本
        """
        pass
    
    def _build_prompt(self, title: str, content: str) -> str:
        """构建提示词"""
        return f"""请为以下法律新闻生成一段简短的摘要（50-100字），提炼关键法律要点。

标题：{title}

内容：{content[:500]}

要求：
1. 简洁明了，突出法律要点
2. 保持客观中立
3. 字数控制在50-100字

摘要："""


class QwenSummarizer(BaseSummarizer):
    """通义千问摘要器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get('model', 'qwen-turbo')
    
    def summarize(self, title: str, content: str) -> str:
        """使用通义千问生成摘要"""
        if not self.api_key:
            logger.warning("通义千问API密钥未配置")
            return content[:100] + "..."
        
        try:
            import dashscope
            from dashscope import Generation
            
            dashscope.api_key = self.api_key
            
            prompt = self._build_prompt(title, content)
            
            response = Generation.call(
                model=self.model,
                prompt=prompt,
                max_tokens=self.max_tokens
            )
            
            if response.status_code == 200:
                return response.output.text.strip()
            else:
                logger.error(f"通义千问调用失败: {response.message}")
                return content[:100] + "..."
                
        except ImportError:
            logger.warning("dashscope未安装，请运行: pip install dashscope")
            return content[:100] + "..."
        except Exception as e:
            logger.error(f"通义千问调用异常: {e}")
            return content[:100] + "..."


class OpenAISummarizer(BaseSummarizer):
    """OpenAI摘要器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get('model', 'gpt-3.5-turbo')
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
    
    def summarize(self, title: str, content: str) -> str:
        """使用OpenAI生成摘要"""
        if not self.api_key:
            logger.warning("OpenAI API密钥未配置")
            return content[:100] + "..."
        
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            prompt = self._build_prompt(title, content)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的法律新闻摘要助手。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
                
        except ImportError:
            logger.warning("openai未安装，请运行: pip install openai")
            return content[:100] + "..."
        except Exception as e:
            logger.error(f"OpenAI调用异常: {e}")
            return content[:100] + "..."


class DeepSeekSummarizer(BaseSummarizer):
    """DeepSeek摘要器"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.model = config.get('model', 'deepseek-chat')
        self.base_url = config.get('base_url', 'https://api.deepseek.com/v1')
    
    def summarize(self, title: str, content: str) -> str:
        """使用DeepSeek生成摘要"""
        if not self.api_key:
            logger.warning("DeepSeek API密钥未配置")
            return content[:100] + "..."
        
        try:
            import openai
            
            client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            prompt = self._build_prompt(title, content)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的法律新闻摘要助手。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens
            )
            
            return response.choices[0].message.content.strip()
                
        except ImportError:
            logger.warning("openai未安装，请运行: pip install openai")
            return content[:100] + "..."
        except Exception as e:
            logger.error(f"DeepSeek调用异常: {e}")
            return content[:100] + "..."


class SimpleSummarizer(BaseSummarizer):
    """简单摘要器（不使用AI）"""
    
    def summarize(self, title: str, content: str) -> str:
        """简单截取内容作为摘要"""
        if content:
            # 截取前100字
            summary = content[:100]
            if len(content) > 100:
                summary += "..."
            return summary
        return title


class AISummarizer:
    """AI摘要服务"""
    
    PROVIDERS = {
        'qwen': QwenSummarizer,
        'openai': OpenAISummarizer,
        'deepseek': DeepSeekSummarizer,
        'simple': SimpleSummarizer,
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化AI摘要服务。
        
        Args:
            config: 配置字典
        """
        self.config = config
        provider = config.get('provider', 'simple')
        
        summarizer_class = self.PROVIDERS.get(provider, SimpleSummarizer)
        self.summarizer = summarizer_class(config)
        
        logger.info(f"AI摘要服务初始化: {provider}")
    
    def summarize(self, title: str, content: str) -> str:
        """
        生成摘要。
        
        Args:
            title: 标题
            content: 内容
        
        Returns:
            摘要文本
        """
        return self.summarizer.summarize(title, content)
    
    def summarize_news(self, news: Dict) -> Dict:
        """
        为新闻生成摘要。
        
        Args:
            news: 新闻字典
        
        Returns:
            更新后的新闻字典
        """
        title = news.get('title', '')
        content = news.get('summary', '')
        
        # 检测无效摘要：空、太短、与标题重复
        is_invalid = (
            not content or 
            len(content) < 20 or
            content == title or 
            content.startswith(title) or
            title in content
        )
        
        # 只有有效摘要才跳过AI生成
        if not is_invalid and 50 <= len(content) <= 200:
            return news
        
        # 调用AI生成摘要
        summary = self.summarize(title, content or title)
        news['summary'] = summary
        
        return news
    
    def summarize_batch(self, news_list: List[Dict]) -> List[Dict]:
        """
        批量生成摘要。
        
        Args:
            news_list: 新闻列表
        
        Returns:
            更新后的新闻列表
        """
        results = []
        for i, news in enumerate(news_list):
            try:
                result = self.summarize_news(news)
                results.append(result)
                logger.debug(f"摘要生成 [{i+1}/{len(news_list)}]: {news.get('title', '')[:30]}...")
            except Exception as e:
                logger.error(f"摘要生成失败: {news.get('title', '')}, 错误: {e}")
                results.append(news)  # 保留原数据
        
        return results


def create_summarizer(config: Dict[str, Any]) -> AISummarizer:
    """
    创建AI摘要器实例。
    
    Args:
        config: 配置字典
    
    Returns:
        AISummarizer实例
    """
    return AISummarizer(config)
