#!/usr/bin/env python
"""
创建Django管理员账户的辅助脚本
使用方法: python create_admin.py
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LostAndFound.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_admin():
    """创建管理员账户"""
    username = input("请输入管理员用户名: ")
    email = input("请输入管理员邮箱（可选，直接回车跳过）: ").strip()
    password = input("请输入密码: ")
    password_confirm = input("请再次输入密码确认: ")
    
    if password != password_confirm:
        print("❌ 两次输入的密码不一致！")
        return
    
    if not username:
        print("❌ 用户名不能为空！")
        return
    
    # 检查用户名是否已存在
    if User.objects.filter(username=username).exists():
        print(f"❌ 用户名 '{username}' 已存在！")
        return
    
    # 创建超级用户
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email if email else '',
            password=password
        )
        print(f"✅ 管理员账户 '{username}' 创建成功！")
        print(f"   现在可以使用该账户登录管理后台: http://127.0.0.1:8000/admin/")
    except Exception as e:
        print(f"❌ 创建失败: {e}")

if __name__ == '__main__':
    create_admin()

