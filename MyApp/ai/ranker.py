"""
重排序 Agent - 使用 DeepSeek 对候选进行打分排序
"""
from .deepseek import DeepSeekClient


RERANK_PROMPT = """你是一个热心帮助同学找回失物的志愿者。请判断下面两个帖子描述的是否可能是同一件物品。

【有人在找】
{lost_title}
{lost_desc}
物品类型：{lost_type}
丢失地点：{lost_location}

【有人捡到】
{found_title}
{found_desc}
物品类型：{found_type}
捡到地点：{found_location}

请用自然亲切的语气，像朋友一样给出你的判断。返回 JSON 格式：
{{
    "confidence": 0.0到1.0之间的数字（1.0表示非常确定是同一件物品）,
    "reason": "用一两句话，像朋友聊天一样说明为什么你觉得这可能是/不是同一件物品"
}}

理由示例（参考风格，不要照抄）：
- "都是黑色的华为手机，而且丢失和捡到的地方都在图书馆附近，很可能就是同一部！"
- "虽然都是钥匙，但一个是宿舍钥匙一个是车钥匙，应该不是同一串。"
- "蓝色的书包，捡到的地点离丢失的地方不远，可以去确认一下。"
- "时间和地点都对得上，而且都提到了有划痕，八成就是这个！"

只返回 JSON，不要其他内容。"""


class CandidateRanker:
    """候选重排序器"""

    def __init__(self, client: DeepSeekClient = None):
        self.client = client or DeepSeekClient()

    def rerank(self, lost_post, found_post) -> dict:
        """
        对单个候选对进行重排序打分
        
        Args:
            lost_post: 寻物帖（Post 实例）
            found_post: 招领帖（Post 实例）
            
        Returns:
            {'confidence': float, 'reason': str}
        """
        # 如果 API 不可用，返回基础评分
        if not self.client.is_available():
            return self._fallback_rerank(lost_post, found_post)

        # 构建提示词
        user_prompt = RERANK_PROMPT.format(
            lost_title=lost_post.title,
            lost_desc=lost_post.description[:500] if lost_post.description else "",
            lost_type=lost_post.ItemType,
            lost_location=lost_post.Location,
            found_title=found_post.title,
            found_desc=found_post.description[:500] if found_post.description else "",
            found_type=found_post.ItemType,
            found_location=found_post.Location
        )

        # 调用 API
        response = self.client.chat(
            system_prompt="你是一个失物招领匹配专家，只返回 JSON 格式的结果。",
            user_prompt=user_prompt,
            temperature=0.2
        )

        # 解析结果
        result = self.client.extract_json(response)
        if not result:
            return self._fallback_rerank(lost_post, found_post)

        # 确保返回格式正确
        confidence = result.get('confidence', 0.5)
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except ValueError:
                confidence = 0.5
        confidence = max(0.0, min(1.0, confidence))

        return {
            'confidence': confidence,
            'reason': result.get('reason', '无法获取匹配理由')
        }

    def _fallback_rerank(self, lost_post, found_post) -> dict:
        """
        降级方案：基于简单规则计算置信度
        """
        confidence = 0.3  # 基础分
        reasons = []

        # 类型匹配加分
        if lost_post.ItemType and found_post.ItemType:
            if lost_post.ItemType == found_post.ItemType:
                confidence += 0.3
                reasons.append(f"都是{lost_post.ItemType}")
            else:
                reasons.append("物品类型不太一样")

        # 位置相似加分
        if lost_post.Location and found_post.Location:
            lost_loc = lost_post.Location
            found_loc = found_post.Location
            if lost_loc == found_loc:
                confidence += 0.2
                reasons.append("地点也吻合")
            elif lost_loc[:1] == found_loc[:1]:  # 同一区域
                confidence += 0.1
                reasons.append("在附近区域")

        # 标题相似加分
        if lost_post.title and found_post.title:
            lost_words = set(lost_post.title)
            found_words = set(found_post.title)
            common = lost_words & found_words - set(' ，。、')
            if len(common) > 3:
                confidence += 0.1
                reasons.append("描述有些相似")

        confidence = min(1.0, confidence)

        # 生成自然的理由
        if confidence >= 0.6:
            reason = "，".join(reasons[:2]) + "，可以去看看是不是你的！"
        elif confidence >= 0.4:
            reason = "，".join(reasons[:2]) + "，不确定是不是同一个，建议确认一下。"
        else:
            reason = reasons[0] if reasons else "信息有限" + "，匹配度不高，仅供参考。"

        return {
            'confidence': confidence,
            'reason': reason
        }

    def batch_rerank(self, lost_post, candidates: list, min_score: float = 0.1) -> list:
        """
        批量重排序
        
        Args:
            lost_post: 寻物帖
            candidates: [(found_post, tfidf_score), ...] 候选列表
            min_score: 最低分数阈值
            
        Returns:
            [(found_post, tfidf_score, rerank_result), ...] 按置信度降序排列
        """
        results = []
        for found_post, tfidf_score in candidates:
            if tfidf_score < min_score:
                continue
            rerank_result = self.rerank(lost_post, found_post)
            results.append((found_post, tfidf_score, rerank_result))

        # 按 LLM 置信度降序排序
        results.sort(key=lambda x: x[2]['confidence'], reverse=True)
        return results
