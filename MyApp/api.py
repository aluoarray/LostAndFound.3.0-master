"""
失物招领 API 接口
供 Coze 智能体调用，实现数据查询和写入
"""
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import Post, User


@csrf_exempt
@require_http_methods(["GET"])
def search_posts(request):
    """
    查询帖子 API
    
    GET /api/posts/search
    
    参数（全部可选，支持组合查询）：
    - keyword: 关键词，搜索标题和描述
    - type: 类型，"失物招领" 或 "寻物启事"
    - item_type: 物品类型（手机/数码产品/鞋服包饰/钱包/书籍/证件/钥匙/快递/其他）
    - location: 丢失区域（支持模糊匹配）
    - date_from: 起始日期（格式：YYYY-MM-DD）
    - date_to: 结束日期（格式：YYYY-MM-DD）
    - state: 状态（未完成/已完成）
    - limit: 返回数量限制，默认20
    
    返回示例：
    {
        "success": true,
        "count": 2,
        "posts": [
            {
                "id": 1,
                "title": "丢失iPhone 15",
                "description": "在A区食堂丢失...",
                "type": "寻物启事",
                "item_type": "手机",
                "location": "A区 食堂",
                "post_time": "2026-01-03 10:30:00",
                "state": "未完成",
                "user_name": "张三",
                "image_url": "/media/images/xxx.jpg"
            }
        ]
    }
    """
    try:
        # 获取查询参数
        keyword = request.GET.get('keyword', '').strip()
        post_type = request.GET.get('type', '').strip()
        item_type = request.GET.get('item_type', '').strip()
        location = request.GET.get('location', '').strip()
        date_from = request.GET.get('date_from', '').strip()
        date_to = request.GET.get('date_to', '').strip()
        state = request.GET.get('state', '').strip()
        owner = request.GET.get('owner', '').strip()
        limit = int(request.GET.get('limit', 20))
        
        # 构建查询
        posts = Post.objects.all().order_by('-PostTime')
        
        # 用户筛选（我的帖子）
        if owner == 'mine' and request.session.get('user_id'):
            posts = posts.filter(user_id=request.session['user_id'])
        
        # 关键词搜索（标题、描述、物品类型、地点）
        if keyword:
            posts = posts.filter(
                Q(title__icontains=keyword) | 
                Q(description__icontains=keyword) |
                Q(ItemType__icontains=keyword) |
                Q(Location__icontains=keyword)
            )
        
        # 类型筛选（失物招领/寻物启事）
        if post_type:
            posts = posts.filter(LostOrFound=post_type)
        
        # 物品类型筛选
        if item_type:
            posts = posts.filter(ItemType=item_type)
        
        # 地点筛选（模糊匹配）
        if location:
            posts = posts.filter(Location__icontains=location)
        
        # 日期范围筛选
        if date_from:
            posts = posts.filter(PostTime__date__gte=date_from)
        if date_to:
            posts = posts.filter(PostTime__date__lte=date_to)
        
        # 状态筛选
        if state:
            posts = posts.filter(State=state)
        
        # 限制返回数量
        posts = posts[:limit]
        
        # 构建返回数据
        result = []
        for post in posts:
            result.append({
                'id': post.id,
                'title': post.title,
                'description': post.description,
                'type': post.LostOrFound,
                'item_type': post.ItemType,
                'location': post.Location,
                'post_time': post.PostTime.strftime('%Y-%m-%d %H:%M:%S'),
                'state': post.State,
                'user_name': post.user.name if post.user else '匿名',
                'image_url': post.Img.url if post.Img else None
            })
        
        return JsonResponse({
            'success': True,
            'count': len(result),
            'posts': result
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_post(request):
    """
    创建帖子 API
    
    POST /api/posts/create
    Content-Type: application/json
    
    请求体参数：
    - user_id: 用户ID（必填）
    - title: 标题（必填）
    - description: 详细描述（必填）
    - type: 类型，"失物招领" 或 "寻物启事"（必填）
    - item_type: 物品类型（必填）
    - location: 丢失/捡到地点（必填）
    
    请求示例：
    {
        "user_id": 202300801087,
        "title": "丢失黑色钱包",
        "description": "今天下午在图书馆三楼丢失一个黑色钱包，内有身份证和银行卡",
        "type": "寻物启事",
        "item_type": "钱包",
        "location": "C区 图书馆"
    }
    
    返回示例：
    {
        "success": true,
        "message": "帖子创建成功",
        "post_id": 123,
        "post": {
            "id": 123,
            "title": "丢失黑色钱包",
            ...
        }
    }
    """
    try:
        # 解析 JSON 请求体
        data = json.loads(request.body)
        
        # 验证必填字段
        required_fields = ['user_id', 'title', 'description', 'type', 'item_type', 'location']
        for field in required_fields:
            if field not in data or not data[field]:
                return JsonResponse({
                    'success': False,
                    'error': f'缺少必填字段: {field}'
                }, status=400)
        
        # 验证用户是否存在，不存在则使用系统中第一个用户
        try:
            user = User.objects.get(id=data['user_id'])
        except User.DoesNotExist:
            # 使用系统中第一个用户
            user = User.objects.first()
            if not user:
                return JsonResponse({
                    'success': False,
                    'error': '系统中没有用户，请先注册'
                }, status=400)
        
        # 验证类型
        valid_types = ['失物招领', '寻物启事']
        if data['type'] not in valid_types:
            return JsonResponse({
                'success': False,
                'error': f'类型必须是: {valid_types}'
            }, status=400)
        
        # 验证物品类型
        valid_item_types = ['手机', '数码产品', '鞋服包饰', '钱包', '书籍', '证件', '钥匙', '快递', '其他']
        if data['item_type'] not in valid_item_types:
            return JsonResponse({
                'success': False,
                'error': f'物品类型必须是: {valid_item_types}'
            }, status=400)
        
        # 创建帖子
        post = Post.objects.create(
            user=user,
            title=data['title'],
            description=data['description'],
            LostOrFound=data['type'],
            ItemType=data['item_type'],
            Location=data['location'],
            State='未完成'
        )
        
        return JsonResponse({
            'success': True,
            'message': '帖子创建成功',
            'post_id': post.id,
            'post': {
                'id': post.id,
                'title': post.title,
                'description': post.description,
                'type': post.LostOrFound,
                'item_type': post.ItemType,
                'location': post.Location,
                'post_time': post.PostTime.strftime('%Y-%m-%d %H:%M:%S'),
                'state': post.State,
                'user_name': user.name
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': '请求体必须是有效的 JSON 格式'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_post_detail(request, post_id):
    """
    获取帖子详情 API
    
    GET /api/posts/<post_id>
    
    返回单个帖子的详细信息
    """
    try:
        post = Post.objects.get(id=post_id)
        return JsonResponse({
            'success': True,
            'post': {
                'id': post.id,
                'title': post.title,
                'description': post.description,
                'type': post.LostOrFound,
                'item_type': post.ItemType,
                'location': post.Location,
                'post_time': post.PostTime.strftime('%Y-%m-%d %H:%M:%S'),
                'state': post.State,
                'user_name': post.user.name if post.user else '匿名',
                'user_id': post.user.id if post.user else None,
                'image_url': post.Img.url if post.Img else None
            }
        })
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'帖子ID {post_id} 不存在'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["GET"])
def get_options(request):
    """
    获取可选项 API
    
    GET /api/options
    
    返回所有可用的筛选选项，供智能体了解有哪些选项
    """
    return JsonResponse({
        'success': True,
        'options': {
            'types': ['失物招领', '寻物启事'],
            'item_types': ['手机', '数码产品', '鞋服包饰', '钱包', '书籍', '证件', '钥匙', '快递', '其他'],
            'locations': [
                'A区 食堂, 宿舍（南区）, 健康与环境工程学院',
                'B区 食堂, 创意设计学院, 外国语学院',
                'C区 湖景食堂, 大数据与互联网学院, 图书馆',
                'D区 城市交通与物流学院, 体育馆, 中德智能制造学院',
                'E区 食堂, 宿舍（北区）, 校医院',
                'F区 鑫福佳, 地铁站',
                '校外 竹韵食堂, 临时运动场, 社康中心'
            ],
            'states': ['未完成', '已完成']
        }
    })
