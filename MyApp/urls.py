from django.urls import path
from . import views
from . import api

app_name = "MyApp"
urlpatterns = [
    path("", views.landing, name="landing"),  # 欢迎页
    path("home/", views.index, name="index"),  # 首页
    path("post/", views.post_create, name="post"),
    path("detail/<int:post_id>/", views.post_detail, name="detail"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("change_avatar/", views.change_avatar, name="change_avatar"),
    path("edit/<int:post_id>/", views.edit_post, name="edit_post"),
    path("delete/<int:post_id>/", views.delete_post, name="delete_post"),
    
    # 匹配功能
    path("trigger_match/<int:post_id>/", views.trigger_match, name="trigger_match"),
    path("notifications/", views.notifications_view, name="notifications"),
    path("notification/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    
    # API 接口
    path("api/posts/search", api.search_posts, name="api_search"),
    path("api/posts/create", api.create_post, name="api_create"),
    path("api/posts/<int:post_id>", api.get_post_detail, name="api_detail"),
    path("api/options", api.get_options, name="api_options"),
]