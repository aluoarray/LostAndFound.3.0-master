"""
DeepSeek API 封装模块
"""
import os
import json
import re
from openai import OpenAI


class DeepSeekClient:
    """DeepSeek API 客户端"""

    def __init__(self):
        api_key = os.environ.get('DEEPSEEK_API_KEY', '')
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        ) if api_key else None

    def is_available(self) -> bool:
        """检查 API 是否可用"""
        return self.client is not None

    def chat(self, system_prompt: str, user_prompt: str,
             temperature: float = 0.3, max_retries: int = 3) -> str:
        """
        发送对话请求
        
        Args:
            system_prompt: 系统提示词
            user_prompt: 用户提示词
            temperature: 温度参数，控制随机性
            max_retries: 最大重试次数
            
        Returns:
            模型返回的文本内容
        """
        if not self.is_available():
            return ""

        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    stream=False
                )
                return response.choices[0].message.content
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"DeepSeek API 调用失败: {e}")
                    return ""
        return ""

    def extract_json(self, response: str) -> dict:
        """
        从响应中提取 JSON
        
        Args:
            response: 模型返回的文本
            
        Returns:
            解析后的字典，解析失败返回空字典
        """
        if not response:
            return {}

        try:
            # 尝试直接解析
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取 ```json ... ``` 块
        match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取 { ... } 块
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return {}
