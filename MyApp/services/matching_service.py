"""
匹配服务 - 协调各 Agent 完成匹配流程
"""
from django.utils import timezone
from MyApp.models import Post, ExtractionCache, CandidateMatch, Notification
from MyApp.ai import DeepSeekClient, EntityExtractor, CandidateSearcher, CandidateRanker


class MatchingService:
    """匹配服务 - 处理帖子匹配的核心逻辑"""

    def __init__(self):
        self.deepseek = DeepSeekClient()
        self.extractor = EntityExtractor(self.deepseek)
        self.searcher = CandidateSearcher()
        self.ranker = CandidateRanker(self.deepseek)

    def process_new_post(self, post: Post) -> list:
        """
        处理新发布的帖子，执行完整匹配流程
        
        Args:
            post: 新发布的帖子
            
        Returns:
            创建的 CandidateMatch 列表
        """
        # 1. 实体抽取
        extraction_data = self.extractor.extract(post)
        self.extractor.save_extraction(post, extraction_data)

        # 2. 确定搜索范围
        if post.LostOrFound == '寻物启事':
            # 寻物帖找招领帖
            candidates = Post.objects.filter(
                LostOrFound='失物招领',
                State='未完成'
            ).exclude(id=post.id)
        else:
            # 招领帖找寻物帖
            candidates = Post.objects.filter(
                LostOrFound='寻物启事',
                State='未完成'
            ).exclude(id=post.id)

        candidates = list(candidates)
        if not candidates:
            return []

        # 3. 候选检索（TF-IDF）
        top_candidates = self.searcher.search(post, candidates, top_k=10)

        # 4. LLM 重排序
        if post.LostOrFound == '寻物启事':
            reranked = self.ranker.batch_rerank(post, top_candidates, min_score=0.05)
        else:
            # 招领帖的情况，需要反过来
            reranked = []
            for found_post, tfidf_score in top_candidates:
                if tfidf_score >= 0.05:
                    rerank_result = self.ranker.rerank(found_post, post)
                    reranked.append((found_post, tfidf_score, rerank_result))
            reranked.sort(key=lambda x: x[2]['confidence'], reverse=True)

        # 5. 创建匹配记录
        matches = []
        for candidate_post, tfidf_score, rerank_result in reranked:
            match = self._create_match(post, candidate_post, tfidf_score, rerank_result)
            if match:
                matches.append(match)

        # 6. 发送高置信度通知
        self._send_notifications(matches)

        return matches

    def _create_match(self, post: Post, candidate: Post, 
                      tfidf_score: float, rerank_result: dict) -> CandidateMatch:
        """
        创建匹配记录
        """
        # 确定哪个是寻物帖，哪个是招领帖
        if post.LostOrFound == '寻物启事':
            lost_post, found_post = post, candidate
        else:
            lost_post, found_post = candidate, post

        # 检查是否已存在
        existing = CandidateMatch.objects.filter(
            lost_post=lost_post,
            found_post=found_post
        ).first()

        if existing:
            # 更新已有记录
            existing.score = tfidf_score
            existing.rerank_confidence = rerank_result['confidence']
            existing.rerank_reason = rerank_result['reason']
            existing.save()
            return existing

        # 创建新记录
        match = CandidateMatch.objects.create(
            lost_post=lost_post,
            found_post=found_post,
            score=tfidf_score,
            method='tfidf+llm' if self.deepseek.is_available() else 'tfidf',
            rerank_confidence=rerank_result['confidence'],
            rerank_reason=rerank_result['reason'],
            status='pending'
        )
        return match

    def _send_notifications(self, matches: list, threshold: float = 0.7):
        """
        发送高置信度匹配通知（自动通知，仅匹配度极高时触发）
        
        Args:
            matches: CandidateMatch 列表
            threshold: 置信度阈值，默认 0.7
        """
        for match in matches:
            if match.rerank_confidence and match.rerank_confidence >= threshold:
                # 通知寻物帖发布者
                self._create_notification(
                    user=match.lost_post.user,
                    match=match,
                    title=f"🔥 极有可能是您丢失的物品！",
                    content=f"您发布的寻物帖「{match.lost_post.title}」与招领帖「{match.found_post.title}」高度匹配（{match.rerank_confidence*100:.0f}%）！{match.rerank_reason}",
                    notification_type='auto'
                )
                # 通知招领帖发布者
                self._create_notification(
                    user=match.found_post.user,
                    match=match,
                    title=f"🔥 极有可能有人在找这件物品！",
                    content=f"您发布的招领帖「{match.found_post.title}」与寻物帖「{match.lost_post.title}」高度匹配（{match.rerank_confidence*100:.0f}%）！{match.rerank_reason}",
                    notification_type='auto'
                )

    def _create_notification(self, user, match: CandidateMatch, 
                            title: str, content: str, notification_type: str = 'auto'):
        """创建通知
        
        Args:
            notification_type: 'auto' 自动通知, 'confirmed' 人工确认通知
        """
        # 避免重复通知（同类型）
        existing = Notification.objects.filter(
            user=user,
            match=match,
            title__startswith=title[:5]  # 简单判断同类型通知
        ).exists()

        if not existing:
            Notification.objects.create(
                user=user,
                match=match,
                title=title,
                content=content
            )

    @staticmethod
    def send_confirmed_notification(match: CandidateMatch):
        """
        发送人工确认通知（管理员审核通过后调用）
        """
        # 通知寻物帖发布者
        Notification.objects.create(
            user=match.lost_post.user,
            match=match,
            title=f"✅ 已确认找到您的物品！",
            content=f"经人工审核确认，招领帖「{match.found_post.title}」就是您丢失的「{match.lost_post.title}」！请尽快联系对方取回。"
        )
        # 通知招领帖发布者
        Notification.objects.create(
            user=match.found_post.user,
            match=match,
            title=f"✅ 已确认物品找到失主！",
            content=f"经人工审核确认，您捡到的「{match.found_post.title}」的失主已找到！对方正在寻找「{match.lost_post.title}」，请等待联系。"
        )

    def get_matches_for_post(self, post: Post) -> list:
        """
        获取帖子的所有匹配
        
        Args:
            post: 帖子实例
            
        Returns:
            CandidateMatch 列表
        """
        if post.LostOrFound == '寻物启事':
            matches = CandidateMatch.objects.filter(lost_post=post)
        else:
            matches = CandidateMatch.objects.filter(found_post=post)
        
        return list(matches.order_by('-rerank_confidence', '-score'))

    def trigger_matching(self, post: Post) -> list:
        """
        手动触发匹配（用于已有帖子）
        """
        return self.process_new_post(post)
