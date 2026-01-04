from django.contrib import admin
from django.utils import timezone
from .models import Post, User, Comment, ExtractionCache, CandidateMatch, Notification


# 注册基础模型
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'email']
    search_fields = ['name', 'email']


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'LostOrFound', 'ItemType', 'State', 'PostTime']
    list_filter = ['LostOrFound', 'ItemType', 'State', 'PostTime']  # 将 PostTime 添加到过滤器而不是 date_hierarchy
    search_fields = ['title', 'description']
    # date_hierarchy = 'PostTime'  # 暂时禁用，避免时区问题


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'user', 'created_at']
    list_filter = ['created_at']


# ==================== 候选人匹配功能相关 ====================

@admin.register(ExtractionCache)
class ExtractionCacheAdmin(admin.ModelAdmin):
    list_display = ['id', 'post', 'item_name', 'color', 'brand', 'created_at']
    search_fields = ['item_name', 'brand', 'features']
    readonly_fields = ['raw_json', 'created_at']


@admin.register(CandidateMatch)
class CandidateMatchAdmin(admin.ModelAdmin):
    list_display = ['id', 'lost_post', 'found_post', 'score', 'rerank_confidence_display', 'status', 'method', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['lost_post__title', 'found_post__title', 'rerank_reason']
    readonly_fields = ['score', 'method', 'rerank_confidence', 'rerank_reason', 'created_at']
    actions = ['accept_matches', 'reject_matches']
    ordering = ['-rerank_confidence', '-score']  # 按置信度和分数降序排列
    
    def rerank_confidence_display(self, obj):
        if obj.rerank_confidence:
            return f"{obj.rerank_confidence * 100:.0f}%"
        return "-"
    rerank_confidence_display.short_description = 'LLM置信度'
    rerank_confidence_display.admin_order_field = 'rerank_confidence'  # 允许点击列头排序
    
    def accept_matches(self, request, queryset):
        """接受匹配 - 更新状态并发送确认通知"""
        from .services import MatchingService
        
        updated = 0
        for match in queryset:
            if match.status != 'accepted':
                match.status = 'accepted'
                match.reviewed_at = timezone.now()
                match.save()
                # 发送人工确认通知
                MatchingService.send_confirmed_notification(match)
                updated += 1
        
        self.message_user(request, f"已接受 {updated} 个匹配，并已通知双方用户")
    accept_matches.short_description = "✅ 确认匹配（通知用户）"
    
    def reject_matches(self, request, queryset):
        """拒绝匹配 - 删除匹配记录及相关通知"""
        count = queryset.count()
        # 先删除相关通知
        for match in queryset:
            Notification.objects.filter(match=match).delete()
        # 再删除匹配记录
        queryset.delete()
        self.message_user(request, f"已删除 {count} 个匹配记录及相关通知")
    reject_matches.short_description = "❌ 拒绝并删除匹配"


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['title', 'content']


# 设置后台中文
admin.site.site_header = '失物招领管理系统'
admin.site.site_title = '失物招领后台'
admin.site.index_title = '管理首页'
