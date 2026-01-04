"""
候选检索 Agent - 基于 TF-IDF 检索候选帖子
"""
import re
import math
from collections import Counter


class CandidateSearcher:
    """候选检索器 - 使用简单的 TF-IDF 实现"""

    def __init__(self):
        self.stop_words = {'的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', 
                          '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', 
                          '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她'}

    def tokenize(self, text: str) -> list:
        """
        简单分词（按字符和常见分隔符）
        """
        # 移除标点符号，按空格和常见分隔符分割
        text = re.sub(r'[^\w\s]', ' ', text)
        # 简单按字符分割（适合中文）+ 按空格分割（适合英文）
        tokens = []
        for word in text.split():
            if len(word) <= 4:
                tokens.append(word)
            else:
                # 长词按2-gram分割
                for i in range(len(word) - 1):
                    tokens.append(word[i:i+2])
        # 过滤停用词
        return [t for t in tokens if t and t not in self.stop_words]

    def compute_tf(self, tokens: list) -> dict:
        """计算词频 TF"""
        counter = Counter(tokens)
        total = len(tokens) if tokens else 1
        return {word: count / total for word, count in counter.items()}

    def compute_idf(self, documents: list) -> dict:
        """计算逆文档频率 IDF"""
        n_docs = len(documents)
        if n_docs == 0:
            return {}
        
        # 统计每个词出现在多少文档中
        doc_freq = Counter()
        for doc_tokens in documents:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                doc_freq[token] += 1
        
        # 计算 IDF
        return {word: math.log(n_docs / (freq + 1)) + 1 
                for word, freq in doc_freq.items()}

    def compute_tfidf(self, tf: dict, idf: dict) -> dict:
        """计算 TF-IDF"""
        return {word: tf_val * idf.get(word, 1) 
                for word, tf_val in tf.items()}

    def cosine_similarity(self, vec1: dict, vec2: dict) -> float:
        """计算余弦相似度"""
        # 获取所有词
        all_words = set(vec1.keys()) | set(vec2.keys())
        if not all_words:
            return 0.0
        
        # 计算点积
        dot_product = sum(vec1.get(w, 0) * vec2.get(w, 0) for w in all_words)
        
        # 计算模
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values())) or 1
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values())) or 1
        
        return dot_product / (norm1 * norm2)

    def search(self, target_post, candidate_posts, top_k: int = 10) -> list:
        """
        基于 TF-IDF 检索候选帖子
        
        Args:
            target_post: 目标帖子（Post 实例）
            candidate_posts: 候选帖子列表
            top_k: 返回前 k 个结果
            
        Returns:
            [(post, score), ...] 按分数降序排列
        """
        if not candidate_posts:
            return []

        # 构建文本
        target_text = f"{target_post.title} {target_post.description} {target_post.ItemType} {target_post.Location}"
        candidate_texts = [
            f"{p.title} {p.description} {p.ItemType} {p.Location}" 
            for p in candidate_posts
        ]

        # 分词
        target_tokens = self.tokenize(target_text)
        candidate_tokens_list = [self.tokenize(text) for text in candidate_texts]

        # 计算 IDF（基于所有文档）
        all_docs = [target_tokens] + candidate_tokens_list
        idf = self.compute_idf(all_docs)

        # 计算目标帖子的 TF-IDF
        target_tf = self.compute_tf(target_tokens)
        target_tfidf = self.compute_tfidf(target_tf, idf)

        # 计算每个候选的相似度
        results = []
        for i, (post, tokens) in enumerate(zip(candidate_posts, candidate_tokens_list)):
            tf = self.compute_tf(tokens)
            tfidf = self.compute_tfidf(tf, idf)
            similarity = self.cosine_similarity(target_tfidf, tfidf)
            results.append((post, similarity))

        # 按相似度降序排序
        results.sort(key=lambda x: x[1], reverse=True)

        return results[:top_k]

    def rule_based_filter(self, target_post, candidate_posts) -> list:
        """
        基于规则的预过滤
        
        Args:
            target_post: 目标帖子
            candidate_posts: 候选帖子列表
            
        Returns:
            过滤后的候选帖子列表
        """
        filtered = []
        target_type = target_post.ItemType.lower() if target_post.ItemType else ""
        target_location = target_post.Location.lower() if target_post.Location else ""

        for post in candidate_posts:
            # 类型匹配
            post_type = post.ItemType.lower() if post.ItemType else ""
            if target_type and post_type and target_type != post_type:
                # 类型不同，降低优先级但不完全排除
                pass
            
            filtered.append(post)

        return filtered
