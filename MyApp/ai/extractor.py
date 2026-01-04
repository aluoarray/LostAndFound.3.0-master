"""
实体抽取 Agent - 从帖子中提取结构化信息
"""
from .deepseek import DeepSeekClient


EXTRACTION_PROMPT = """你是一个专业的信息抽取助手。请从以下失物/招领帖子中提取结构化信息。

帖子内容：
标题：{title}
描述：{description}
类型：{item_type}
位置：{location}

请以 JSON 格式返回以下字段（如果信息不存在则留空字符串）：
{{
    "item_name": "物品名称",
    "color": "颜色",
    "brand": "品牌",
    "features": "特征描述（材质、大小、独特标记等）",
    "location_detail": "详细位置",
    "time_info": "时间信息"
}}

只返回 JSON，不要其他内容。"""


class EntityExtractor:
    """实体抽取器"""

    def __init__(self, client: DeepSeekClient = None):
        self.client = client or DeepSeekClient()

    def extract(self, post) -> dict:
        """
        从帖子中抽取实体信息
        
        Args:
            post: Post 模型实例
            
        Returns:
            抽取的实体信息字典
        """
        # 如果 API 不可用，返回基础信息
        if not self.client.is_available():
            return self._fallback_extract(post)

        # 构建提示词
        user_prompt = EXTRACTION_PROMPT.format(
            title=post.title,
            description=post.description,
            item_type=post.ItemType,
            location=post.Location
        )

        # 调用 API
        response = self.client.chat(
            system_prompt="你是一个专业的信息抽取助手，只返回 JSON 格式的结果。",
            user_prompt=user_prompt,
            temperature=0.1
        )

        # 解析结果
        result = self.client.extract_json(response)
        if not result:
            return self._fallback_extract(post)

        return result

    def _fallback_extract(self, post) -> dict:
        """
        降级方案：直接从帖子字段提取基础信息
        """
        return {
            "item_name": post.title,
            "color": "",
            "brand": "",
            "features": post.description[:200] if post.description else "",
            "location_detail": post.Location,
            "time_info": str(post.PostTime) if post.PostTime else ""
        }

    def save_extraction(self, post, extraction_data: dict):
        """
        保存抽取结果到数据库
        
        Args:
            post: Post 模型实例
            extraction_data: 抽取的数据字典
        """
        from MyApp.models import ExtractionCache

        ExtractionCache.objects.update_or_create(
            post=post,
            defaults={
                'item_name': extraction_data.get('item_name', '')[:100],
                'color': extraction_data.get('color', '')[:50],
                'brand': extraction_data.get('brand', '')[:100],
                'features': extraction_data.get('features', ''),
                'location_detail': extraction_data.get('location_detail', '')[:200],
                'time_info': extraction_data.get('time_info', '')[:100],
                'raw_json': extraction_data
            }
        )
