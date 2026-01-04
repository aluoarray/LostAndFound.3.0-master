# ngrok 配置和使用总结

## 📋 完整流程总结

### 第一步：下载 ngrok

1. 访问 https://ngrok.com/download
2. 下载 Windows 版本（`ngrok.exe`）
3. 将 `ngrok.exe` 放到项目根目录：`G:\Test2\LostAndFound.3.0-master\`

### 第二步：配置认证令牌

```powershell
# 进入项目目录
cd G:\Test2\LostAndFound.3.0-master

# 配置认证令牌（从 ngrok 控制台获取）
.\ngrok.exe config add-authtoken 你的认证令牌
```

**获取认证令牌的方法：**
- 登录 https://dashboard.ngrok.com/
- 进入"入门" → "您的身份验证令牌"
- 复制完整的认证令牌（长字符串，不是 `cr_` 或 `usr_` 开头的ID）

**验证配置：**
```powershell
.\ngrok.exe config check
```

### 第三步：启动 Django 服务器

在一个终端窗口中运行：

```powershell
cd G:\Test2\LostAndFound.3.0-master
python manage.py runserver
```

### 第四步：启动 ngrok 隧道

在另一个终端窗口中运行：

```powershell
cd G:\Test2\LostAndFound.3.0-master
.\ngrok.exe http 8000 --domain=kingston-vagrom-nonradically.ngrok-free.dev
```

### 第五步：配置 Django（已自动完成）

#### 1. 配置 CSRF 信任源

在 `LostAndFound/settings.py` 中添加：

```python
CSRF_TRUSTED_ORIGINS = [
    'https://kingston-vagrom-nonradically.ngrok-free.dev',
    'http://kingston-vagrom-nonradically.ngrok-free.dev',
]
```

#### 2. 配置根路径重定向

在 `LostAndFound/urls.py` 中添加：

```python
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('MyApp/', include('MyApp.urls')),
    path('', RedirectView.as_view(url='/MyApp/', permanent=False), name='home'),
]
```

## 🚀 快速启动命令（日常使用）

### 启动服务（两个终端窗口）

**终端1 - Django 服务器：**
```powershell
cd G:\Test2\LostAndFound.3.0-master
python manage.py runserver
```

**终端2 - ngrok 隧道：**
```powershell
cd G:\Test2\LostAndFound.3.0-master
.\ngrok.exe http 8000 --domain=kingston-vagrom-nonradically.ngrok-free.dev
```

## 📝 关键命令速查

| 操作 | 命令 |
|------|------|
| 配置认证令牌 | `.\ngrok.exe config add-authtoken <你的令牌>` |
| 验证配置 | `.\ngrok.exe config check` |
| 启动隧道 | `.\ngrok.exe http 8000 --domain=kingston-vagrom-nonradically.ngrok-free.dev` |
| 查看版本 | `.\ngrok.exe version` |
| 查看帮助 | `.\ngrok.exe --help` |

## 🌐 访问地址

- **应用地址：** https://kingston-vagrom-nonradically.ngrok-free.dev/
- **管理后台：** https://kingston-vagrom-nonradically.ngrok-free.dev/admin/
- **ngrok 监控界面：** http://127.0.0.1:4040

## ⚠️ 注意事项

1. **使用 `.\ngrok.exe` 而不是 `ngrok`**
   - 因为 ngrok.exe 在项目目录中，需要使用相对路径

2. **每次使用都需要两个终端**
   - 一个运行 Django 服务器
   - 一个运行 ngrok 隧道

3. **修改配置后需要重启**
   - 修改 `settings.py` 后需要重启 Django 服务器
   - ngrok 配置修改后需要重新运行 ngrok 命令

4. **永久安装（可选）**
   - 如果想直接使用 `ngrok` 命令，可以将 `ngrok.exe` 添加到系统 PATH
   - 或者将 `ngrok.exe` 放到系统目录（如 `C:\Program Files\ngrok\`）

## 🔧 故障排查

### 问题：无法识别 ngrok 命令
**解决：** 使用 `.\ngrok.exe` 而不是 `ngrok`

### 问题：认证令牌错误
**解决：** 确保从 ngrok 控制台获取的是完整的认证令牌，不是用户ID或凭证ID

### 问题：CSRF 验证失败
**解决：** 确保在 `settings.py` 中配置了 `CSRF_TRUSTED_ORIGINS`

### 问题：404 错误
**解决：** 确保 Django 服务器正在运行，并且 URL 配置正确

## 📚 相关文件

- `ngrok.exe` - ngrok 客户端程序
- `LostAndFound/settings.py` - Django 配置文件（包含 CSRF 配置）
- `LostAndFound/urls.py` - URL 路由配置（包含根路径重定向）
- `ngrok安装配置指南.md` - 详细的安装配置指南

