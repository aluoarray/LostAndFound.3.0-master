from django.shortcuts import render, redirect, get_object_or_404
from .models import Post, Comment, User, CandidateMatch, Notification
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date


def landing(request):
    """炫酷欢迎页"""
    return render(request, 'MyApp/landing.html')


def index(request):
    posts = Post.objects.all().order_by('-PostTime')
    category = request.GET.get('category')
    date = request.GET.get('date')
    zone = request.GET.get('zone')
    location = request.GET.get('location')
    owner = request.GET.get('owner')

    if category:
        posts = posts.filter(ItemType=category)
    if date:
        posts = posts.filter(PostTime__date__gte=parse_date(date))
    if zone:
        posts = posts.filter(Location__startswith=zone)
    if location:
        posts = posts.filter(Location__icontains=location)
    if owner == 'mine' and request.session.get('user_id'):
        posts = posts.filter(user_id=request.session['user_id'])

    user_avatar = None
    if request.session.get('user_id'):
        user = User.objects.filter(id=request.session['user_id']).first()
        if user and user.avatar:
            user_avatar = user.avatar.url
    return render(request, 'MyApp/home.html', {'posts': posts, 'user_avatar': user_avatar})

def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comments = Comment.objects.filter(post=post).order_by('created_at')
    
    # 获取候选匹配
    if post.LostOrFound == '寻物启事':
        candidate_matches = CandidateMatch.objects.filter(lost_post=post).order_by('-rerank_confidence', '-score')[:5]
    else:
        candidate_matches = CandidateMatch.objects.filter(found_post=post).order_by('-rerank_confidence', '-score')[:5]
    
    # 处理置信度显示（转换为百分比）
    for match in candidate_matches:
        if match.rerank_confidence:
            match.rerank_confidence = match.rerank_confidence * 100
    
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        content = request.POST.get('content')
        if user_id and content:
            user = User.objects.get(id=user_id)
            Comment.objects.create(post=post, user=user, content=content)
            return redirect('MyApp:detail', post_id=post_id)
    return render(request, 'MyApp/detail.html', {
        'post': post, 
        'comments': comments,
        'candidate_matches': candidate_matches
    })

def post_create(request):
    if request.method == 'POST':
        user_id = request.session.get('user_id')
        if not user_id:
            return redirect('MyApp:login')
        user = User.objects.get(id=user_id)
        post = Post.objects.create(
            user=user,
            LostOrFound=request.POST.get('lost_or_found', '丢失'),
            title=request.POST['title'],
            description=request.POST['description'],
            ItemType=request.POST['category'],
            Location=request.POST['zone'],  # 只保存大区
            Img=request.FILES.get('image'),
        )
        # 触发匹配
        try:
            from .services import MatchingService
            service = MatchingService()
            service.process_new_post(post)
        except Exception as e:
            print(f"匹配服务异常: {e}")
        return redirect('MyApp:index')
    return render(request, 'MyApp/post.html')

def login_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        password = request.POST.get('password')
        try:
            user = User.objects.get(id=user_id)
            if user.password == password:
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                return redirect('MyApp:index')
            else:
                return render(request, 'MyApp/login.html', {'login_error': '密码错误'})
        except User.DoesNotExist:
            return render(request, 'MyApp/login.html', {'login_error': '用户ID不存在'})
    return render(request, 'MyApp/login.html')

def register_view(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        if password != password2:
            return render(request, 'MyApp/login.html', {'register': True, 'register_error': '两次密码不一致'})
        if User.objects.filter(id=user_id).exists():
            return render(request, 'MyApp/login.html', {'register': True, 'register_error': '用户ID已存在'})
        if User.objects.filter(name=name).exists():
            return render(request, 'MyApp/login.html', {'register': True, 'register_error': '用户名已存在'})
        if User.objects.filter(email=email).exists():
            return render(request, 'MyApp/login.html', {'register': True, 'register_error': '邮箱已被注册'})
        User.objects.create(id=user_id, name=name, email=email, password=password)
        return render(request, 'MyApp/login.html', {'login_error': '注册成功，请登录'})
    return render(request, 'MyApp/login.html', {'register': True})

def logout_view(request):
    request.session.flush()
    return redirect('MyApp:login')

def change_avatar(request):
    if request.method == 'POST' and request.session.get('user_id'):
        user = User.objects.get(id=request.session['user_id'])
        avatar = request.FILES.get('avatar')
        if avatar:
            user.avatar = avatar
            user.save()
        return redirect('MyApp:index')
    return redirect('MyApp:login')

def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.session.get('user_id') == post.user.id:
        post.delete()
    return redirect('MyApp:index')

def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.session.get('user_id') != post.user.id:
        return redirect('MyApp:index')
    if request.method == 'POST':
        post.title = request.POST['title']
        post.ItemType = request.POST['category']
        post.Location = request.POST['zone']
        post.description = request.POST['description']
        post.LostOrFound = request.POST.get('lost_or_found', '失物招领')
        if request.FILES.get('image'):
            post.Img = request.FILES['image']
        post.save()
        return redirect('MyApp:detail', post_id=post.id)
    return render(request, 'MyApp/post.html', {'post': post, 'edit': True})


def trigger_match(request, post_id):
    """手动触发匹配"""
    post = get_object_or_404(Post, id=post_id)
    # 只允许帖子作者触发匹配
    if request.session.get('user_id') != post.user.id:
        return redirect('MyApp:detail', post_id=post_id)
    
    try:
        from .services import MatchingService
        service = MatchingService()
        service.trigger_matching(post)
    except Exception as e:
        print(f"匹配服务异常: {e}")
    
    return redirect('MyApp:detail', post_id=post_id)


def notifications_view(request):
    """用户通知列表"""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('MyApp:login')
    
    notifications = Notification.objects.filter(user_id=user_id).order_by('-created_at')
    return render(request, 'MyApp/notifications.html', {'notifications': notifications})


def mark_notification_read(request, notification_id):
    """标记通知为已读"""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('MyApp:login')
    
    notification = get_object_or_404(Notification, id=notification_id, user_id=user_id)
    notification.is_read = True
    notification.save()
    
    # 跳转到匹配的帖子详情
    if notification.match:
        if notification.match.lost_post.user_id == user_id:
            return redirect('MyApp:detail', post_id=notification.match.found_post.id)
        else:
            return redirect('MyApp:detail', post_id=notification.match.lost_post.id)
    
    return redirect('MyApp:notifications')
