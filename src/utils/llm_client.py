"""
LLM 客户端封装模块
提供 OpenAI API 兼容的 LLM 调用接口，支持重试机制和错误处理
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from openai import OpenAI, APIError, APITimeoutError, RateLimitError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class LLMClient:
    """LLM 客户端封装类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化 LLM 客户端
        
        Args:
            config: 配置字典，包含 model, temperature, max_tokens 等参数
        """
        self.config = config
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY', config.get('openai', {}).get('api_key', '')),
            base_url=os.getenv('OPENAI_BASE_URL', config.get('openai', {}).get('base_url', 'https://api.openai.com/v1'))
        )
        
        # 重试配置
        self.retry_config = {
            'stop': stop_after_attempt(config.get('llm', {}).get('retry_attempts', 3)),
            'wait': wait_exponential(multiplier=1, min=config.get('llm', {}).get('retry_delay', 2), max=10),
            'retry': retry_if_exception_type((APIError, APITimeoutError, RateLimitError))
        }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APIError, APITimeoutError, RateLimitError))
    )
    def generate_completion(self, prompt: str, system_prompt: Optional[str] = None, **kwargs) -> str:
        """
        生成文本补全
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            **kwargs: 其他参数
            
        Returns:
            LLM 生成的文本
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        llm_config = self.config.get('llm', {})
        params = {
            "model": llm_config.get('model', 'gpt-4-turbo-preview'),
            "messages": messages,
            "temperature": kwargs.get('temperature', llm_config.get('temperature', 0.1)),
            "max_tokens": kwargs.get('max_tokens', llm_config.get('max_tokens', 4096)),
            "timeout": kwargs.get('timeout', llm_config.get('timeout', 30))
        }
        
        try:
            response = self.client.chat.completions.create(**params)
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM 调用失败: {str(e)}")
            raise
    
    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        生成 JSON 格式的响应
        
        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词
            
        Returns:
            解析后的 JSON 字典
        """
        json_prompt = f"""
请严格按照 JSON 格式返回响应，不要包含任何额外的文本或解释。

{prompt}

请返回纯 JSON 格式：
"""
        
        response = self.generate_completion(json_prompt, system_prompt)
        
        # 尝试解析 JSON
        import json
        try:
            # 提取 JSON 部分
            if '```json' in response:
                json_str = response.split('```json')[1].split('```')[0].strip()
            elif '```' in response:
                json_str = response.split('```')[1].strip()
            else:
                json_str = response.strip()
            
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON 解析失败，尝试修复: {e}")
            # 尝试修复 JSON
            return self._fix_json(response)
    
    def _fix_json(self, text: str) -> Dict[str, Any]:
        """尝试修复格式错误的 JSON"""
        import json
        import re
        
        # 移除可能的代码块标记
        text = re.sub(r'```(json)?', '', text).strip()
        
        # 尝试多种解析方式
        for attempt in range(3):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                # 尝试修复常见的 JSON 问题
                text = re.sub(r',\s*\}', '}', text)  # 移除尾随逗号
                text = re.sub(r',\s*\]', ']', text)
                text = re.sub(r"'", '"', text)  # 单引号转双引号
        
        # 如果仍然失败，请求 LLM 修复
        fix_prompt = f"""
以下文本应该是一个 JSON 对象，但格式有误。请修复并返回正确的 JSON 格式：

{text}

请只返回修复后的 JSON，不要包含其他内容。
"""
        
        fixed_response = self.generate_completion(fix_prompt, "你是一个 JSON 格式修复专家")
        return json.loads(fixed_response)


class LLMError(Exception):
    """LLM 相关错误"""
    pass