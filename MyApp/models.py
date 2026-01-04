from django.db import models
from django.utils import timezone

# Create your models here.

class User(models.Model):
    id = models.IntegerField(primary_key=True) # 用户ID
    name = models.CharField(max_length=100) # 用户名
    email = models.EmailField(max_length=100, unique=True) # 用户邮箱
    password = models.CharField(max_length=100) # 用户密码
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, default='avatars/default_avatar.jpg') # 上传的头像图片

    def __str__(self):
        return self.name

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 发布帖子的用户
    LostOrFound = models.CharField(max_length=10) # 物品是丢失还是找到
    PostTime = models.DateTimeField(default=timezone.now) # 发布的时间（使用时区感知时间）
    Img = models.ImageField(upload_to='images/', blank=True, null=True) # 上传的图片
    title = models.CharField(max_length=100) # 物品标题
    description = models.TextField() # 详细描述
    ItemType = models.CharField(max_length=50) # 物品类型
    Location = models.CharField(max_length=500) # 物品位置
    State = models.CharField(max_length=20, default='未完成') # 物品状态

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE) # 关联的帖子
    user = models.ForeignKey(User, on_delete=models.CASCADE) # 评论的用户
    content = models.TextField() # 评论内容
    created_at = models.DateTimeField(auto_now_add=True) # 评论时间

    def __str__(self):
        return f"{self.user.name} - {self.post.title}"


# ==================== 候选人匹配功能相关模型 ====================

class ExtractionCache(models.Model):
    """实体抽取缓存 - 存储从帖子中抽取的结构化信息"""
    post = models.OneToOneField(Post, on_delete=models.CASCADE, verbose_name='关联帖子')
    item_name = models.CharField(max_length=100, blank=True, verbose_name='物品名称')
    color = models.CharField(max_length=50, blank=True, verbose_name='颜色')
    brand = models.CharField(max_length=100, blank=True, verbose_name='品牌')
    features = models.TextField(blank=True, verbose_name='特征描述')
    location_detail = models.CharField(max_length=200, blank=True, verbose_name='详细位置')
    time_info = models.CharField(max_length=100, blank=True, verbose_name='时间信息')
    raw_json = models.JSONField(default=dict, verbose_name='原始JSON')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '实体抽取缓存'
        verbose_name_plural = '实体抽取缓存'

    def __str__(self):
        return f"抽取缓存 - {self.post.title}"


class CandidateMatch(models.Model):
    """候选匹配 - 存储寻物帖和招领帖的匹配关系"""
    STATUS_CHOICES = [
        ('pending', '待审核'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
    ]

    lost_post = models.ForeignKey(Post, on_delete=models.CASCADE,
                                   related_name='lost_matches', verbose_name='寻物帖')
    found_post = models.ForeignKey(Post, on_delete=models.CASCADE,
                                    related_name='found_matches', verbose_name='招领帖')
    score = models.FloatField(default=0.0, verbose_name='匹配分数')
    method = models.CharField(max_length=50, default='tfidf', verbose_name='匹配方法')
    rerank_confidence = models.FloatField(null=True, blank=True, verbose_name='LLM置信度')
    rerank_reason = models.TextField(blank=True, verbose_name='匹配理由')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                              default='pending', verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    reviewed_at = models.DateTimeField(null=True, blank=True, verbose_name='审核时间')

    class Meta:
        verbose_name = '候选匹配'
        verbose_name_plural = '候选匹配'
        unique_together = ['lost_post', 'found_post']

    def __str__(self):
        return f"{self.lost_post.title} <-> {self.found_post.title} ({self.score:.2f})"


class Notification(models.Model):
    """用户通知 - 存储匹配成功后的通知消息"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    match = models.ForeignKey(CandidateMatch, on_delete=models.CASCADE, verbose_name='关联匹配')
    title = models.CharField(max_length=200, verbose_name='通知标题')
    content = models.TextField(verbose_name='通知内容')
    is_read = models.BooleanField(default=False, verbose_name='是否已读')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = '通知'

    def __str__(self):
        return f"{self.user.name} - {self.title}"