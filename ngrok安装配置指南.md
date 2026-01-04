# ngrok 安装和配置指南

## 问题分析

你遇到的错误 `无法将"ngrok"项识别为 cmdlet、函数、脚本文件或可运行程序的名称` 是因为：
- ✅ 你已经有 ngrok 账户和域名（`kingston-vagrom-nonradically.ngrok-free.dev`）
- ❌ 但本地 Windows 系统还没有安装 ngrok 客户端程序

## 解决方案

### 方法1：使用 Chocolatey 安装（推荐，最简单）

如果你已经安装了 Chocolatey 包管理器：

```powershell
choco install ngrok
```

### 方法2：使用 Scoop 安装

如果你已经安装了 Scoop 包管理器：

```powershell
scoop install ngrok
```

### 方法3：手动下载安装（适用于所有情况）

#### 步骤1：下载 ngrok

1. 访问 ngrok 官网：https://ngrok.com/download
2. 选择 Windows 版本下载
3. 或者直接下载：https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip

#### 步骤2：解压并配置

**选项A：解压到项目目录（临时使用）**

1. 将下载的 `ngrok.exe` 解压到项目目录：`G:\Test2\LostAndFound.3.0-master\`
2. 在项目目录中直接运行：
   ```powershell
   .\ngrok.exe http 8000 --domain=kingston-vagrom-nonradically.ngrok-free.dev
   ```

**选项B：安装到系统（推荐，永久使用）**

1. 创建一个目录存放 ngrok，例如：`C:\Program Files\ngrok\`
2. 将 `ngrok.exe` 解压到这个目录
3. 将 ngrok 添加到系统 PATH 环境变量：
   - 右键"此电脑" → "属性" → "高级系统设置" → "环境变量"
   - 在"系统变量"中找到 `Path`，点击"编辑"
   - 点击"新建"，添加：`C:\Program Files\ngrok\`
   - 点击"确定"保存
4. **重新打开 PowerShell**（重要！环境变量更改需要重启终端）

#### 步骤3：配置认证令牌

1. 登录 ngrok 控制台：https://dashboard.ngrok.com/
2. 进入"您的身份验证令牌"（Your Auth Token）页面
3. 复制你的认证令牌
4. 在 PowerShell 中运行：
   ```powershell
   ngrok config add-authtoken 你的认证令牌
   ```

#### 步骤4：验证安装

```powershell
ngrok version
```

如果显示版本号，说明安装成功！

#### 步骤5：使用你的域名启动隧道

```powershell
ngrok http 8000 --domain=kingston-vagrom-nonradically.ngrok-free.dev
```

## 快速测试（临时方案）

如果你只是想快速测试，不想配置 PATH：

1. 下载 `ngrok.exe` 到项目目录
2. 在项目目录运行：
   ```powershell
   .\ngrok.exe http 8000 --domain=kingston-vagrom-nonradically.ngrok-free.dev
   ```

## 常见问题

### Q: 配置认证令牌后仍然无法使用域名？
A: 确保：
- 域名 `kingston-vagrom-nonradically.ngrok-free.dev` 在你的账户中已创建
- 认证令牌正确配置（运行 `ngrok config check` 检查）
- 账户类型支持使用自定义域名（免费账户通常有开发域名）

### Q: 提示 "authtoken is required"？
A: 需要先配置认证令牌：
```powershell
ngrok config add-authtoken 你的认证令牌
```

### Q: 提示 "domain not found"？
A: 检查：
- 域名拼写是否正确
- 域名是否在你的 ngrok 账户中
- 登录 https://dashboard.ngrok.com/domains 查看可用域名

## 下一步

安装配置完成后，你需要：

1. **启动 Django 服务器**（在一个终端窗口）：
   ```powershell
   python manage.py runserver
   ```

2. **启动 ngrok 隧道**（在另一个终端窗口）：
   ```powershell
   ngrok http 8000 --domain=kingston-vagrom-nonradically.ngrok-free.dev
   ```

3. **配置 Django 的 CSRF 信任源**（如果需要）：
   在 `LostAndFound/settings.py` 中添加：
   ```python
   CSRF_TRUSTED_ORIGINS = [
       'https://kingston-vagrom-nonradically.ngrok-free.dev',
   ]
   ```

